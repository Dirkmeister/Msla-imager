# Test patterns (REQ-026)

`python tools/make_patterns.py --out out/patterns` writes each pattern as an IF-13 job folder, plus `flat/<name>.png` for single-frame patterns (native 1440 x 2560, 1-bit, lit = copper). `python tools/check_patterns.py` measures them.

Every pattern carries the polarity mark: copper text "CU", next to an "F". On the developed panel the letters must be resist (after etch, copper). Letters showing as voids in a solid block mean polarity is inverted somewhere. Text reads mirrored on screen and correctly on the copper (stamp rule, docs/orientation.md), except `tlcd5_screen`.

| Pattern | For | Frames | What it is | Pass reading |
|---|---|---|---|---|
| tlcd2_checker | T-LCD-2 (L2) | 1, display | Full-field 1 px checkerboard, pixel (i, j) lit when i + j even. ID block at mid-left | Every pixel alternates at center and 4 corners; no beat or blur |
| tlcd2_grating | T-LCD-2 (L2) | 1, display | 1 px frame on the outermost pixels; 64 x 64 px patches of 1-on-1-off lines (vertical, horizontal) at center and corners | All 4 edge lines visible (no crop or overscan); lines resolved at all 5 sites |
| tlcd3_ruler_1px | T-LCD-3 on screen (L2) | 1, display | 1 px lines on columns 80 and 2480 (2400 px = 4.4646 in, 113.40 mm) and rows 120 and 1320 (1200 px = 2.2323 in, 56.70 mm) | Center to center 4.4646 ± 0.0019 in |
| tlcd3_ruler_5px | T-LCD-3 / S-3 on copper (L2, L6) | 1, nominal time | Same centers, 5 px (9.30 mil) lines | Average of outside-to-outside and inside-to-inside = 4.4646 ± 0.0019 in |
| tlcd5_screen | T-LCD-5 (L2) | 1, display | Upright F, CU, arrow +U, FAR SIDE, FRONT, in screen view | From the operator position the F reads normally and upright. Sets native_rot_ccw / native_mirror |
| tlcd5_top, tlcd5_bottom | T-LCD-5 (L2), S-5 precursor | 1 each, nominal | Face text "F CU TOP" / "F CU BOT" through the converter's side path; crosses at top-view (1.6, 0.7), (-1.6, -0.7), (1.6, -0.7) in | Each face reads correctly from its side; crosses overlap through the board |
| s4_white | S-4 (L6) | 1, operator time | All lit except the ID block | Through-LCD clearing time for T_LCD |
| s4_black | S-4 (L6) | 1, operator time | All dark; the ID block's lit text is the positive control | At 3x nominal: only the ID text holds (REQ-010) |
| s1_coarse | S-1 (L6) | 13 (12 zones + blank), 679 s | 4 x 3 zones of 0.32 in, times 15, 21, 30, 42, 60, 85, 120, 170, 240, 339, 480, 679 s. Each zone: 10/10 comb along u, along v, a solid square, a solid square with a 10 mil cross slot. Times label each zone | First zone that holds; window of zones with clean 10/10 |
| s1_fine | S-1 (L6) | 9, end = start x 2^(7/4) | 8 zones at 2^(1/4) from `--fine-start` (default 60 s is a placeholder) | Nominal = window center; window ≥ 3 fine steps |
| s2_map | S-2 (L6) | 9 | 4 x 7 cells A1..D7 (cell edges on pixel columns 0, 366, 731, 1097, 1463, 1829, 2194, 2560 and rows 0, 360, 720, 1080, 1440), 8 solid sub-zones each at `--map-centre` x 2^((j - 3.5)/4) (default 120 s is a placeholder) | First sub-zone that holds per cell; 1 sub-zone = 2^(1/4) in irradiance |
| s3_coupons | S-3 (L6), T-SW-1 | 1, nominal | 5 sites (C, TL, TR, BL, BR) x 5 sizes (5/5 to 25/25) x 2 orientations of serpentine-comb structures; ruler marks 2400 px apart | Opens: S_A to S_B; shorts: S to C_L, S to C_R; 10 ± 2 mil at 10/10 |

Wedges use progressive masking: every zone starts lit at UV on and goes dark at its own time, so each zone is a real cold-start exposure of that length. Zone positions are in each job's `zones` for correcting with the S-2 map.

Coupon pads (0.045 in square): S_A bottom-left, C_L top-left, S_B top-right, C_R bottom-right for runs along u; rotated 90° for runs along v. Path lengths for 4-wire width estimates are in the job's `zones`.

Placeholders to replace after S-1 coarse: `--fine-start` (one coarse step below the first good zone) and `--map-centre`. Suggestion for L6: center the map on the hold threshold rather than the nominal, since the map reads where each cell first holds.
