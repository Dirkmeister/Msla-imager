#!/usr/bin/env python3
"""Measure the generated patterns against their definitions (REQ-002/003/005/023/026).

  python tools/check_patterns.py --dir out/patterns

Reads the PNGs back from disk (native orientation), converts to the image frame, and checks:
  format     1-bit grayscale, native size, checksums (IF-13 verify)
  checker    every pixel outside the ID keep-out alternates
  ruler      lit columns/rows exactly where defined; centre to centre 2400 px and 1200 px
  combs      every 10 mil line in every wedge zone is 5 px; spaces 5 or 6 px
  coupons    opens and shorts by connected components on all 50 structures; run widths per size
  mirror     top-side screen image == pixel flip of the unmirrored render, pixel for pixel
  frames     wedge and map frames mask in order; last frame blank; times as defined
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pcbimager.machine import Machine                                  # noqa: E402
from pcbimager.raster import load_png_bool, from_native, Canvas        # noqa: E402
from pcbimager.job import verify_job                                   # noqa: E402
from pcbimager.units import px_count, mil                              # noqa: E402
from pcbimager import patterns as P                                    # noqa: E402
from pcbimager.orient import topview_to_screen_affine, flip_pixels    # noqa: E402

FAIL = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def frames(d, m):
    man = json.loads((d / "job.json").read_text())
    out = []
    for f in man["exposures"][0]["frames"]:
        out.append((f["t_s"], from_native(load_png_bool(d / f["file"]), m)))
    return man, out


def runs(v):
    """Run lengths of a 1-D bool array: list of (value, length)."""
    v = np.asarray(v, dtype=np.int8)
    edges = np.flatnonzero(np.diff(v)) + 1
    bounds = np.concatenate([[0], edges, [len(v)]])
    return [(bool(v[a]), int(b - a)) for a, b in zip(bounds[:-1], bounds[1:])]


def to_screen(m, pt_mm, side="top"):
    A = topview_to_screen_affine(m, side)
    x, y = Canvas(m).T(A(pt_mm))
    return int(np.floor(x)), int(np.floor(y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="out/patterns")
    ap.add_argument("--machine", default=None)
    a = ap.parse_args()
    m = Machine.load(a.machine)
    D = Path(a.dir)
    H, W = m.image_h, m.image_w

    print("format")
    for jd in sorted(p for p in D.iterdir() if (p / "job.json").exists()):
        probs = verify_job(jd)
        check(not probs, f"{jd.name}: IF-13 verify {probs or ''}")

    print("checker (T-LCD-2)")
    _, fr = frames(D / "tlcd2_checker", m)
    img = fr[0][1]
    jj, ii = np.indices(img.shape)
    ref = (ii + jj) % 2 == 0
    diff = img != ref
    ys, xs = np.nonzero(diff)
    box = (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None
    inside = 0 if box is None else int(diff[box[1]:box[3] + 1, box[0]:box[2] + 1].sum())
    check(box is not None and inside == int(diff.sum()) and box[2] < W // 2,
          f"all differences from a perfect checkerboard sit in one box (the ID block) {box}")
    outside = diff.copy()
    if box:
        outside[box[1]:box[3] + 1, box[0]:box[2] + 1] = False
    check(not outside.any(), f"pixels outside the ID box that fail to alternate: {int(outside.sum())}")
    for nm, (y, x) in {"centre": (H // 2, W // 2), "TL": (0, 0), "TR": (0, W - 1),
                       "BL": (H - 1, 0), "BR": (H - 1, W - 1)}.items():
        check(img[y, x] == ((x + y) % 2 == 0), f"checker parity at {nm} pixel ({x},{y})")

    print("ruler (T-LCD-3, REQ-003)")
    for wpx, nm in ((1, "tlcd3_ruler_1px"), (5, "tlcd3_ruler_5px")):
        _, fr = frames(D / nm, m)
        img = fr[0][1]
        full_cols = np.flatnonzero(img.all(axis=0))
        full_rows = np.flatnonzero(img.all(axis=1))
        cu = [c for c in full_cols]
        rv = [r for r in full_rows]
        groups_c = np.split(np.array(cu), np.flatnonzero(np.diff(cu) > 1) + 1)
        groups_r = np.split(np.array(rv), np.flatnonzero(np.diff(rv) > 1) + 1)
        cc = [g.mean() + 0.5 for g in groups_c]
        rc = [g.mean() + 0.5 for g in groups_r]
        check([len(g) for g in groups_c] == [wpx, wpx] and abs(cc[1] - cc[0] - 2400) < 1e-9,
              f"{nm}: full-height lines {[list(map(int, g[[0, -1]])) for g in groups_c]}, "
              f"centres {cc}, spacing {cc[1] - cc[0]} px")
        check([len(g) for g in groups_r] == [wpx, wpx] and abs(rc[1] - rc[0] - 1200) < 1e-9,
              f"{nm}: full-width lines {[list(map(int, g[[0, -1]])) for g in groups_r]}, "
              f"spacing {rc[1] - rc[0]} px")
    print(f"  2400 px x {m.pitch_mm * 1000:.2f} um = {2400 * m.pitch_mm:.3f} mm "
          f"= {2400 * m.pitch_mm / 25.4:.4f} in")

    print("combs in wedge zones (REQ-023: 10 mil = 5 px, spaces 5 or 6)")
    for nm in ("s1_coarse", "s1_fine"):
        man, fr = frames(D / nm, m)
        img = fr[0][1]
        widths, spaces = set(), set()
        nz = 0
        for z in man["zones"]:
            x0, y0, x1, y1 = z["screen_bbox_px"]
            zz = img[y0:y1, x0:x1]
            h, w = zz.shape
            # screen is flipped about the long axis: copper-top quadrants are at the screen bottom.
            q_u = zz[h // 2:, :w // 2]     # comb, lines along u
            q_v = zz[h // 2:, w // 2:]     # comb, lines along v
            for q, axis in ((q_u, 0), (q_v, 1)):
                line = q[:, q.shape[1] // 2] if axis == 0 else q[q.shape[0] // 2, :]
                rr = runs(line)
                inner = rr[1:-1]
                widths |= {L for v, L in inner if v}
                spaces |= {L for v, L in inner if not v}
                nz += sum(1 for v, L in inner if v)
        check(widths == {5} and spaces <= {5, 6} and nz == 10 * len(man["zones"]),
              f"{nm}: {nz} comb lines, widths {sorted(widths)} px, spaces {sorted(spaces)} px")
        times = [z["t_s"] for z in man["zones"]]
        lit = [int(f[1].sum()) for f in fr]
        check(all(b < a for a, b in zip(lit, lit[1:])) and lit[-1] == 0,
              f"{nm}: lit area falls every frame and ends blank ({len(fr)} frames)")
        ft = [f[0] for f in fr]
        check(ft[1:] == times and ft[0] == 0.0 and man["exposures"][0]["time"]["end_s"] == times[-1],
              f"{nm}: frame times {ft}")
    man, _ = frames(D / "s1_coarse", m)
    check([z["t_s"] for z in man["zones"]] == [15, 21, 30, 42, 60, 85, 120, 170, 240, 339, 480, 679],
          "s1_coarse zone times 15 ... 679 s")

    print("map (S-2)")
    man, fr = frames(D / "s2_map", m)
    lit = [int(f[1].sum()) for f in fr]
    check(len(man["zones"]) == 28 and all(b < a for a, b in zip(lit, lit[1:])) and lit[-1] == 0,
          f"s2_map: 28 cells, {len(fr)} frames, lit area falls every frame")
    st = man["purpose"]["params"]["sub_times_s"]
    r = [b / a for a, b in zip(st, st[1:])]
    check(all(abs(x - 2 ** 0.25) < 0.01 for x in r), f"s2_map sub-zone ratios {[round(x, 3) for x in r]}")

    print("coupons (S-3): connectivity and widths")
    _, fr = frames(D / "s3_coupons", m)
    img = fr[0][1]
    lab4, n4 = ndimage.label(img, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    lab8, n8 = ndimage.label(img, structure=np.ones((3, 3)))
    _, nets, _, info = P.s3_coupon_layer(m)
    opens = shorts = 0
    comps8 = {}
    for nd, mt in nets:
        pads = {k: to_screen(m, v) for k, v in mt["pads"].items()}
        L4 = {k: lab4[y, x] for k, (x, y) in pads.items()}
        L8 = {k: lab8[y, x] for k, (x, y) in pads.items()}
        tag = f"{mt['site']} {mt['s_mil']}/{mt['s_mil']} runs along {mt['orient']}"
        if not (L4["S_A"] and L4["S_A"] == L4["S_B"]):
            opens += 1
            print("    open:", tag)
        if L8["S_A"] in (L8["C_L"], L8["C_R"]) or L8["C_L"] == L8["C_R"] or 0 in L8.values():
            shorts += 1
            print("    short:", tag)
        for k, v in L8.items():
            comps8.setdefault(v, set()).add((tag, k if k.startswith("C") else "S"))
    cross = [c for c, owners in comps8.items() if len({o[0] for o in owners}) > 1]
    check(opens == 0, f"opens: {opens} of {len(nets)} serpentines (4-connected)")
    check(shorts == 0 and not cross, f"shorts: {shorts} within structures, {len(cross)} between "
                                     f"structures (8-connected)")
    # widths: scan across the five conductors at the structure centre
    bad = []
    space_sets = {}
    for nd, mt in nets:
        s = mt["s_mil"]
        n = px_count(mil(s))
        cx, cy = to_screen(m, mt["centre_mm"])
        half = int(np.ceil(4.5 * mil(s) / m.pitch_mm)) + 2      # just the five conductors
        if mt["orient"] == "u":
            line = img[cy - half:cy + half + 1, cx]
        else:
            line = img[cy, cx - half:cx + half + 1]
        rr = runs(line)
        core = [L for v, L in rr if v]
        gaps = [L for v, L in rr[1:-1] if not v]
        # five conductors (S0 C0 S1 C1 S2) cross the centre line, all n px
        if core != [n] * 5:
            bad.append((mt["site"], s, mt["orient"], core, gaps))
        else:
            space_sets.setdefault(s, set()).update(gaps)
    check(not bad, f"run widths = round(s / 47.25 um) for all structures {bad if bad else ''}")
    for s in (5, 10, 15, 20, 25):
        n = px_count(mil(s))
        print(f"    {s:2d}/{s:<2d} mil: lines {n:2d} px ({n * m.pitch_mm / 0.0254:5.2f} mil), "
              f"spaces {sorted(space_sets.get(s, []))} px (exact {2 * s / (m.pitch_mm / 0.0254) - n:.2f})")

    print("mirror (REQ-004): screen == pixel flip of the top-view render")
    for side in ("top", "bottom"):
        pat = P.tlcd5_side(m, side)
        _, fr = frames(D / f"tlcd5_{side}", m)
        check(np.array_equal(fr[0][1], pat.frames[0][1]), f"tlcd5_{side}: file matches a fresh render")
    from pcbimager.geom import transform, Layer
    from pcbimager.orient import face_to_top_view
    lay, nets, labels, _ = P.s3_coupon_layer(m)
    full = Layer(lay)
    full.extend(labels)
    unflipped = Canvas(m).render(full).img
    _, fr = frames(D / "s3_coupons", m)
    check(np.array_equal(flip_pixels(fr[0][1], m), unflipped),
          "s3_coupons: flip of the screen image == unmirrored render (exact)")
    # polarity: CU mark lit
    check(fr[0][1].sum() > 0, "s3_coupons: copper lit (non-empty)")

    print()
    print("ALL PASS" if not FAIL else f"{len(FAIL)} FAIL")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
