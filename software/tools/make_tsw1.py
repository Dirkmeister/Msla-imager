#!/usr/bin/env python3
"""T-SW-1 test vehicle: the S-3 coupon panel on F.Cu, an F/CU/BOT target and a comb on B.Cu,
three through-hole pads as front-to-back references, ruler marks. Written as a KiCad 7 board,
then exported with kicad-cli exactly as the normal workflow would.

  python tools/make_tsw1.py --out artwork/tsw1         (needs kicad-cli on PATH for the exports)
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pcbimager.machine import Machine                       # noqa: E402
from pcbimager.kicad_out import Board                       # noqa: E402
from pcbimager.geom import Layer, Track                     # noqa: E402
from pcbimager.units import inch, mil                       # noqa: E402
from pcbimager import patterns as P                         # noqa: E402

THT_IN = ((-1.5, 0.0), (1.5, 0.0), (0.0, -0.75))   # front-to-back reference pads
B_COMB_IN = (0.0, 0.55)                            # bottom-side 10/10 comb centre


def bottom_comb(cx, cy):
    """10/10 mil comb on B.Cu: 7 lines along u then 7 along v, side by side."""
    lay = Layer()
    for k in range(7):
        d = (k - 3) * mil(20)
        lay.append(Track((cx - inch(0.30), cy + d), (cx - inch(0.05), cy + d), mil(10)))
        lay.append(Track((cx + inch(0.175) + d, cy - inch(0.125)), (cx + inch(0.175) + d, cy + inch(0.125)),
                         mil(10)))
    return lay


def build(out):
    m = Machine()
    out.mkdir(parents=True, exist_ok=True)
    lay, nets, labels, info = P.s3_coupon_layer(m)
    b = Board()
    b.layer(lay, "F.Cu")
    gu, gv = m.board_area_mm
    b.outline_rect(gu, gv)
    # KiCad text on F.Cu (reads normally from the top) and B.Cu (mirrored, as KiCad places it)
    for nm, box in info["sites"].items():
        b.text(nm, ((box[0] + box[2]) / 2, box[3] - inch(0.04)), inch(0.06), mil(10), "F.Cu")
    b.text("F", (inch(-0.25), inch(1.02)), inch(0.10), mil(15), "F.Cu")
    b.text("CU", (inch(0.05), inch(1.02)), inch(0.10), mil(15), "F.Cu")
    b.text("TSW1 TOP V0.1", (0, inch(0.86)), inch(0.06), mil(10), "F.Cu")
    b.text("F", (inch(0.25), inch(-0.35)), inch(0.30), inch(0.04), "B.Cu", mirror=True)
    b.text("CU", (inch(-0.25), inch(-0.35)), inch(0.20), inch(0.03), "B.Cu", mirror=True)
    b.text("BOT", (inch(-0.85), inch(-0.35)), inch(0.15), inch(0.025), "B.Cu", mirror=True)
    b.layer(bottom_comb(inch(B_COMB_IN[0]), inch(B_COMB_IN[1])), "B.Cu")
    for (u, v) in THT_IN:
        b.tht_pad((inch(u), inch(v)), inch(0.070), inch(0.035))
        for sgn in (-1, 1):   # crosses on B.Cu outside the pad ring
            b.track(Track((inch(u) + sgn * inch(0.06), inch(v)), (inch(u) + sgn * inch(0.18), inch(v)), mil(10)), "B.Cu")
            b.track(Track((inch(u), inch(v) + sgn * inch(0.06)), (inch(u), inch(v) + sgn * inch(0.18)), mil(10)), "B.Cu")
    pcb = out / "tsw1.kicad_pcb"
    b.write(pcb, "T-SW-1 test vehicle")
    return pcb


def export(pcb):
    out = pcb.parent
    kc = shutil.which("kicad-cli")
    if not kc:
        print("kicad-cli not found: open tsw1.kicad_pcb in KiCad and plot F.Cu, B.Cu, Edge.Cuts "
              "(Gerber) and drill (Excellon), plus SVG of F.Cu and B.Cu with board-area page size.")
        return
    g = out / "gerber"
    g.mkdir(exist_ok=True)
    subprocess.run([kc, "pcb", "export", "gerbers", "-l", "F.Cu,B.Cu,Edge.Cuts", "-o", str(g) + "/", str(pcb)],
                   check=True, capture_output=True)
    subprocess.run([kc, "pcb", "export", "drill", "-o", str(g) + "/", str(pcb)], check=True, capture_output=True)
    s = out / "svg"
    s.mkdir(exist_ok=True)
    for lyr, fn in (("F.Cu", "F_Cu.svg"), ("B.Cu", "B_Cu.svg")):
        subprocess.run([kc, "pcb", "export", "svg", "-l", f"{lyr},Edge.Cuts", "--page-size-mode", "2",
                        "--exclude-drawing-sheet", "--drill-shape-opt", "0",
                        "-o", str(s / fn), str(pcb)], check=True, capture_output=True)
    for p in sorted(out.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(out)}  {p.stat().st_size} B")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="artwork/tsw1")
    a = ap.parse_args()
    pcb = build(Path(a.out))
    export(pcb)
