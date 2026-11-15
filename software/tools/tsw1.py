#!/usr/bin/env python3
"""T-SW-1: the converter test that decides D-08 (Gerber + Excellon vs SVG).

Builds the T-SW-1 board (tools/make_tsw1.py), exports it with kicad-cli, converts it through both
paths (normal and inverted), reads the job PNGs back from disk and measures:
  widths     10 mil lines = 5 px on all 10 structures at 10/10 (5 sites x 2 orientations), and
             every other size = round(s / 47.25 um); bottom-side comb too
  spaces     10/10 spaces are 5 or 6 px
  ruler      two 10 mil lines, centres exactly 2400 px apart
  opens/shorts  connected components on all 50 serpentine-comb structures
  pads       0.045 in square pads: size in px (R1 keeps 24 x 24; R2 may not)
  mirror     top screen image is the flip of the board: through-hole pad centres on top and bottom
             coincide in board coordinates, and the asymmetric pad lands where the flip puts it
  invert     inverted job == bitwise NOT of the normal job
  vs direct  pixel differences against a direct render of the same geometry (structures only)
Pass/fail per imager-06 T-SW-1. D-08 rule (imager-03): first to pass wins; Gerber carries drills.

  python tools/tsw1.py --out out/tsw1
  python tools/tsw1.py --out out/tsw1 --use-existing    (after plotting artwork/tsw1/tsw1.kicad_pcb
                                                         from your KiCad into artwork/tsw1/gerber, /svg)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pcbimager.machine import Machine, Calibration                       # noqa: E402
from pcbimager.convert import convert, LayerSpec                         # noqa: E402
from pcbimager.raster import load_png_bool, from_native, Canvas          # noqa: E402
from pcbimager.orient import topview_to_screen_affine, render_topview    # noqa: E402
from pcbimager.geom import Layer, Flash, Track                           # noqa: E402
from pcbimager.units import px_count, mil, inch                          # noqa: E402
from pcbimager import patterns as P                                      # noqa: E402
sys.path.insert(0, str(ROOT / "tools"))
import make_tsw1 as MT                                                   # noqa: E402


def runs(v):
    v = np.asarray(v, dtype=np.int8)
    e = np.flatnonzero(np.diff(v)) + 1
    b = np.concatenate([[0], e, [len(v)]])
    return [(bool(v[x]), int(y - x)) for x, y in zip(b[:-1], b[1:])]


def scr(m, pt_mm, side):
    x, y = Canvas(m).T(topview_to_screen_affine(m, side)(pt_mm))
    return x, y


def job_images(d, m):
    man = json.loads((d / "job.json").read_text())
    out = {}
    for e in man["exposures"]:
        out[e["side"]] = from_native(load_png_bool(d / e["frames"][0]["file"]), m)
    return out, man


def measure(m, imgs):
    top, bot = imgs["top"], imgs["bottom"]
    R = {}
    _, nets, _, info = P.s3_coupon_layer(m)
    widths, spaces10, wrong = {}, set(), []
    for nd, mt in nets:
        s = mt["s_mil"]
        n = px_count(mil(s))
        x, y = scr(m, mt["centre_mm"], "top")
        cx, cy = int(np.floor(x)), int(np.floor(y))
        half = int(np.ceil(4.5 * mil(s) / m.pitch_mm)) + 2
        line = top[cy - half:cy + half + 1, cx] if mt["orient"] == "u" else top[cy, cx - half:cx + half + 1]
        rr = runs(line)
        core = [L for v, L in rr if v]
        gaps = [L for v, L in rr[1:-1] if not v]
        widths.setdefault(s, set()).update(core)
        if s == 10:
            spaces10.update(gaps)
        if core != [n] * 5:
            wrong.append((mt["site"], s, mt["orient"], core))
    R["widths_px"] = {s: sorted(v) for s, v in widths.items()}
    R["wrong_structures"] = wrong
    R["spaces_10_px"] = sorted(spaces10)
    # connectivity
    l4, _ = ndimage.label(top, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    l8, _ = ndimage.label(top, structure=np.ones((3, 3)))
    opens = shorts = 0
    pad_sizes = set()
    for nd, mt in nets:
        pads = {}
        for k, p in mt["pads"].items():
            x, y = scr(m, p, "top")
            pads[k] = (int(np.floor(x)), int(np.floor(y)))
        a4 = {k: l4[y, x] for k, (x, y) in pads.items()}
        a8 = {k: l8[y, x] for k, (x, y) in pads.items()}
        if not a4["S_A"] or a4["S_A"] != a4["S_B"]:
            opens += 1
        if a8["S_A"] in (a8["C_L"], a8["C_R"]) or a8["C_L"] == a8["C_R"] or 0 in a8.values():
            shorts += 1
        for k, (x, y) in pads.items():   # pad extent through its centre
            row = runs(top[y, x - 20:x + 21])
            col = runs(top[y - 20:y + 21, x])
            # leads enter each pad from one side, so the run across the lead axis is the pad size
            pad_sizes.add(min(max(L for v, L in row if v), max(L for v, L in col if v)))
    R["opens"], R["shorts"] = opens, shorts
    R["pad_sizes_px"] = sorted(pad_sizes)
    # ruler: 10 mil lines at u = ru (top view), measured on screen row through v = 0
    ru = info["ruler_u_mm"]
    y = int(np.floor(scr(m, (0.0, 0.0), "top")[1]))
    cents = []
    for u in ru:
        x = int(np.floor(scr(m, (u, 0.0), "top")[0]))
        seg = top[y, x - 15:x + 16]
        lit = np.flatnonzero(seg)
        cents.append((x - 15 + lit.min() + x - 15 + lit.max() + 1) / 2 if len(lit) else None)
        R.setdefault("ruler_line_px", []).append(int(len(lit)))
    R["ruler_spacing_px"] = None if None in cents else cents[1] - cents[0]
    # bottom comb
    bw, bs = set(), set()
    cx, cy = inch(MT.B_COMB_IN[0]), inch(MT.B_COMB_IN[1])
    for (pu, pv, axis) in ((cx - inch(0.175), cy, 0), (cx + inch(0.175), cy, 1)):
        x, yy = scr(m, (pu, pv), "bottom")
        x, yy = int(np.floor(x)), int(np.floor(yy))
        line = bot[yy - 50:yy + 51, x] if axis == 0 else bot[yy, x - 50:x + 51]
        rr = runs(line)
        bw.update(L for v, L in rr[1:-1] if v)
        bs.update(L for v, L in rr[1:-1] if not v)
    R["bottom_comb_widths_px"], R["bottom_comb_spaces_px"] = sorted(bw), sorted(bs)
    # mirror: through-hole pad centroids, both sides, back to board coordinates
    errs, flip_ok = [], True
    for (u, v) in MT.THT_IN:
        cents = {}
        for side, img in (("top", top), ("bottom", bot)):
            x, yv = scr(m, (inch(u), inch(v)), side)
            x, yv = int(np.floor(x)), int(np.floor(yv))
            win = img[yv - 25:yv + 26, x - 25:x + 26]
            lab, _ = ndimage.label(win)
            k = lab[25, 25]
            if k == 0:
                flip_ok = False
                continue
            ys, xs = np.nonzero(lab == k)
            cents[side] = (x - 25 + xs.mean() + 0.5, yv - 25 + ys.mean() + 0.5)
        if len(cents) == 2:
            # undo the screen flip of the top side: y -> H - y (long axis) or x -> W - x
            tx, ty = cents["top"]
            if m.flip_axis == "long":
                ty = m.image_h - ty
            else:
                tx = m.image_w - tx
            errs.append((round(tx - cents["bottom"][0], 3), round(ty - cents["bottom"][1], 3)))
    R["front_to_back_px"] = errs
    # asymmetric check: the (0, -0.75) pad must appear at the flipped spot on the top screen image
    x, yflip = scr(m, (0.0, inch(-0.75)), "top")
    x, yraw = Canvas(m).T((0.0, inch(-0.75)))
    R["top_is_flipped"] = bool(top[int(yflip), int(x)]) and (
        m.flip_axis != "long" or not top[int(yraw), int(x)])
    return R


def direct_reference(m):
    """Direct render of the same geometry (no text) and the mask of where to compare."""
    lay, nets, labels, info = P.s3_coupon_layer(m)
    tv = Layer(lay)
    for (u, v) in MT.THT_IN:
        tv.append(Flash((inch(u), inch(v)), "circle", inch(0.070)))
    top = render_topview(m, tv, "top")
    mask = np.zeros_like(top)
    for nd, mt in nets:
        allp = Layer()
        for v in nd.values():
            allp.extend(v)
        from pcbimager.geom import bbox
        b = bbox(allp)
        (x0, y0), (x1, y1) = scr(m, (b[0], b[1]), "top"), scr(m, (b[2], b[3]), "top")
        xa, xb = sorted((int(x0) - 2, int(x1) + 3))
        ya, yb = sorted((int(y0) - 2, int(y1) + 3))
        mask[ya:yb, xa:xb] = True
    return top, mask


def evaluate(R, pixdiff):
    crit = {
        "10 mil lines = 5 px (all 10 structures)": R["widths_px"].get(10) == [5],
        "10/10 spaces 5 or 6 px": set(R["spaces_10_px"]) <= {5, 6} and R["spaces_10_px"] != [],
        "every size = round(s/47.25 um)": not R["wrong_structures"],
        "bottom comb 5 px, spaces 5 or 6": R["bottom_comb_widths_px"] == [5]
                                          and set(R["bottom_comb_spaces_px"]) <= {5, 6},
        "ruler exactly 2400 px": R["ruler_spacing_px"] == 2400,
        "no opens, no shorts (50 structures)": R["opens"] == 0 and R["shorts"] == 0,
        "mirror: front-to-back <= 0.5 px": bool(R["front_to_back_px"]) and len(R["front_to_back_px"]) == 3
                                            and all(abs(a) <= 0.5 and abs(b) <= 0.5 for a, b in R["front_to_back_px"]),
        "mirror: top image is flipped": R["top_is_flipped"],
        "invert = bitwise NOT": R["invert_exact"],
        "drills carried": R["holes_in_job"] == len(MT.THT_IN),
    }
    return crit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/tsw1")
    ap.add_argument("--artwork", default=str(ROOT / "artwork/tsw1"))
    ap.add_argument("--use-existing", action="store_true",
                    help="measure the exports already in <artwork>/gerber and <artwork>/svg "
                         "(e.g. plotted from your own KiCad) instead of rebuilding and re-exporting")
    a = ap.parse_args()
    m = Machine()
    art = Path(a.artwork)
    if not a.use_existing:
        pcb = MT.build(art)
        MT.export(pcb)
    g, s = art / "gerber", art / "svg"
    out = Path(a.out)
    paths = {
        "gerber": ([LayerSpec(str(g / "tsw1-F_Cu.gtl"), "top"), LayerSpec(str(g / "tsw1-B_Cu.gbl"), "bottom")],
                   dict(outline=str(g / "tsw1-Edge_Cuts.gm1"), drill=str(g / "tsw1.drl"))),
        "svg": ([LayerSpec(str(s / "F_Cu.svg"), "top", "svg"), LayerSpec(str(s / "B_Cu.svg"), "bottom", "svg")], {}),
    }
    ref_top, mask = direct_reference(m)
    table, raw = {}, {}
    for name, (specs, kw) in paths.items():
        r = convert(f"tsw1_{name}", specs, out, label="TSW1", **kw)
        imgs, man = job_images(r.job_dir, m)
        R = measure(m, imgs)
        specs_inv = [LayerSpec(sp.path, sp.side, sp.fmt, invert=True) for sp in specs]
        ri = convert(f"tsw1_{name}_inv", specs_inv, out, label="TSW1", **kw)
        imgs_i, _ = job_images(ri.job_dir, m)
        R["invert_exact"] = all(np.array_equal(imgs_i[k], ~imgs[k]) for k in imgs)
        diff = int(((imgs["top"] != ref_top) & mask).sum())
        R["pixels_differing_from_direct_render"] = diff
        R["holes_in_job"] = man.get("converter_report", {}).get("holes", 0)
        raw[name] = R
        table[name] = evaluate(R, diff)
    print("\nT-SW-1 results")
    names = list(table)
    w = max(len(c) for c in table[names[0]])
    print(f"{'criterion':{w}s}  " + "  ".join(f"{n:>7s}" for n in names))
    for c in table[names[0]]:
        print(f"{c:{w}s}  " + "  ".join(f"{('PASS' if table[n][c] else 'FAIL'):>7s}" for n in names))
    for n in names:
        R = raw[n]
        print(f"\n[{n}] widths {R['widths_px']} spaces10 {R['spaces_10_px']} ruler {R['ruler_spacing_px']} px "
              f"(lines {R['ruler_line_px']} px) pads {R['pad_sizes_px']} f2b {R['front_to_back_px']} "
              f"holes {R['holes_in_job']} vs-direct {R['pixels_differing_from_direct_render']} px")
    passed = {n: all(t.values()) for n, t in table.items()}
    print("\npaths passing:", [n for n, ok in passed.items() if ok])
    (out / "tsw1_results.json").write_text(json.dumps({"criteria": table, "measurements": raw}, indent=1,
                                                     default=lambda o: list(o) if isinstance(o, (set, tuple)) else str(o)))
    return 0 if any(passed.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
