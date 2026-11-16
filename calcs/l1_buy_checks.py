# L1: L1.3 light-engine buy checks. (1) Fresnel candidates against imager-05's spec and calc §6: corner/center, dimmest-point light vs f = 10 in, cluster half-angle and smear at t = 0.725 mm (basis) and 0.326 mm (L2.1 EST), reflector exit cap, groove blur at the LCD gap (EST); (2) XL6009 at 3 strings, 26.2 V, from 12 V and 11.75 V against the XLSEMI datasheet Rev 1.1. Run: python3 calcs/l1_buy_checks.py (stdlib only)
"""
Sources
  Image 2560 x 1440 at 47.25 um = 120.96 x 68.04 mm (calc §2). Cluster A r = 11.19 mm (calc §6).
  n = 1.5, 2.5 mil budget, t 0.725 mm basis and 0.3258 mm EST (calc §5 and its HQ note).
  Fresnel spec (imager-05 v0.6): f 9.05-12 in, clear >= 5.6 in circle or >= 4.9 x 2.8 in centered.
  Hedge (R6): near f 6.28 in, where corner/center = 0.707 (calc §6).
  Candidates: Edmund Optics product pages and its 2021 catalog table (EFL, effective size,
  grooves per inch); Knight Optical stock table (LFG254152: 254 mm, 152 mm dia, facet 1.0 mm).
  LCD gap under the lens 0.4 in (10 mm) is imager-05's EST (judgment; L1.5 sets it).
  XL6009 (XLSEMI DS Rev 1.1): 5-32 V in, Fosc 320/400/480 kHz, switch current limit 4 A,
  Rds(on) 110/120 mOhm at 12 V and 4 A, Dmax 90 %, RthJA 30 C/W (TO263-5L, no heatsink).
  Load: sinks at VBE 0.729 V / 3.9 Ohm max (calc §9), 3 strings, 26.2 V (calc §8), eta 85 % EST.
"""
import math

MM = 25.4
W_MM, H_MM = 120.96, 68.04
R_CORNER = math.hypot(W_MM / 2, H_MM / 2)        # mm, image corner radius
R_SRC = 11.19                                     # mm, cluster A radius incl. package
N = 1.5
BUDGET = 2.5 * MM / 1000                          # mm (2.5 mil)
T_BASIS, T_EST = 0.725, 0.3258                    # mm
GAP = 0.4 * MM                                    # mm, lens to LCD (EST)


def alpha_max(t):
    return math.degrees(math.asin(N * math.sin(math.atan(BUDGET / t))))


def smear_mil(alpha_deg, t):
    inner = math.asin(math.sin(math.radians(alpha_deg)) / N)
    return t * math.tan(inner) / MM * 1000


def ratio(f):
    return math.cos(math.atan(R_CORNER / f)) ** 4


def gain_vs_254(f):
    return (254.0 / f) ** 2 * ratio(f) / ratio(254.0)


def verdict(r):
    if r >= 0.84:
        return "pass >= 0.84"
    if r >= 0.707:
        return "relaxed only (>= 0.707, S-1 window >= 3 fine steps or masking)"
    return "fail (< 0.707)"


print("== Inputs")
print(f"corner r = hypot({W_MM/2:.2f}, {H_MM/2:.2f}) = {R_CORNER:.2f} mm ({R_CORNER/MM:.3f} in)")
a_b, a_e = alpha_max(T_BASIS), alpha_max(T_EST)
print(f"alpha_max = {a_b:.2f} deg at t {T_BASIS} mm; {a_e:.1f} deg at t {T_EST} mm (EST)")
print(f"ratio(254 mm) = cos^4(atan({R_CORNER:.2f}/254)) = {ratio(254.0):.4f}")
f_hedge = R_CORNER / math.tan(math.acos(0.707 ** 0.25))
print(f"f where corner/center = 0.707: {f_hedge:.1f} mm ({f_hedge/MM:.2f} in)")

# name, f mm, clear aperture (text), grooves per mm pitch (mm), role, aperture ok
cands = [
    ("Edmund #32-685 6.7x6.7 in, 10 in FL", 254.00, "6.0 in dia", 25.4 / 100, "main", 6.0 >= 5.6),
    ("Knight LFG254152 170x170 mm, 254 FL", 254.00, "152 mm dia (5.98 in)", 1.0, "main", 152 / MM >= 5.6),
    ("Edmund #32-598 11x11 in, 9.2 in FL", 233.68, "10.5 x 10.5 in", 25.4 / 50, "main, cut to fit", True),
    ("Edmund #32-686 6.7x6.7 in, 12 in FL", 304.80, "6.0 in dia", 25.4 / 50, "main, edge of range", True),
    ("Edmund #32-687 11x11 in, 7 in FL", 177.80, "10.5 x 10.5 in", 25.4 / 50, "hedge, cut to fit", True),
    ("Edmund #32-597 11x11 in, 8.2 in FL", 208.28, "10.5 x 10.5 in", 25.4 / 50, "hedge, cut to fit", True),
    ("Edmund #32-594 6.7x6.7 in, 6 in FL", 152.40, "6.0 in dia", 25.4 / 125, "hedge?", True),
    ("Edmund #43-013 5.5x5.5 in, 10 in FL", 254.00, "5.0 in eff", 25.4 / 100, "main?", False),
    ("Budget PMMA 240x240 mm, 250 FL (eBay)", 250.00, "240 mm square", 0.3, "main, budget, cut to fit; pitch EST", True),
]

print("\n== Fresnel candidates")
for name, f, ap, pitch, role, ap_ok in cands:
    f_in = f / MM
    in_range = 9.05 <= round(f_in, 3) <= 12.0      # round: 304.80 mm is 12.000 in
    r = ratio(f)
    g = gain_vs_254(f)
    a = math.degrees(math.atan(R_SRC / f))
    s_b, s_e = smear_mil(a, T_BASIS), smear_mil(a, T_EST)
    refl_cap = min(f * math.tan(math.radians(a_b)), 42.5)
    blur = 2 * GAP * math.tan(math.radians(a))
    print(f"{name} [{role}]")
    print(f"  f {f:.2f} mm = {f_in:.2f} in; main range 9.05-12 in: {'yes' if in_range else 'no'}; aperture {ap}: {'ok' if ap_ok else 'FAILS spec'}")
    print(f"  corner/center cos^4(atan({R_CORNER:.2f}/{f:.2f})) = {r:.3f} -> {verdict(r)}")
    print(f"  dimmest-point light vs f 254: (254/{f:.2f})^2 x {r:.4f}/{ratio(254.0):.4f} = {g:.2f}x")
    print(f"  cluster half-angle atan({R_SRC}/{f:.2f}) = {a:.2f} deg; smear {s_b:.2f} mil at 0.725 mm, {s_e:.2f} mil at 0.326 mm (EST)")
    print(f"  reflector exit cap = {f:.2f} x tan {a_b:.2f} deg = {refl_cap:.1f} mm")
    print(f"  groove blur at the LCD (EST): 2 x {GAP:.2f} x tan {a:.2f} deg = {blur:.3f} mm over pitch {pitch:.3f} mm = {blur/pitch:.2f} grooves")

print("\n== XL6009, 3 strings at 26.2 V")
i_str = 0.729 / 3.9
i_out = 3 * i_str
v_out, eta, v_d = 26.2, 0.85, 0.5           # v_d: Schottky drop, EST
p_out = v_out * i_out
p_in = p_out / eta
print(f"string max = 0.729/3.9 = {i_str*1000:.1f} mA; 3 strings = {i_out:.4f} A")
print(f"P_out = {v_out} x {i_out:.4f} = {p_out:.2f} W; P_in at {eta:.0%} (EST) = {p_in:.2f} W")
for v_in in (12.0, 11.75):
    i_in = p_in / v_in
    d = 1 - v_in / (v_out + v_d)
    print(f"Vin {v_in} V: I_in = {p_in:.2f}/{v_in} = {i_in:.3f} A; D = 1 - {v_in}/({v_out}+{v_d}) = {d:.3f} (Dmax 0.90)")
    for l_uh in (10, 22, 33, 47, 68):
        di = v_in * d / (l_uh * 1e-6 * 320e3)
        pk = i_in + di / 2
        print(f"  L {l_uh:>2} uH at 320 kHz: dI = {v_in}x{d:.3f}/({l_uh}u x 320k) = {di:.3f} A; peak {pk:.2f} A = {pk/4:.0%} of the 4 A limit")
    p_sw = i_in ** 2 * d * 0.120
    print(f"  switch conduction (EST, no ripple or switching loss): {i_in:.3f}^2 x {d:.3f} x 0.120 = {p_sw:.3f} W -> +{p_sw*30:.1f} C at 30 C/W")

print("\n== D-12 C with off-the-shelf 20 mm PMMA TIR collimators (EST; options for Dallas, 2026-11-16)")
# Beam full angle is the optic's FWHM rating; half-angle taken as half of it (EST: tails ignored,
# and a 3528 package may widen the beam vs the 1-3 W star LEDs these optics are rated on).
PITCH = 20.0                                     # mm, 20 mm optics touching
for full in (5, 15, 25):
    half = full / 2
    s_b, s_e = smear_mil(half, T_BASIS), smear_mil(half, T_EST)
    gap = PITCH / (2 * math.tan(math.radians(half)))   # calc §6c: one cell of overlap
    ok_b = "ok" if s_b <= 2.5 else "over"
    ok_e = "ok" if s_e <= 2.5 else "over"
    print(f"{full:>2} deg beam: smear {s_b:.2f} mil at 0.725 mm ({ok_b}), {s_e:.2f} mil at 0.326 mm ({ok_e}); "
          f"one-cell overlap gap {PITCH}/(2 tan {half} deg) = {gap:.1f} mm ({gap/MM:.2f} in)")
print(f"round optics touching in a square grid fill pi/4 = {math.pi/4:.3f} of the area: the corners need overlap")
area = (7 * PITCH) * (3 * H_MM / 3) / 100          # cm^2: 7 columns at 20 mm by the 68.04 mm image height
a_mean = 21 * 0.210 * 1000 * 0.0387 / (W_MM * H_MM / 100) * 0.85   # A's mean after an 85 % Fresnel
print(f"A mean after the Fresnel: 21 x 210 mW x 3.87 % / {W_MM*H_MM/100:.2f} cm^2 x 0.85 = {a_mean:.2f} mW/cm^2")
for eta in (0.5, 0.8):
    c_mean = 21 * 0.210 * 1000 * eta / area
    print(f"C, 3 x 7 at 20 mm, capture {eta:.0%} (EST): 21 x 210 mW x {eta} / {area:.2f} cm^2 = {c_mean:.1f} mW/cm^2 = {c_mean/a_mean:.0f}x A")
