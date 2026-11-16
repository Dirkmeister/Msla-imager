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

## Measurements

Pending.
