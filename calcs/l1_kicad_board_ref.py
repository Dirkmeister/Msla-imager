# L1: L1.2 reference for the board-identity check. Reads the KiCad boards in GitHub Dirkmeister/UV-Backlight-Prototype (read only) at the production commit and at HEAD, and prints what a physical board can be checked against: outline, silkscreen text, LED grid, connectors with pin nets, mounting holes, parts and values. Run: python3 calcs/l1_kicad_board_ref.py <path to a clone of UV-Backlight-Prototype with history> > calcs/l1_kicad_board_ref_out.md
import math
import subprocess
import sys

MM_PER_IN = 25.4

# Board files by commit. 8208f05 "Sent to production" (2022-12-17) is the only commit with production files;
# its production/gerber.zip was generated 2022-12-07 23:08 (KiCad 6.0.6). 528a10d "IC Change" (2023-01-31) is HEAD.
REVS = [
    ("LED board, production (8208f05, 2022-12-17)", "8208f05", "UV-Backlight-Prototype.kicad_pcb"),
    ("LED board, HEAD (528a10d, 2023-01-31)", "528a10d", "UV-PCB/UV-Backlight-Prototype.kicad_pcb"),
    ("UV-PS board, HEAD (528a10d, 2023-01-31)", "528a10d", "UV-PS/UV-PS/UV-PS.kicad_pcb"),
]
SCH_REVS = [
    ("UV-PS schematic, 8f49e4d (2023-01-14, before 'IC Change')", "8f49e4d", "UV-PS/UV-PS/UV-PS.kicad_sch"),
    ("UV-PS schematic, HEAD (528a10d)", "528a10d", "UV-PS/UV-PS/UV-PS.kicad_sch"),
]


def git_show(repo, rev, path):
    return subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], check=True,
                          capture_output=True, text=True).stdout


def git_bytes(repo, rev, path):
    return subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], check=True,
                          capture_output=True).stdout


def parse_sexp(text):
    """Minimal KiCad s-expression parser: lists, quoted strings, atoms."""
    stack, cur, i, n = [], [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "(":
            stack.append(cur)
            cur = []
            i += 1
        elif c == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    buf.append("\n" if text[j + 1] == "n" else text[j + 1])
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            cur.append(("str", "".join(buf)))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "()":
                j += 1
            cur.append(text[i:j])
            i = j
    return cur[0]


def val(x):
    return x[1] if isinstance(x, tuple) else x


def kids(node, name):
    return [k for k in node if isinstance(k, list) and k and k[0] == name]


def kid(node, name):
    k = kids(node, name)
    return k[0] if k else None


def nums(node):
    return [float(v) for v in node[1:] if not isinstance(v, (list, tuple))]


def board(text):
    root = parse_sexp(text)
    out = {"edges": [], "texts": [], "fps": []}
    for g in root:
        if not isinstance(g, list) or not g:
            continue
        if g[0] in ("gr_line", "gr_arc", "gr_rect", "gr_circle", "gr_poly"):
            if val(kid(g, "layer")[1]) == "Edge.Cuts":
                pts = []
                for key in ("start", "mid", "end", "center"):
                    k = kid(g, key)
                    if k:
                        pts.append(tuple(nums(k)[:2]))
                out["edges"].append((g[0], pts))
        elif g[0] == "gr_text":
            at = nums(kid(g, "at"))
            out["texts"].append((val(g[1]).replace("\n", " ").strip(), at[0], at[1], val(kid(g, "layer")[1])))
        elif g[0] == "footprint":
            at = nums(kid(g, "at"))
            fp = {"lib": val(g[1]), "x": at[0], "y": at[1], "rot": at[2] if len(at) > 2 else 0.0,
                  "side": val(kid(g, "layer")[1]), "ref": "", "value": "", "ref_silk": False, "pads": []}
            for t in kids(g, "fp_text"):
                kind, txt, layer = t[1], val(t[2]), val(kid(t, "layer")[1])
                hidden = "hide" in t[3:] or any(isinstance(e, list) and e[0] == "effects" and "hide" in e for e in t)
                if kind == "reference":
                    fp["ref"] = txt
                    fp["ref_silk"] = layer.endswith("SilkS") and not hidden and txt not in ("", "REF**")
                elif kind == "value":
                    fp["value"] = txt
            for p in kids(g, "pad"):
                net = kid(p, "net")
                fp["pads"].append((val(p[1]), val(net[2]) if net else ""))
            out["fps"].append(fp)
    return out


def cluster(vals, tol=0.5):
    """Group coordinates within tol mm; return each group's most common value (the grid line)."""
    groups = []
    for v in sorted(vals):
        if groups and v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [round(max(set(g), key=g.count), 2) for g in groups]


def bbox(edges):
    xs = [p[0] for _, pts in edges for p in pts]
    ys = [p[1] for _, pts in edges for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def corner_radius(edges, x0, y0, x1, y1):
    """For a rounded rectangle: lines stop short of the bbox corners by the radius."""
    r = []
    for kind, pts in edges:
        if kind == "gr_line":
            (ax, ay), (bx, by) = pts[0], pts[-1]
            if abs(ax - bx) < 1e-6:          # vertical edge
                r.append(min(abs(min(ay, by) - y0), abs(y1 - max(ay, by))))
            elif abs(ay - by) < 1e-6:        # horizontal edge
                r.append(min(abs(min(ax, bx) - x0), abs(x1 - max(ax, bx))))
    return max(r) if r else 0.0


def f_mm_in(v):
    return f"{v:.2f} mm ({v / MM_PER_IN:.3f} in)"


def describe(label, text, emit):
    b = board(text)
    emit(f"\n## {label}\n")
    if not b["edges"]:
        emit("No Edge.Cuts outline.")
    else:
        x0, y0, x1, y1 = bbox(b["edges"])
        w, h = x1 - x0, y1 - y0
        r = corner_radius(b["edges"], x0, y0, x1, y1)
        emit(f"- Outline: {w:.2f} x {h:.2f} mm = {w / MM_PER_IN:.3f} x {h / MM_PER_IN:.3f} in "
             f"(Edge.Cuts x {x0:g} to {x1:g}, y {y0:g} to {y1:g}); corner radius {r:.2f} mm ({r / MM_PER_IN:.3f} in); "
             f"{len(b['edges'])} edge segments")
    origin = (x0, y0) if b["edges"] else (0.0, 0.0)

    def rel(fp):
        return fp["x"] - origin[0], fp["y"] - origin[1]

    emit(f"- Footprints: {len(b['fps'])}")
    emit("- Board text on silkscreen (gr_text): " +
         ("; ".join(f"\"{t}\" at {x - origin[0]:.1f}, {y - origin[1]:.1f} mm from the top-left corner ({ly})"
                    for t, x, y, ly in b["texts"]) if b["texts"] else "none"))
    silk_refs = sorted((fp["ref"] for fp in b["fps"] if fp["ref_silk"]), key=lambda s: (s.rstrip("0123456789"), int("0" + s[len(s.rstrip("0123456789")):])))
    emit(f"- Reference designators printed on silk ({len(silk_refs)}): {', '.join(silk_refs) if silk_refs else 'none'}")
    unref = [fp for fp in b["fps"] if fp["ref"] in ("", "REF**")]
    if unref:
        emit(f"- Footprints with no reference ({len(unref)}): " +
             "; ".join(f"{fp['lib'].split(':')[-1]} at {rel(fp)[0]:.1f}, {rel(fp)[1]:.1f} mm, {len(fp['pads'])} pads" for fp in unref))

    leds = [fp for fp in b["fps"] if fp["ref"].startswith("D") and "LED" in fp["lib"]]
    if leds:
        xs = cluster([rel(fp)[0] for fp in leds])
        ys = cluster([rel(fp)[1] for fp in leds])
        odd = [f"{fp['ref']} at {rel(fp)[0]:.2f}, {rel(fp)[1]:.2f}" for fp in leds
               if min(abs(rel(fp)[0] - v) for v in xs) > 0.05 or min(abs(rel(fp)[1] - v) for v in ys) > 0.05]
        px = [round(b2 - a2, 2) for a2, b2 in zip(xs, xs[1:])]
        py = [round(b2 - a2, 2) for a2, b2 in zip(ys, ys[1:])]
        emit(f"- LEDs: {len(leds)} x {leds[0]['lib'].split(':')[-1]}, value \"{leds[0]['value']}\"; "
             f"columns at x = {', '.join(f'{v:g}' for v in xs)} mm; rows at y = {', '.join(f'{v:g}' for v in ys)} mm (from the top-left corner)")
        if xs and ys:
            sx, sy = xs[-1] - xs[0], ys[-1] - ys[0]
            if odd:
                emit(f"  - Off-grid by more than 0.05 mm (placement slip): {'; '.join(odd)} mm")
            emit(f"  - Pitch x {px} mm, y {py} mm. First to last LED centre: {xs[-1]:g} - {xs[0]:g} = {f_mm_in(sx)} across, "
                 f"{ys[-1]:g} - {ys[0]:g} = {f_mm_in(sy)} down")
            if b["edges"]:
                cx, cy = (xs[0] + xs[-1]) / 2, (ys[0] + ys[-1]) / 2
                emit(f"  - LED block centre {cx:.1f}, {cy:.1f} mm vs board centre {w / 2:.1f}, {h / 2:.1f} mm: "
                     f"offset {cx - w / 2:+.1f} mm across, {cy - h / 2:+.1f} mm down")
    holes = [fp for fp in b["fps"] if fp["lib"].startswith("MountingHole")]
    if holes:
        emit(f"- Mounting holes ({holes[0]['lib'].split(':')[-1]}): " +
             "; ".join(f"{fp['ref']} at {rel(fp)[0]:.2f}, {rel(fp)[1]:.2f} mm" for fp in sorted(holes, key=lambda f: f["ref"])))
        hx = sorted({round(rel(fp)[0], 2) for fp in holes})
        hy = sorted({round(rel(fp)[1], 2) for fp in holes})
        if len(hx) == 2 and len(hy) == 2:
            emit(f"  - Hole centres {hx[1] - hx[0]:.2f} x {hy[1] - hy[0]:.2f} mm apart = "
                 f"{(hx[1] - hx[0]) / MM_PER_IN:.3f} x {(hy[1] - hy[0]) / MM_PER_IN:.3f} in")
    for fp in sorted(b["fps"], key=lambda f: f["ref"]):
        if fp["ref"].startswith("J"):
            pins = "; ".join(f"{p} {n or 'no net'}" for p, n in sorted(fp["pads"], key=lambda t: int(t[0]) if t[0].isdigit() else 999) if p)
            emit(f"- {fp['ref']}: {fp['lib'].split(':')[-1]} at {rel(fp)[0]:.2f}, {rel(fp)[1]:.2f} mm, rot {fp['rot']:g}. Pins: {pins}")
    others = [fp for fp in b["fps"] if fp["ref"] and fp["ref"] != "REF**" and not fp["ref"].startswith(("D", "J", "H", "TP"))]
    if others:
        emit("- Other parts: " + "; ".join(f"{fp['ref']} {fp['value']} ({fp['lib'].split(':')[-1]})"
                                         for fp in sorted(others, key=lambda f: f["ref"])))
    tps = [fp for fp in b["fps"] if fp["ref"].startswith("TP")]
    if tps:
        emit(f"- Test points ({len(tps)}): " + "; ".join(f"{fp['ref']} {fp['value']}" for fp in sorted(tps, key=lambda f: int(f['ref'][2:]))))
    return b


def sch_parts(text):
    root = parse_sexp(text)
    parts = []
    for s in kids(root, "symbol"):
        props = {val(p[1]): val(p[2]) for p in kids(s, "property")}
        ref = props.get("Reference", "")
        if ref.startswith("#"):
            continue
        parts.append((ref, props.get("Value", ""), val(kid(s, "lib_id")[1])))
    return sorted(parts)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 calcs/l1_kicad_board_ref.py <UV-Backlight-Prototype clone with history>")
    repo = sys.argv[1]
    lines = []
    emit = lines.append
    emit("# L1: L1.2 board-identity reference, GitHub Dirkmeister/UV-Backlight-Prototype (read only)")
    emit("\nGenerated by calcs/l1_kicad_board_ref.py. Coordinates are from each board's top-left Edge.Cuts corner, x right, y down.")
    emit("p.89 sketch for comparison: 5 x 2.75 in board, 3 rows of 7 at 5/8 x 7/8 in pitch, so first to last LED centre "
         f"6 x 5/8 = 3.750 in ({6 * 0.625 * MM_PER_IN:.2f} mm) across and 2 x 7/8 = 1.750 in ({2 * 0.875 * MM_PER_IN:.2f} mm) down.")
    boards = {}
    for label, rev, path in REVS:
        boards[label] = describe(label, git_show(repo, rev, path), emit)

    # Production gerbers: what was actually sent
    import io
    import zipfile
    z = zipfile.ZipFile(io.BytesIO(git_bytes(repo, "8208f05", "production/gerber.zip")))
    emit("\n## production/gerber.zip at 8208f05 (what was sent)\n")
    emit("- Files: " + ", ".join(f"{i.filename} ({i.date_time[0]}-{i.date_time[1]:02d}-{i.date_time[2]:02d} {i.date_time[3]:02d}:{i.date_time[4]:02d})" for i in z.infolist()))
    edge = z.read("UV-Backlight-Prototype-Edge_Cuts.gbr").decode()
    import re
    pts = [(int(a) / 1e6, int(b) / 1e6) for a, b in re.findall(r"^X(-?\d+)Y(-?\d+)", edge, re.M)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    emit(f"- Edge_Cuts extents: x {min(xs):g} to {max(xs):g}, y {min(ys):g} to {max(ys):g} mm = "
         f"{max(xs) - min(xs):.2f} x {max(ys) - min(ys):.2f} mm")
    bom = z.read("bom.csv").decode().splitlines()
    emit("- bom.csv rows: " + " | ".join(r for r in bom[1:]
                                        if not r.startswith("TP")))
    gen = re.search(r"Created by KiCad \(PCBNEW \(([^)]*)\)\) date ([0-9-]+ [0-9:]+)", edge)
    if gen:
        emit(f"- Generated by KiCad {gen.group(1)} on {gen.group(2)}")
    prod = boards["LED board, production (8208f05, 2022-12-17)"]
    prod_refs = {fp["ref"] for fp in prod["fps"] if fp["ref"] not in ("", "REF**")}
    bom_refs = set()
    for r in bom[1:]:
        if r.startswith('"'):
            bom_refs |= {s.strip() for s in r.split('"')[1].split(",")}
        elif r and not r.startswith(","):
            bom_refs.add(r.split(",")[0])
    emit(f"- Designators in the 8208f05 .kicad_pcb but not in bom.csv: {sorted(prod_refs - bom_refs) or 'none'}; "
         f"in bom.csv but not in the .kicad_pcb: {sorted(bom_refs - prod_refs) or 'none'}")

    for label, rev, path in SCH_REVS:
        emit(f"\n## {label}\n")
        emit("- " + "; ".join(f"{r} {v} ({lib})" for r, v, lib in sch_parts(git_show(repo, rev, path))))

    print("\n".join(lines))


if __name__ == "__main__":
    main()
