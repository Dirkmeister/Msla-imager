# T-SW-1 results and D-08

Run 2026-11-14 with `python tools/tsw1.py`: the T-SW-1 board (`artwork/tsw1/tsw1.kicad_pcb`, made by `tools/make_tsw1.py`) exported by kicad-cli 7.0.11, converted through both paths, PNGs read back from the job folders and measured.

Board: F.Cu holds the S-3 coupon panel (5 sites x 5 sizes x 2 orientations = 50 serpentine-comb structures, 200 square pads of 0.045 in), ruler marks 2400 px apart and KiCad text F, CU, site names. B.Cu holds F, CU, BOT (KiCad back-side text), a 10/10 comb along u and v, and crosses. Three through-hole pads (0.070 in pad, 0.035 in drill) at (-1.5, 0), (1.5, 0), (0, -0.75) in serve as front-to-back references. Edge.Cuts = the v1 board area, 4.5622 x 2.4787 in.

| Criterion | Gerber + Excellon | SVG |
|---|---|---|
| 10 mil lines = 5 px (all 10 structures) | PASS | PASS |
| 10/10 spaces 5 or 6 px | PASS | PASS |
| every size = round(s/47.25 um) | PASS | PASS |
| bottom comb 5 px, spaces 5 or 6 | PASS | PASS |
| ruler exactly 2400 px | PASS | PASS |
| no opens, no shorts (50 structures) | PASS | PASS |
| mirror: front-to-back <= 0.5 px | PASS | PASS |
| mirror: top image is flipped | PASS | PASS |
| invert = bitwise NOT | PASS | PASS |
| drills carried | PASS | FAIL |

The first nine rows are imager-06 T-SW-1 as written. "Drills carried" is the D-08 tie-break ("Gerber carries drills").

| Measurement | Gerber | SVG |
|---|---|---|
| Line widths by size, px | {'5': [3], '10': [5], '15': [8], '20': [11], '25': [13]} | {'5': [3], '10': [5], '15': [8], '20': [11], '25': [13]} |
| 10/10 spaces, px | [5, 6] | [5, 6] |
| Ruler, center to center | 2400.0 px | 2400.0 px |
| 0.045 in pads, px | [24] | [24, 25] |
| Front-to-back, through-hole pad centers (dx, dy) px | [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)] | [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)] |
| Opens / shorts (50 structures) | 0 / 0 | 0 / 0 |
| Holes in the job | 3 | 0 |
| Pixels differing from a direct render of the same geometry (structure areas) | 0 | 1367 |

## D-08: Gerber X2 + Excellon

Both paths pass T-SW-1 as written, in the same run, so the tie-break decides: Gerber carries the drills. The measurements add two reasons:
- Pads: Gerber keeps flash semantics, so R1 holds and every 0.045 in pad is exactly 24 px. SVG delivers pads as filled paths (R2), 24 or 25 px.
- Fidelity: the Gerber path reproduces a direct render of the same geometry pixel for pixel (0 differing). The SVG path differs in 1367 px, all at pads.

SVG stays in the converter as a fallback (p.77 asked for SVG) but is not the supported path.

## Limits of this run

- KiCad 7.0.11 in the sandbox. To close T-SW-1 on your own KiCad: open `artwork/tsw1/tsw1.kicad_pcb`, plot F.Cu, B.Cu and Edge.Cuts as Gerber (default names, `tsw1-F_Cu.gtl` etc.) plus the Excellon drill file into `artwork/tsw1/gerber/`, plot F.Cu + Edge.Cuts and B.Cu + Edge.Cuts to SVG (color, board area only) as `artwork/tsw1/svg/F_Cu.svg` and `B_Cu.svg`, then run `python tools/tsw1.py --use-existing`.
- The test board uses plain rect pads. KiCad's default roundrect pads come out as aperture macros, which take R2 (± 1 px). Recognizing KiCad's RoundRect macro as an R1 pad is a small follow-up if pad size matters.
- On screen only. T-LCD-3 and S-3 then measure the same files on the LCD and on copper.
