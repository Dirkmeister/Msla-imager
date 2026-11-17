# L1: L1.11 C optic test: bench procedures, test board, rig

Package L1.11 of lane L1 (imager-09). Tests: T-UV-7 (optic 400 nm efficiency) and T-UV-6 (LED-to-optic height, beam, pointing), then C21 or C28 (imager-06 "C optic and array checks", calc §5 and §6c). This folder holds what the bench needs; the calc scripts and readings sit in `calcs/` (`l1_11_*`).

Rule for every step with a lit LED: the shroud is closed first. Read through the meter, never by eye in the beam (R9). The XL6009 check has no UV.

## 1. XL6009 bench check (no UV)

What it proves: the XL6009 module (B07XG323G8) holds 26.2 V at the C21 strings' 0.55 A from the 12 V brick for 10 min without running hot (calc §8). Readings go in `calcs/l1_11_xl6009.csv`; `python3 calcs/l1_11_xl6009.py` does the math and the pass rules.

On hand: XL6009 module, ALITOVE ALT-1205T brick, the two 24 Ω 50 W loads, Klein MM300 (one meter), Klein IR thermometer, leads.

```
 brick +12 ──(meter, 10 A jack, step 6 only)── IN+ ┌─────────┐ OUT+ ── 24 Ω ── 24 Ω ──┐
 brick GND ─────────────────────────────────── IN- │ XL6009  │ OUT- ──────────────────┘
                                                   └─────────┘
 loads screwed or clamped flat on metal; fingers off: 7.15 W each
```

1. **Cap.** Read the voltage printed on the output electrolytic (the OUT side). Pass: ≥ 35 V. → `cap_out_rating_V`.
2. **Load, cold.** Meter on 200 Ω: touch the probes together (`R_leads_ohm`), then the two loads in series (`R_load_cold_ohm`, about 48).
3. **Set point.** Brick on, no load. Meter on 200 V at OUT; trim the pot to read 26.2 (`V_out_noload_V`). Also note the brick alone on 20 V (`V_brick_noload_V`).
4. **Run.** Power off, connect the 48 Ω load (on metal), power on and start a timer. Meter stays in V mode; move the probes, not the wires:
   - 1 min: OUT on 200 V → `V_out_1min_V`. If it reads under 26.2, trim back to 26.2 now and log the trimmed value instead.
   - 2 min: IN terminals on 20 V → `V_in_2min_V`. 5 min OUT, 6 min IN, 10 min OUT and IN.
   - Watch for a dropout or the output clicking off → `dropout_or_hiccup`.
5. **Temperatures at 10 min.** IR thermometer close in, so the spot covers one part: XL6009 chip, diode, inductor, output cap, each load (the loads' shiny housing reads low: aim at a matte spot or a strip of masking tape). Room temperature at the bench. Pass: hottest module point ≤ 185 °F (85 °C) (EST, proposed).
6. **Input current.** Power off. Meter red lead to the 10 A jack, in series with IN+. Power on, read within 30 s while everything is still hot → `I_in_A`. Power off. Red lead back to the V jack before anything else.
7. Optional: the same in series with OUT+ → `I_out_A` (the script also gets it from V/R).

Expected (EST, calc §8): 0.546 A and 14.30 W out; about 1.40 A in at 12.0 V at 85 %. The meter's 10 A range is ±(3 % + 5 digits), so η comes out about ±0.07: good enough for the record, not a pass rule.

Pass (proposed; the lead confirms): cap ≥ 35 V; 26.2 V with no load; Vout at 10 min within 0.1 V of 1 min with no dropout; hottest module point ≤ 85 °C. A fail puts a CV boost on the buy list with the build optics.

## 2. Test board panel (`test_board/`)

One KiCad 7 file, three boards on one 2-sided 1.6 mm (0.063 in) 1 oz FR4 blank. Panel 86 x 125 mm (3.39 x 4.92 in). On a 4 x 5 in (101.6 x 127 mm) piece that leaves 0.31 in (7.8 mm) a side across but only 0.04 in (1 mm) a side along: (101.6 - 86)/2 and (127 - 125)/2. A 4 x 6 in (101.6 x 152.4 mm) piece leaves 0.54 in (13.7 mm) along for clamping; or cut the test board (86 x 80 mm) from one piece and the two small boards from another. Isolation-milled on the top only, 0.4 mm (15.7 mil) cuts; the bottom copper stays intact as a floating heat spreader. PCB milling on the 3018 isn't set up yet (Dallas, 2026-11-17): the Gerbers wait for it.

![F.Cu, drills and outlines](test_board/l1_11_panel_fcu.png)

- `l1_11_test_board.kicad_pcb` / `.kicad_pro`, footprints in `l1_11.pretty` (project `fp-lib-table`). Regenerate: `python3 light/l1_11/test_board/make_test_board.py` (KiCad 7 pcbnew). No schematic: the board is drawn directly; nets below.
- `gerber/`: F.Cu (isolate), Edge.Cuts (cut out), PTH drill (10 x 0.126 in (3.2 mm), all unplated on a milled board), F.SilkS and F.Fab for reference. B.Cu is empty on purpose: don't mill the bottom.
- `drc_report.txt`: 0 clearance, short or unconnected errors. Left: library warnings (this sandbox has no global footprint table; they clear in your KiCad) and a few silkscreen warnings (no silk on a milled board).

**A. Test board, 86 x 80 mm (3.39 x 3.15 in).** 9 CUN0LF1B at C21's pitch, 0.787 x 0.893 in (20.00 x 22.68 mm), footprint `LED_SMD:LED_PLCC_2835_Handsoldering` (KiCad 7's stock part matches the V1 board @ 8208f05 pad for pad: large pad 1 = K at -1.05 mm, pad 2 = A at +1.525 mm). The strings are the rows, anode on the left: `VIN_Rr | D | Rr_N1 | D | Rr_N2 | D | Rr_OUT`. Each cut runs through an LED's pad gap, so every inner cathode pad sits in a 0.77 x 0.88 in (19.6 x 22.3 mm) island (119.325 - 99.725 by 111.14 - 88.86 for the center LED): most of the copper stays (L1.12 reads FR4's per-LED θ from this board). NTC TH1 (1206) sits on two isolated islands 0.20 in (5 mm) right of the center LED, beside its cathode pad, with two wire pads. No ballasts on this board: their 1.1 W typ would bias L1.12's θ. Holes: 4 x M3 on the ATS's 53.00 mm (2.087 in) square centred on the center LED, 4 x M3 at the corners for the holder and stand; each has an isolated copper ring under the screw head, so a screw can't join two nets through the ATS.

**B. Control board, 60 x 40 mm, outside the shroud.** Brick +12 V in → three VIN wires. Each string's OUT wire → a link (JP1-3: solder bridge, or clip lead; open it and clip the meter's 200 mA range across to read that string's current; leave it open to switch the string off) → ballast R1-3 → GND. Ballast footprint takes either your 12 Ω ≥ 0.61 W axial laid flat (leads bent to the outer pads) or four 47 Ω 1206 in parallel (11.75 Ω): fit one. Detector load RL across DET A+/K- (1206 or axial, 100 kΩ to start) with meter pads; NTC wire and meter pads.

**C. Detector board, 22 x 36 mm.** The spare CUN0LF1B (D10) as the detector, A+ and K- wire pads, 2 x M3 to the detector carriage.

**Before soldering: polarity.** The footprint (and V1) say the large pad is the cathode; the CUN0LF1B DS drawing isn't readable as text. Two checks, neither powers an LED:
1. Phone macro photos, sent here: a spare from the cut tape, top and bottom; one LED on the populated V1 board with both pads in view (V1 put pad 1 = K on the large pad).
2. Daylight, optional: a spare with fine wires on its pads, 1 MΩ across them, meter on 200 mV, facing a window or outside. A positive reading means the red lead is on the anode.

If the large pad turns out to be the anode, nothing changes on the board: all nine face the same way, so swap the string wires (VIN on the right pads, OUT on the left). The NTC still sits by the large (thermal) pad.

**Assembly.** LEDs from the cut tape, all the same way round (large pad right as drawn). Mill, deburr, clean; paste and hot air or a hot plate, or an iron. TH1 on its two islands; two fine wires off its wire pads, flat on the board, out past the right edge (the holder gets a groove for them). Grease on the ATS, board centred on it, 4 x M3 through the ATS's corner holes (caliper them first, and the ATS base thickness, for the screw length); nuts between the fins.

| Wire | From | To |
|---|---|---|
| VIN1-3 | control V12 pads | test board VIN1-3 (left edge) |
| OUT1-3 | test board OUT1-3 (right edge) | control S1-S3 OUT pads |
| NTC x2 | TH1 wire pads | control NTC pads |
| DET x2 | detector A+, K- | control DET A+, K- |
| Brick | +12 and GND | control +12 IN, GND IN |

At the brick's 12.0 V each string runs 125-225 mA across the Vf bins, 175 mA typ, through 12 Ω; ballast 0.61 W max (calcs/l1_c_lead_checks.py section 6, EST). With 4 x 47 Ω (11.75 Ω) the top bin reaches (12.0 - 3 x 3.1)/11.75 = 230 mA, still under the DS's 250 mA.
