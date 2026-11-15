# pcb-imager

Computer-side software for the MSLA PCB imager (MSLA PRINTER Project, lane L4): the test-pattern generator (REQ-026), the Gerber-to-PNG converter (REQ-022, D-08 = Gerber X2 + Excellon), and the IF-13 job format the Pi reads. The Pi app comes later (waits on L2's display method and L3's IF-09).

All output frames are 1-bit PNGs at the panel's native 1440 x 2560 (47.25 µm), copper lit.

## Install

```
pip install -r requirements.txt          # Python 3.10+
```
KiCad's `kicad-cli` on PATH is only needed to regenerate the T-SW-1 exports.

## Use

```
python tools/make_patterns.py --out out/patterns                 # all test patterns (docs/patterns.md)
python tools/make_patterns.py --only s1_fine --fine-start 85     # after S-1 coarse
python tools/make_patterns.py --only s2_map --map-centre 170
python tools/check_patterns.py --dir out/patterns                # measures every pattern

python tools/convert.py --job flasher --out out/jobs \
    --top flasher-F_Cu.gtl --bottom flasher-B_Cu.gbl \
    --outline flasher-Edge_Cuts.gm1 --drill flasher.drl          # board -> IF-13 job

python tools/tsw1.py --out out/tsw1                              # T-SW-1 (docs/tsw1.md)
```

KiCad plot settings for the converter: Gerber, F.Cu, B.Cu, Edge.Cuts, default options; drill file Excellon, mm, absolute origin. Draw the board outline on Edge.Cuts: the converter centers its bounding box on the panel.

## Layout

| Path | What |
|---|---|
| `pcbimager/units.py` | Rounding rule R1 to R4 (docs/rounding-rule.md) |
| `pcbimager/raster.py` | 1-bit rasterizer, native orientation, PNG I/O |
| `pcbimager/orient.py` | Stamp rule, flip axis, mirrored side (docs/orientation.md) |
| `pcbimager/patterns.py`, `coupons.py`, `marks.py`, `font.py` | Pattern generator, S-3 coupons, CU/F marks, Hershey stroke text |
| `pcbimager/gerber_in.py`, `svg_in.py`, `convert.py` | Converter v0 |
| `pcbimager/job.py` | IF-13 writer and loader checks (docs/IF-13.md) |
| `pcbimager/kicad_out.py` | Writes test-vehicle boards as .kicad_pcb |
| `config/machine.json` | Machine geometry; three values pending (below) |
| `out/patterns/` | Generated patterns, committed so L2 and L6 can use them without running anything |
| `artwork/tsw1/` | T-SW-1 board and its KiCad 7.0.11 exports |

## Pending values (config/machine.json)

| Key | Default | Set by |
|---|---|---|
| `native_rot_ccw`, `native_mirror` | 90, false | L2, T-LCD-5 with `tlcd5_screen` |
| `flip_axis` | "long" | L5, D-14 |
| `mirrored_side` | "top" | Physics (docs/orientation.md); overrule only on a T-LCD-5 result |

Change one, re-run `make_patterns.py`, and the job manifests record what the frames were rendered for.
