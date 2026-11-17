# L1: L1.11 XL6009 bench check (no UV): 26.2 V into 48 ohm for 10 min, from calcs/l1_11_xl6009.csv. Run: python3 calcs/l1_11_xl6009.py (stdlib only)
"""
L1.11 step "XL6009 bench check" (imager-09 L1.11; imager-04 §8).

Readings go in calcs/l1_11_xl6009.csv (blank = not read yet). Procedure: light/l1_11/README.md, section 1.
One meter (Klein MM300), so V and A are read in turn, not together.

Meter accuracy, MM300 manual as extracted (verify against the printed manual):
  DC V   20.00 V range: 0.01 V steps, +-(0.5 % + 3 digits); 200.0 V range: 0.1 V steps, +-(0.8 % + 3 digits)
  DC A   10.00 A range: 0.01 A steps, +-(3.0 % + 5 digits)
  Ohms   200.0 ohm range: 0.1 ohm steps, +-(1.0 % + 5 digits)
Design point (calc §8, EST): 26.2 V out, 48 ohm (two 24 ohm 50 W in series) -> 0.5458 A, 14.30 W; at 85 % EST,
16.82 W in, 1.40 A at 12.0 V. XL6009 DS (XLSEMI): operating Tj -40 to 125 C, thermal shutdown built in.
Pass rules (proposed by L1.11; the lead confirms):
  1. output capacitor marked >= 35 V
  2. reaches 26.2 V with no load
  3. under the 48 ohm load: Vout at 10 min within 1 count (0.1 V) of Vout at 1 min, no dropout or hiccup
  4. hottest point on the module <= 85 C by IR after 10 min at room temperature (EST: leaves room for the
     enclosure's 35 C ambient and the junction-to-case rise under the DS's 125 C)
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "l1_11_xl6009.csv")

V_SET, R_NOM, ETA_EST = 26.2, 48.0, 0.85


def acc(value, pct, digits, step):
    """meter accuracy band: +-(pct % of reading + digits x step)"""
    return abs(value) * pct / 100 + digits * step


def load():
    rows = {}
    with open(CSV, newline="") as f:
        for r in csv.DictReader(f):
            v = r["value"].strip()
            if v == "":
                rows[r["key"]] = None
            else:
                try:
                    rows[r["key"]] = float(v)
                except ValueError:
                    rows[r["key"]] = v
    return rows


def show(label, x, unit, fmt="{:.3f}"):
    print(f"  {label}: " + ("TBD" if x is None else fmt.format(x) + f" {unit}"))


r = load()
print("== Expected (EST, calc §8)")
i_nom = V_SET / R_NOM
p_nom = V_SET * i_nom
print(f"  I_out = {V_SET} / {R_NOM} = {i_nom:.4f} A; P_out = {V_SET} x {i_nom:.4f} = {p_nom:.2f} W; "
      f"{p_nom/2:.2f} W per 24 ohm load")
print(f"  at eta {ETA_EST}: P_in = {p_nom:.2f} / {ETA_EST} = {p_nom/ETA_EST:.2f} W; I_in = {p_nom/ETA_EST:.2f} / 12.0 = "
      f"{p_nom/ETA_EST/12.0:.3f} A ({p_nom/ETA_EST/11.75:.3f} A at 11.75 V); module loss {p_nom/ETA_EST - p_nom:.2f} W")

print("\n== Readings")
for k in ("cap_out_rating_V", "V_brick_noload_V", "V_out_noload_V", "R_leads_ohm", "R_load_cold_ohm",
          "V_out_1min_V", "V_in_2min_V", "V_out_5min_V", "V_in_6min_V", "V_out_10min_V", "V_in_10min_V",
          "I_in_A", "I_out_A", "T_room_C", "T_ic_C", "T_diode_C", "T_inductor_C", "T_capout_C", "T_load1_C",
          "T_load2_C"):
    show(k, r.get(k), "", "{}")
print(f"  dropout_or_hiccup: {r.get('dropout_or_hiccup') or 'TBD'}")

print("\n== Derived")
R = None
if r.get("R_load_cold_ohm") is not None:
    R = r["R_load_cold_ohm"] - (r.get("R_leads_ohm") or 0.0)
    dR = acc(r["R_load_cold_ohm"], 1.0, 5, 0.1)
    print(f"  R_load = {r['R_load_cold_ohm']} - {r.get('R_leads_ohm') or 0.0} (leads) = {R:.1f} ohm "
          f"+-{dR:.2f} ohm (meter); cold value, hot R not measured (EST: within about 1 %)")
vout = r.get("V_out_10min_V")
vin = r.get("V_in_10min_V")
iin = r.get("I_in_A")
pout = pin = None
if vout is not None and R:
    iout = vout / R
    pout = vout * iout
    rel = math.sqrt((2 * acc(vout, 0.8, 3, 0.1) / vout) ** 2 + (dR / R) ** 2)
    print(f"  I_out = V_out / R = {vout} / {R:.1f} = {iout:.4f} A")
    print(f"  P_out = V_out^2 / R = {vout}^2 / {R:.1f} = {pout:.2f} W +-{rel:.1%} (2 x V_out's band and R's band, RSS)")
    if r.get("I_out_A") is not None:
        print(f"  I_out read on 10 A: {r['I_out_A']} A +-{acc(r['I_out_A'], 3.0, 5, 0.01):.3f} A, "
              f"against {iout:.4f} A from V/R")
if vin is not None and iin is not None:
    pin = vin * iin
    rel_in = math.sqrt((acc(vin, 0.5, 3, 0.01) / vin) ** 2 + (acc(iin, 3.0, 5, 0.01) / iin) ** 2)
    print(f"  P_in = V_in x I_in = {vin} x {iin} = {pin:.2f} W +-{rel_in:.1%} (RSS; the 10 A range dominates)")
if pin and pout:
    eta = pout / pin
    rel_eta = math.sqrt(rel ** 2 + rel_in ** 2)
    print(f"  eta = P_out / P_in = {pout:.2f} / {pin:.2f} = {eta:.3f} +-{eta*rel_eta:.3f} "
          f"(calc §8 assumed {ETA_EST}); module loss {pin - pout:.2f} W")

print("\n== Pass rules (proposed)")
res = []
cap = r.get("cap_out_rating_V")
res.append(("1 output cap >= 35 V", None if cap is None else cap >= 35, f"{cap} V"))
vnl = r.get("V_out_noload_V")
res.append(("2 26.2 V with no load", None if vnl is None else abs(vnl - V_SET) <= 0.05, f"{vnl} V"))
v1, v10 = r.get("V_out_1min_V"), r.get("V_out_10min_V")
dh = r.get("dropout_or_hiccup")
ok3 = None
if v1 is not None and v10 is not None and dh is not None:
    ok3 = abs(v10 - v1) <= 0.1 + 1e-9 and str(dh).lower() in ("no", "n", "0")
res.append(("3 holds under 48 ohm, 10 min", ok3, f"{v1} -> {v10} V, dropout {dh}"))
temps = [r.get(k) for k in ("T_ic_C", "T_diode_C", "T_inductor_C", "T_capout_C")]
tmax = max([t for t in temps if t is not None], default=None)
res.append(("4 hottest module point <= 85 C (EST)", None if tmax is None else tmax <= 85, f"{tmax} C"))
for name, ok, val in res:
    print(f"  {name}: {'TBD' if ok is None else ('PASS' if ok else 'FAIL')} ({val})")
if all(ok is True for _, ok, _ in res):
    print("XL6009: PASS")
elif any(ok is False for _, ok, _ in res):
    print("XL6009: FAIL -> a CV boost goes on the buy list with the build optics (imager-09 L1.11)")
else:
    print("XL6009: incomplete")
