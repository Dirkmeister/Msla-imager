#!/usr/bin/env python3
"""Generate the REQ-026 test patterns as IF-13 job folders, plus flat PNGs of single-frame patterns.

  python tools/make_patterns.py --out out/patterns
  python tools/make_patterns.py --out out/patterns --only s1_fine --fine-start 85
  python tools/make_patterns.py --out out/patterns --only s2_map --map-centre 170

--machine config/machine.json sets native orientation, flip axis, etc. (defaults match it).
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pcbimager.machine import Machine, Calibration          # noqa: E402
from pcbimager import patterns as P                         # noqa: E402
from pcbimager.job import write_job, exposure_from_pattern, verify_job   # noqa: E402
from pcbimager.raster import to_native, save_png_1bit       # noqa: E402

BUILDERS = {
    "tlcd2_checker": lambda m, a: P.tlcd2_checker(m),
    "tlcd2_grating": lambda m, a: P.tlcd2_grating(m),
    "tlcd3_ruler_1px": lambda m, a: P.tlcd3_ruler(m, 1),
    "tlcd3_ruler_5px": lambda m, a: P.tlcd3_ruler(m, 5),
    "tlcd5_screen": lambda m, a: P.tlcd5_screen(m),
    "tlcd5_top": lambda m, a: P.tlcd5_side(m, "top"),
    "tlcd5_bottom": lambda m, a: P.tlcd5_side(m, "bottom"),
    "s4_white": lambda m, a: P.s4_white(m),
    "s4_black": lambda m, a: P.s4_black(m),
    "s1_coarse": lambda m, a: P.s1_coarse(m),
    "s1_fine": lambda m, a: P.s1_fine(m, a.fine_start),
    "s2_map": lambda m, a: P.s2_map(m, a.map_centre),
    "s3_coupons": lambda m, a: P.s3_coupons(m),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="out/patterns")
    ap.add_argument("--machine", default=None)
    ap.add_argument("--only", nargs="*", choices=sorted(BUILDERS))
    ap.add_argument("--fine-start", type=float, default=60.0,
                    help="S-1 fine wedge start, s: one coarse step below the first good coarse zone "
                         "(default 60 is a placeholder)")
    ap.add_argument("--map-centre", type=float, default=120.0,
                    help="S-2 map centre time, s (default 120 is a placeholder)")
    a = ap.parse_args()
    m = Machine.load(a.machine)
    out = Path(a.out)
    flat = out / "flat"
    flat.mkdir(parents=True, exist_ok=True)
    for name in (a.only or BUILDERS):
        t0 = time.time()
        pat = BUILDERS[name](m, a)
        ex = exposure_from_pattern(pat)
        d = write_job(out, name, [ex], m, Calibration(),
                      purpose={"test": pat.test, "notes": pat.notes, "params": pat.params},
                      zones=pat.zones or None)
        probs = verify_job(d)
        if len(pat.frames) == 1:
            save_png_1bit(to_native(pat.frames[0][1], m), flat / f"{name}.png")
        print(f"{name:16s} {len(pat.frames):2d} frame(s) {time.time() - t0:5.1f} s "
              f"{'OK' if not probs else probs}")


if __name__ == "__main__":
    main()
