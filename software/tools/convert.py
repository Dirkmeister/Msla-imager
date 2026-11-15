#!/usr/bin/env python3
"""Converter v0 CLI: KiCad Gerber + Excellon (or SVG) -> IF-13 job folder.

Gerber (recommended):
  python tools/convert.py --job flasher --out out/jobs \\
      --top board-F_Cu.gtl --bottom board-B_Cu.gbl --outline board-Edge_Cuts.gm1 --drill board.drl
SVG (export each copper layer with Edge.Cuts, colour mode, page size 'board area only'):
  python tools/convert.py --job flasher --out out/jobs --top-svg F_Cu.svg --bottom-svg B_Cu.svg
Options: --rotate 90, --offset U V (inches), --invert-top/--invert-bottom, --machine config/machine.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pcbimager.convert import convert, LayerSpec      # noqa: E402
from pcbimager.machine import Machine, Calibration    # noqa: E402
from pcbimager.job import verify_job                  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job", required=True)
    ap.add_argument("--out", default="out/jobs")
    ap.add_argument("--top")
    ap.add_argument("--bottom")
    ap.add_argument("--top-svg")
    ap.add_argument("--bottom-svg")
    ap.add_argument("--outline")
    ap.add_argument("--drill")
    ap.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270])
    ap.add_argument("--offset", type=float, nargs=2, default=(0.0, 0.0), metavar=("U", "V"))
    ap.add_argument("--invert-top", action="store_true")
    ap.add_argument("--invert-bottom", action="store_true")
    ap.add_argument("--machine")
    ap.add_argument("--calibration")
    ap.add_argument("--no-template", action="store_true")
    a = ap.parse_args()
    specs = []
    for side, g, s, inv in (("top", a.top, a.top_svg, a.invert_top), ("bottom", a.bottom, a.bottom_svg, a.invert_bottom)):
        if g:
            specs.append(LayerSpec(g, side, "gerber", invert=inv))
        elif s:
            specs.append(LayerSpec(s, side, "svg", invert=inv))
    if not specs:
        ap.error("give at least one layer")
    r = convert(a.job, specs, a.out, outline=a.outline, drill=a.drill, rotate_deg=a.rotate,
                offset_in=tuple(a.offset), machine=Machine.load(a.machine),
                calibration=Calibration.load(a.calibration), template=not a.no_template)
    print(json.dumps(r.report, indent=1))
    probs = verify_job(r.job_dir)
    print("job:", r.job_dir, "OK" if not probs else probs)


if __name__ == "__main__":
    main()
