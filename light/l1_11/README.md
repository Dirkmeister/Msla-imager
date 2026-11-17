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
