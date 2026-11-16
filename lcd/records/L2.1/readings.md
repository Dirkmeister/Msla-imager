L2 LCD mask
# L2.1 LCD inspection: readings and photo record

Package L2.1 (imager-09): T-LCD-1, T-LCD-4, panel outline, driver ID. Bench work by Dallas; photo readings by the L2.1 thread.

Status: photo batch 1 in (2026-11-15). Measurements pending.

Marks: [?] unsure reading. (inference) not measured or not printed on the part. EST estimate.

## Photos

Batch 1 has no scale in frame; dimensions come from the caliper and micrometer, not from these photos. Photos are cropped to the part at native resolution (phone files arrived at 1512 x 2016 px).

| File | What | Notes |
|---|---|---|
| P01_chain_as_received.jpg | Whole chain on its MDF board, as found | Marker labels: "LCD Driver Module", "HDMI → MIPI", "Converter Board", "2K Monochrome LCD", "Raspi Zero" (4 brass standoffs, no Pi fitted), "HDMI" arrow, "PWR" at the driver's gold mini-USB and at the Pi position |
| P02_panel_front.jpg | Panel front, unpowered | Fine scratches across much of the front face, on the polarizer or on a film over it [?] |
| P03_panel_back.jpg | Panel back | Uniform silver sheet. Printed code near one corner reads "04DS40?9" [?]; the rest is not legible. No model label seen |
| P04_edge_long.jpg | One long edge, panel lifted (inference: the edge on the label side) | Layered edge with a bright white band (inference: light-guide edge). Not measurable from the photo |
| P08_fpc_end.jpg | FPC end close-up | FPC bonded across the ledge; black FPC section with pad windows under green coating; small orange tab (Z08); blue tabs at both FPC-end corners; translucent white block near one corner |
| P10_converter_side1.jpg | Converter board, ribbon side | Silkscreen "Sharp04" and "Copyright © YX Electronics 2017". 4 mounting holes: 2 fitted with hex-socket screws (diagonal), 2 empty. No ICs on this face. The panel FPC enters under a silver stiffener |
| P13_driver_side1.jpg | Driver board, component side | Silkscreen "HDMI TO MIPI", "Version 3.2". The listing calls it VS-CXMIPI-V1; that name is not on this face |
| Z08_led_tab_x3.jpg | 3x zoom of the small orange tab on the panel FPC | Printed "LE" (boxed, small mark beside it) [?] and "H3617DP" [?]. 3 solder pads under clear coating; a 3-conductor flex runs from the pads into the module at the FPC-end corner |
| Z10_converter_ffc_tails_60.png | Converter board's ribbon connector, tails marked | 60 counted |
| Z13_driver_ffc_tails_60.png | Driver board's ribbon connector, contacts marked | 60 counted; silkscreen "1" at one end |

## Read from the photos (batch 1)

### Chain (IF-12)

Pi (not on the board) → HDMI → driver board "HDMI TO MIPI Version 3.2" → grey FFC ribbon → converter board "Sharp04" → panel FPC (into the converter board under the silver stiffener) → panel.

| Connector | Pins or type | How |
|---|---|---|
| Driver board, ribbon connector | 60 | Photo count, Z13 (±1 at the ends, EST) |
| Converter board, ribbon connector | 60 | Photo count, Z10 (±1 at the ends, EST) |
| Grey ribbon | 60, from both ends | Printed "AWM 20624 80C 60V VW-1" |
| Panel FPC into the converter board | Not counted; the listing says 50 | Under the stiffener; counting needs unplugging, not done |
| Driver video input | Full-size HDMI receptacle (type A) | P13 |
| Driver power | Gold mini-USB (Dallas's PWR label), silver micro-USB, two pads marked "5V-12V +" | P13. The listing gives 5 V, more than 1 A, on micro-USB. Which input is power is left to L2.2 |
| Driver header pads | "G RX TX 5V" and "RST DA CK G 3.3V" | P13 |

The listing's two pin counts fit this chain (inference): 60 pins on the driver board and ribbon side, 50 on the panel's own connector, with the converter board adapting one to the other.

### Chip markings, driver board top face (P13)

| Part | Package | Marking |
|---|---|---|
| Center IC | Square QFN | Not legible in P13 |
| IC, lower left | TSSOP-20 | Not legible in P13 |
| Regulator | SOT-223 | Line 1 "AMS1117" [?]; line 2 not legible |
| IC beside the "4R7" inductor | Small QFN or DFN | Not legible in P13 |
| Inductor | Shielded SMD | "4R7" |

Converter board, ribbon side: no ICs.

### Backlight (inference, to confirm at the bench)

A white backlight looks fitted: the silver back (P03), the white band in the edge (P04), and a 3-conductor flex from the module soldered to the "LE" tab on the panel FPC (Z08), which reads as the backlight's LED flex. If that is confirmed, it counts as bonded under the L2 lead's rule and stays on in L2.1.

### Panel type

The MDF board label says "2K Monochrome LCD" (P01, Dallas's marker). The listing gives 1440 (RGB) x 2560, and the vendor spec gives R, G, B vertical stripes (imager-03 D-13). The stripe check (T-LCD-1) decides.

### Front face

Fine scratches across much of the front (P02). The blue tabs at both FPC-end corners (P08) may belong to a film over the polarizer [?]. Nothing peeled.

## Panels on hand

Two (Dallas, 2026-11-15). Panel 1: on the MDF board with the converter and driver boards, backlight fitted (inference above). Panel 2: "the same, but from the printer, and has everything removed" (Dallas). Panel 2 takes the cell readings A, B, C (no backlight under the glass); panel 1 takes the module reading M and the stripe check. Label and outline comparison pending.

## Vendor pages

Dallas's link is K002211 on VSDISPLAY's own site; K002146 is the same vendor's no-backlight kit; the Newegg listing is the one in imager-03. Inches from mm / 25.4.

| Item | K002211 (Dallas's link) | K002146 (no-backlight kit) | Newegg listing |
|---|---|---|---|
| Panel | LS055R1SX04; normally black, transmissive; WLED backlight; title says it can ship without backlight for 3D printers | LS055R1SX04, backlight removed | LS055R1SX04, WLED backlight |
| Outline, H x V x D | 2.793 x 5.059 x 0.0571 in (70.94 x 128.49 x 1.45 mm) | Same figures, with the backlight removed | Same figures |
| Active area | 2.679 x 4.762 in (68.04 x 120.96 mm) | Same | Same |
| Panel connector | 50 pins | 50 pins | 50 pins |
| Driver board | VS-CXMIPI-V1, 2.362 x 1.575 x 0.118 in (60 x 40 x 3 mm), "40Pin Mipi LCD Screen" | VS-HDMITMIPI-V1, 2.559 x 2.520 x 0.118 in (65 x 64 x 3 mm), "50Pin Mipi LCD Screen", "60Pin Cable" | VS-CXMIPI-V1, 2.756 x 1.575 x 0.197 in (70 x 40 x 5 mm), "60Pin Mipi LCD Screen" |
| Refresh | Not stated | Not stated | 50 Hz only |
| Power | 5 V, more than 1 A, micro-USB; standby under 0.3 W | 5 V, more than 1 A; standby under 0.3 W | 5 V, more than 1 A, micro-USB; standby under 0.3 W |
| Packing list | Driver board, panel, signal cable, converter board, 8 Ω 2 W speaker | Driver board, panel (backlight removed), signal cable, converter board | Driver board, panel, signal cable, converter board |

Reading of the pages: they are template copies. The no-backlight kit repeats the 1.45 mm thickness, so the vendor figure can't tell the module from the bare cell; the micrometer decides (panel 1 M, panel 2 A). The driver board's size and pin count differ page to page; the caliper decides the size. The photo count (60 on the ribbon side) matches K002146's "60Pin Cable" and Newegg's 60, so K002211's "40Pin" looks like a copy error (inference). Panel 2's exposed plug can settle the panel's 50.

Sources: https://www.vslcd.com/product-5040461810375675.html · https://www.vslcd.com/K002146-5.5inch-2560x1440-lcd-screen-without-backlight-H/D-driver-board.html · https://www.newegg.com/p/3C6-01ZY-00DW8

## Datasheet: Sharp LCY-1314302B

Sharp's LS055R1SX04 specification, Spec No. LCY-1314302B (first issue 2014-04-04, revision A 2014-05-09), uploaded by Dallas 2026-11-15. The PDF is not in this repo: it carries Sharp's copyright notice, the outline drawing is marked confidential, and the repo is public. Cited here by its own page numbers. Inches = mm / 25.4.

Table 1, p.5: active area 68.04 (H) x 120.96 (V) mm; 1440 x 2560; 1 pixel = R + G + B dots; pitch 0.01575 (H) x 0.04725 (V) mm; R, G, B vertical stripes; normally black; outline 70.94 (W) x 128.49 (H) x 1.35 (D) mm typ, "without some projections and FPC".

Construction, p.5: LCD panel, COG driver (R63419), FPC with components, white LEDs, prism sheet, diffuser, light guide, reflector, plastic frame and metal frame. The LCD panel is held by double-sided adhesive tape, which "do[es] not guarantee to permanently fix the panels".

Connector, pp. 5 and 10: JAE WP7B-P050VA1, 50 pins, 0.4 mm pitch, board to board; mates with WP7B-S050VA1. Backlight on pins 47 (LED1-), 48 (LED+), 49 (LED2-) (p.9).

Fig. 13 outline, p.31:

| Layer | W | L |
|---|---|---|
| Metal frame | 2.793 in (70.94 ± 0.15 mm) | 5.059 in (128.49 ± 0.15 mm) |
| TFT (bottom) glass | 2.757 in (70.04 ± 0.15 mm) | 5.023 in (127.59 ± 0.15 mm) |
| CF (top) glass | 2.757 in (70.04 ± 0.15 mm) | 4.907 in (124.65 ± 0.15 mm) |
| Front polarizer | 2.742 in (69.64 ± 0.15 mm) | 4.845 in (123.06 ± 0.15 mm) |
| Active area | 2.679 in (68.04 mm) | 4.762 in (120.96 mm) |

Also on Fig. 13: module thickness 0.0531 ± 0.0039 in (1.35 ± 0.10 mm). Active area to metal frame 0.057 in (1.45 ± 0.2 mm) on the long sides, (1.45) mm at the far end, 0.239 in (6.08 ± 0.2 mm) at the FPC end; check 1.45 + 120.96 + 6.08 = 128.49 mm and 1.45 + 68.04 + 1.45 = 70.94 mm. FPC 3.87 in (98.2 ± 0.5 mm) past the frame edge, laid flat; tail 0.354 in (9 mm) wide; bend radius over 0.5 mm (note 4); components under insulating tape, 0.7 mm high at most. A soldering area with insulating tape on the FPC at the FPC-end corner (inference: the LED pads, the "LE" tab in Z08). A protective-film pull tab and Ag paste at the FPC-end corner. Top polarizer surface is hard coat (note 8). General tolerance ±0.5 mm (note 3). Pixel callout at the top-left active-area corner, front view with the FPC end at the bottom: R G B R, left to right.

Notices, pp. 1 to 4: a protective film is on the panel surface as shipped; peel it slowly under anti-ESD control (ion blower, ground strap). Water droplets on the polarizer must be wiped off at once.

Derived from Fig. 13 (EST: assumes the frame overhangs the glass equally at both ends and the two glasses are flush at the far end):
- Ledge depth = 127.59 - 124.65 = 2.94 mm (0.116 in).
- Glass beyond the front polarizer on each long side = (70.04 - 69.64)/2 = 0.20 mm (0.008 in): likely too narrow for B there.
- Frame overhang per side = (70.94 - 70.04)/2 = 0.45 mm; per end, if equal = (128.49 - 127.59)/2 = 0.45 mm.
- Glass edge to active area: long sides (70.04 - 68.04)/2 = 1.00 mm (0.039 in); far end 1.45 - 0.45 = 1.00 mm; FPC end (bottom glass) 6.08 - 0.45 = 5.63 mm (0.222 in); check 1.00 + 120.96 + 5.63 = 127.59 mm. Top glass edge to active area at the FPC end = 124.65 - 120.96 - 1.00 = 2.69 mm (0.106 in).
- On the 4.5 x 6 in panel with the image centered (D-09): panel edge to image edge = (6.000 - 4.762)/2 = 0.619 in (15.72 mm), so frame edge to panel edge = 15.72 - 1.45 = 14.27 mm (0.562 in) at the far end and 15.72 - 6.08 = 9.64 mm (0.380 in) at the FPC end, where the FPC also leaves.

What the datasheet settles, pending the bench checks below: stripes (R, G, B vertical, R at the left edge seen from the front with the FPC end toward you); the panel's own connector (50 pins); p.78's 71 x 128 mm is the metal-frame outline rounded to the mm (70.94 and 128.49; inference), not a bezel opening; the listings' 1.45 mm is the datasheet's maximum (1.35 + 0.10). What it doesn't give: any glass or polarizer thickness, so t still needs the micrometer on panel 2.

## Measurements

Pending.
