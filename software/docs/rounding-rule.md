# Pixel rounding rule (REQ-023, imager-04 §2)

Pitch p = 47.25 µm = 1.860 mil. Pixel edges at integers, pixel centers at k + 0.5.

- **R1, size first.** Tracks, round, rect and obround pads keep their size: n = round_half_up(size / p), at least 1 px. The center line (or center point) snaps to the nearest pixel center when n is odd and to the nearest pixel edge when n is even, so the feature is exactly n px wide wherever it sits. Spaces take the remainder.
- **R2, regions.** Pours, polygons, aperture-macro pads (KiCad roundrect), rotated pads and SVG fills: a pixel is lit when its center is inside the shape (nonzero winding, half-open spans). Edges land on the nearest pixel boundary, so sizes are ± 1 px.
- **R3, no gray.** A pixel is lit when its center is strictly inside the snapped shape. No anti-aliasing.
- **R4, curves.** Arcs and text strokes keep the R1 width but are not snapped.
- Ties (a center exactly on a snap boundary) break toward +x and +y in the render frame. With the mirrored side rendered unmirrored and pixel-flipped, a tied feature lands at the same board position on both faces.

| Feature, mil | 5 | 8 | 10 | 15 | 20 | 25 |
|---|---|---|---|---|---|---|
| Line, px | 3 | 4 | 5 | 8 | 11 | 13 |
| Line, mil (mm) | 5.58 (0.142) | 7.44 (0.189) | 9.30 (0.236) | 14.88 (0.378) | 20.46 (0.520) | 24.18 (0.614) |
| Space at s/s, px | 2 or 3 | 4 or 5 | 5 or 6 | 8 or 9 | 10 or 11 | 13 or 14 |

Space at s/s: pitch 2s / p minus n. At 10/10: 20 / 1.860 = 10.75 px pitch, minus 5 = 5.75 px, so 5 or 6 px by position. At 5/5 the 3 px line leaves 2.38 px on average, so spaces of 2 px (3.72 mil, 0.094 mm) occur: 5/5 prints tighter than drawn.

Measured (tools/check_patterns.py, tools/tsw1.py): 10 mil tracks at 300 random positions all 5 px; 0.060 x 0.030 in rect pads at 300 random positions all 32 x 16 px; all 50 coupon structures at their sizes; 10/10 spaces only 5 and 6 px.

Not yet in the rule: per-orientation bias for the RGB stripes (`bias_px_u`, `bias_px_v` in the machine config, default 0). Set only if S-3 fails in one orientation (imager-06 failure responses).
