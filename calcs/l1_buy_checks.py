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
    ("Generic PMMA 240x240 mm, 250 FL (eBay; Amazon B0BC8BFPWF)", 250.00, "240 mm square", None, "main, budget, cut to fit", True),
    ("Six Seasons 2-pack dia 250 mm, 240 FL (Amazon B07BJLFPDJ)", 240.00, "250 mm dia", 0.5, "main, budget", True),
    ("Six Seasons 2-pack dia 250 mm, 260 FL (Amazon B07BJLFPDJ)", 260.00, "250 mm dia", 0.5, "main, budget", True),
    ("Six Seasons 2-pack dia 250 mm, 290 FL (Amazon B07BJLFPDJ)", 290.00, "250 mm dia", 0.5, "main, budget", True),
    ("Six Seasons 300x300 mm, 300 FL (Amazon B0CL3CRN55)", 300.00, "300 mm square", None, "main, budget, cut to fit", True),
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
    r_lo = ratio(0.95 * f)      # EST tolerance: Knight's standard range is +-5 %; budget lenses state none
    print(f"{name} [{role}]")
    print(f"  f {f:.2f} mm = {f_in:.2f} in; main range 9.05-12 in: {'yes' if in_range else 'no'}; aperture {ap}: {'ok' if ap_ok else 'FAILS spec'}")
    print(f"  corner/center cos^4(atan({R_CORNER:.2f}/{f:.2f})) = {r:.3f} -> {verdict(r)}")
    print(f"  dimmest-point light vs f 254: (254/{f:.2f})^2 x {r:.4f}/{ratio(254.0):.4f} = {g:.2f}x")
    print(f"  cluster half-angle atan({R_SRC}/{f:.2f}) = {a:.2f} deg; smear {s_b:.2f} mil at 0.725 mm, {s_e:.2f} mil at 0.326 mm (EST)")
    print(f"  reflector exit cap = {f:.2f} x tan {a_b:.2f} deg = {refl_cap:.1f} mm")
    print(f"  at f -5 % (EST tolerance): {0.95*f:.1f} mm -> corner/center {r_lo:.3f} ({verdict(r_lo)})")
    if pitch is None:
        print(f"  groove blur at the LCD (EST): {blur:.3f} mm; pitch not stated by the seller")
    else:
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
PITCH = 20.0                                     # mm, 20 mm optics touching (7 columns)
ROW = H_MM / 3                                   # mm, 3 rows over the image height: 22.68 mm
P_GOV = max(PITCH, ROW)                          # the larger pitch sets the overlap (fixed 2026-11-16:
                                                 # the first run used the 20 mm column pitch only)
for full in (5, 15, 25):
    half = full / 2
    s_b, s_e = smear_mil(half, T_BASIS), smear_mil(half, T_EST)
    gap = P_GOV / (2 * math.tan(math.radians(half)))   # calc §6c: one cell of overlap
    ok_b = "ok" if s_b <= 2.5 else "over"
    ok_e = "ok" if s_e <= 2.5 else "over"
    print(f"{full:>2} deg beam: smear {s_b:.2f} mil at 0.725 mm ({ok_b}), {s_e:.2f} mil at 0.326 mm ({ok_e}); "
          f"one-cell overlap gap {P_GOV:.2f}/(2 tan {half} deg) = {gap:.1f} mm ({gap/MM:.2f} in)")
print(f"round optics touching in a square grid fill pi/4 = {math.pi/4:.3f} of the area: the corners need overlap")
area = (7 * PITCH) * (3 * H_MM / 3) / 100          # cm^2: 7 columns at 20 mm by the 68.04 mm image height
a_mean = 21 * 0.210 * 1000 * 0.0387 / (W_MM * H_MM / 100) * 0.85   # A's mean after an 85 % Fresnel
print(f"A mean after the Fresnel: 21 x 210 mW x 3.87 % / {W_MM*H_MM/100:.2f} cm^2 x 0.85 = {a_mean:.2f} mW/cm^2")
for eta in (0.5, 0.8):
    c_mean = 21 * 0.210 * 1000 * eta / area
    print(f"C, 3 x 7 at 20 mm, capture {eta:.0%} (EST): 21 x 210 mW x {eta} / {area:.2f} cm^2 = {c_mean:.1f} mW/cm^2 = {c_mean/a_mean:.0f}x A")

# ---------------------------------------------------------------------------
print("\n== Why A can't just be short (same lens, same cluster, shorter f)")
# Both of A's numbers come from f: half-angle atan(r/f) sets smear, cos^4(atan(corner/f)) sets uniformity.
for f in (254.0, 152.4, 101.6):
    a = math.degrees(math.atan(R_SRC / f))
    print(f"f {f/MM:.1f} in: corner/center {ratio(f):.3f} ({verdict(ratio(f))}); half-angle {a:.2f} deg, "
          f"smear {smear_mil(a, T_BASIS):.2f} mil at 0.725 mm; dimmest-point light {gain_vs_254(f):.2f}x f 10 in")

# ---------------------------------------------------------------------------
print("\n== Folded A: one 45 deg first-surface mirror under the Fresnel (for Dallas, 2026-11-16)")
# The LED face sits P = 0.975 f_vis from the Fresnel along the path (405 nm focus, EST, imager-05).
# A 45 deg mirror under the Fresnel turns most of P sideways. The 4.9 x 2.8 in clear area (imager-05)
# runs its 2.8 in side along the fold, since the mirror's height scales with that side.
# Unfolded about the mirror, a ray from source point x_s to Fresnel point x_c sits at
# x_s (1 - s/P) + x_c s/P after a path s. Mirror: u = z - z_m = x - x_m, centered on the beam axis;
# L_h = source to mirror center, L_v = mirror center up to the Fresnel. For a source of radius r_e:
#   q = (a - r_e)/P; top hit u_top = (r_e + q L_h)/(1 - q); bottom hit u_bot = -(r_e + q L_h)/(1 + q)
#   the Fresnel clears the mirror's top edge by CLR: L_v = u_top + CLR and L_h + L_v = P
#   -> L_h = (P - CLR)(1 - q) - r_e
F_VIS = 260.0                     # mm, B07BJLFPDJ 260 mm option
P = 0.975 * F_VIS                 # mm (EST)
A_HALF = 2.8 * MM / 2             # mm, clear-area half-width along the fold
B_HALF = 4.9 * MM / 2             # mm, clear-area half-length across the fold
CLR = 0.2 * MM                    # mm, mirror top edge to Fresnel underside (EST: frame lip)
# EST stack items, the same for every configuration below (in):
BASE, HOLDER, T_FRES, T_LCD, T_COVER = 0.12, 0.12, 0.08, 0.12, 0.12   # T_COVER: LCD frame/top plate
SINK, WALL, LIP = 1.25, 0.12, 0.20     # LED board + heatsink behind the LED face; wall; Fresnel frame lip
WIDTH = 6.0 + 2 * WALL                 # in: the 6 in side of the 4.5 x 6 in panel (D-09) across the box
TOP = (T_FRES + GAP / MM + T_LCD + T_COVER)   # in, Fresnel underside to the top of the cover


def fold(r_e):
    q = (A_HALF - r_e) / P
    l_h = (P - CLR) * (1 - q) - r_e
    k = r_e + q * l_h
    u_top, u_bot = k / (1 - q), -k / (1 + q)
    l_v = u_top + CLR
    return q, l_h, l_v, u_top, u_bot


def y_env(r_e, s):
    return r_e * (1 - s / P) + B_HALF * s / P


print(f"P = 0.975 x {F_VIS:.0f} = {P:.1f} mm ({P/MM:.2f} in); clear area 4.9 x 2.8 in, 2.8 in side along the fold")
for label, r_e in (("bare cluster A", R_SRC), ("A + calc 6b reflector, 25 mm exit", 25.0)):
    q, l_h, l_v, u_top, u_bot = fold(r_e)
    vert = u_top - u_bot
    w_top = 2 * y_env(r_e, l_h + u_top)
    w_bot = 2 * y_env(r_e, l_h + u_bot)
    h_in = BASE + HOLDER + (-u_bot + l_v) / MM + TOP
    l_in = WALL + SINK + (l_h + A_HALF) / MM + LIP + WALL
    a = math.degrees(math.atan(r_e / P))
    print(f"{label} (r_e {r_e} mm): q = ({A_HALF:.2f} - {r_e})/{P:.1f} = {q:.4f}")
    print(f"  L_h = ({P:.1f} - {CLR:.2f})(1 - {q:.4f}) - {r_e} = {l_h:.1f} mm ({l_h/MM:.2f} in); "
          f"L_v = {u_top:.2f} + {CLR:.2f} = {l_v:.1f} mm ({l_v/MM:.2f} in)")
    print(f"  mirror hits u = +{u_top:.2f} / {u_bot:.2f} mm: {vert:.1f} mm tall ({vert/MM:.2f} in), "
          f"{vert*math.sqrt(2):.1f} mm along the face ({vert*math.sqrt(2)/MM:.2f} in); "
          f"width {w_top:.1f} mm at the top end ({w_top/MM:.2f} in), {w_bot:.1f} mm at the bottom ({w_bot/MM:.2f} in)")
    print(f"  4 x 6 in mirror (4 in along the face, 6 in across): {'fits' if vert*math.sqrt(2) <= 4*MM and w_top <= 6*MM else 'SHORT'} "
          f"({4*MM - vert*math.sqrt(2):.1f} and {6*MM - w_top:.1f} mm spare)")
    print(f"  height = {BASE} + {HOLDER} + ({-u_bot:.2f} + {l_v:.2f})/25.4 + {TOP:.2f} = {h_in:.2f} in ({h_in*MM:.0f} mm)")
    print(f"  length = {WALL} + {SINK} + ({l_h:.1f} + {A_HALF:.2f})/25.4 + {LIP} + {WALL} = {l_in:.2f} in; width {WIDTH:.2f} in (EST)")
    print(f"  half-angle atan({r_e}/{P:.1f}) = {a:.2f} deg: smear {smear_mil(a, T_BASIS):.2f} mil at 0.725 mm, "
          f"{smear_mil(a, T_EST):.2f} at 0.326 mm (unchanged by a flat mirror)")
    if r_e == R_SRC:
        L_H_A, L_V_A, U_TOP_A, U_BOT_A = l_h, l_v, u_top, u_bot

d = math.radians(1.0)
tilt = math.degrees(math.atan(2 * d * L_H_A / P))
print(f"mirror 1 deg off 45: virtual source moves 2 x 1 deg x {L_H_A:.1f} = {2*d*L_H_A:.2f} mm -> beam tilt "
      f"atan({2*d*L_H_A:.2f}/{P:.1f}) = {tilt:.2f} deg -> uniform shift {smear_mil(tilt, T_BASIS):.2f} mil at 0.725 mm, "
      f"{smear_mil(tilt, T_EST):.2f} at 0.326 mm (a shift, not blur)")
for r_m in (0.85, 0.92):   # EST: aluminum at 400 nm; T-UV-7's spare-CUN method measures the real mirror
    print(f"mirror R {r_m} (EST): A mean 1.76 -> {1.76*r_m:.2f} mW/cm^2")

print("\n== Same EST stack items, three configurations (in)")
tower = BASE + SINK + P / MM + TOP
print(f"A tower: {BASE} + {SINK} + {P/MM:.2f} + {TOP:.2f} = {tower:.2f} tall, footprint {WIDTH:.2f} x {4.5+2*WALL:.2f} (panel-limited, lens trimmed)")
q, l_h, l_v, u_top, u_bot = fold(R_SRC)
h_fold = BASE + HOLDER + (-u_bot + l_v) / MM + TOP
l_fold = WALL + SINK + (l_h + A_HALF) / MM + LIP + WALL
print(f"A folded: {h_fold:.2f} tall, {l_fold:.2f} x {WIDTH:.2f}")
gap15 = P_GOV / (2 * math.tan(math.radians(7.5))) / MM
PLATE, BOARD, OPTIC = 0.25, 1.6 / MM, 0.45      # EST: C's spread heat on a plate; 20 mm TIR optic height TBD
c_h = BASE + PLATE + BOARD + OPTIC + gap15 + T_LCD + T_COVER
print(f"C (3 x 7, 20 mm TIR, 15 deg): {BASE} + {PLATE} + {BOARD:.2f} + {OPTIC} + {gap15:.2f} + {T_LCD} + {T_COVER} = {c_h:.2f} tall, "
      f"{WIDTH:.2f} x {4.5+2*WALL:.2f}")
gap6c = 65.4 / MM
c6_h = BASE + PLATE + BOARD + 17 / MM + 0.2 + gap6c + T_LCD + T_COVER   # calc 6c: f 17 mm, lens 0.2 in (EST)
print(f"C (calc 6c, 4 x 7, 17 mm singlets, 7.52 deg): ... + 17 mm + 0.2 + {gap6c:.2f} + ... = {c6_h:.2f} tall")

print("\n== Fold mirror candidates: Amazon first-surface glass (DIY-projector type), sizes from the listings")
# Need (bare cluster / reflector): along the 45 deg face and across. The top edge sits at u_top;
# any extra length hangs below the beam and lowers the floor (box gets taller) unless cut.
q, l_h, l_v, u_top, u_bot = fold(R_SRC)
need_face, need_across = (u_top - u_bot) * math.sqrt(2), 2 * y_env(R_SRC, l_h + u_top)
qr, l_hr, l_vr, u_topr, u_botr = fold(25.0)
need_face_r, need_across_r = (u_topr - u_botr) * math.sqrt(2), 2 * y_env(25.0, l_hr + u_topr)
print(f"need {need_face:.1f} along x {need_across:.1f} across mm (bare); {need_face_r:.1f} x {need_across_r:.1f} (25 mm reflector)")
for name, face, across in (("HHDLMTOYS B0F8HZ5NGR / AMNOUR B0CZNLWWZW, 156 x 102 x 2 mm", 102, 156),
                           ("HHDLMTOYS B0F8H75D4L, 160 x 115 x 3 mm option", 115, 160),
                           ("HHDLMTOYS B0F8H75D4L, 122 x 106 x 3 mm option", 106, 122),
                           ("RUEHALF B0GW4WT69F, 100 x 100 x 3 mm", 100, 100),
                           ("AMNOUR B0CZNLWWZW, 128 x 80 x 2 mm option", 80, 128)):
    best = None
    for f_, a_ in ((face, across), (across, face)):          # try both orientations
        if f_ >= need_face and a_ >= need_across:
            if best is None or f_ < best[0]:
                best = (f_, a_)
    if best is None:
        print(f"{name}: SHORT (no orientation covers {need_face:.1f} x {need_across:.1f})")
        continue
    f_, a_ = best
    drop = f_ / math.sqrt(2) - (u_top - u_bot)               # mm of extra glass below the beam, vertical
    h_uncut = BASE + HOLDER + (f_ / math.sqrt(2) - u_top + l_v) / MM + TOP
    ok_r = f_ >= need_face_r and a_ >= need_across_r
    print(f"{name}: fits with {f_} mm along the face; uncut it hangs {drop:.1f} mm lower -> height "
          f"{BASE} + {HOLDER} + ({f_}/sqrt2 - {u_top:.2f} + {l_v:.2f})/25.4 + {TOP:.2f} = {h_uncut:.2f} in; "
          f"reflector variant {'fits' if ok_r else 'SHORT'}")
    w_box = max(WIDTH, (a_ + 2.0) / MM + 2 * WALL)          # 1 mm side clearance for the uncut mirror
    print(f"  box width max({WIDTH:.2f}, ({a_} + 2)/25.4 + 2 x {WALL}) = {w_box:.2f} in")
print(f"corner/center at the LED-to-Fresnel distance: cos^4(atan({R_CORNER:.2f}/{P:.1f})) = {ratio(P):.3f}")

print("\n== C design map (D-12 = C, Dallas 2026-11-16): one-cell overlap gap and stack, same EST items as above")
# C21: 7 x 3 at 20 mm (columns) by 22.68 mm (rows), 20 mm TIR optics, 3 strings of 7 (XL6009 plan as is).
# C28: calc 6c's 4 x 7 at 17.28 x 17.01 mm, singlets f 17 mm (lens 0.2 in thick, EST), 4 strings (T-PWR-1).
for name, pitch, full, opt_h in (("C21, 20 mm TIR 15 deg", ROW, 15.0, OPTIC),
                                 ("C21, 20 mm TIR 25 deg", ROW, 25.0, OPTIC),
                                 ("C28, 17 mm lens at 7.52 deg", 120.96 / 7, 2 * 7.52, 17 / MM + 0.2)):
    half = full / 2
    gap = pitch / (2 * math.tan(math.radians(half)))
    st = BASE + PLATE + BOARD + opt_h + gap / MM + T_LCD + T_COVER
    s_b, s_e = smear_mil(half, T_BASIS), smear_mil(half, T_EST)
    print(f"{name}: smear {s_b:.2f} mil at 0.725 mm ({'ok' if s_b <= 2.5 else 'over'}), {s_e:.2f} at 0.326 mm; "
          f"gap {pitch:.2f}/(2 tan {half:.2f}) = {gap:.1f} mm ({gap/MM:.2f} in); stack {BASE} + {PLATE} + {BOARD:.2f} + "
          f"{opt_h:.2f} + {gap/MM:.2f} + {T_LCD} + {T_COVER} = {st:.2f} in")
for n in (21, 28):
    print(f"{n} LEDs electrical at typ: {n} x 3.3 V x 0.18 A = {n*3.3*0.18:.2f} W")

print("\n== Fusion Optix 20XPS 25 deg out of stock (Dallas, 2026-11-16): is the in-family 30 deg a substitute?")
for full in (25.0, 30.0):
    half = full / 2
    gap = ROW / (2 * math.tan(math.radians(half)))
    print(f"{full:.0f} deg FWHM: smear {smear_mil(half, T_BASIS):.2f} mil at 0.725 mm, {smear_mil(half, T_EST):.2f} at 0.326 mm "
          f"(margin {1 - smear_mil(half, T_EST)/2.5:.0%} of 2.5); gap {gap/MM:.2f} in")
# a 3528 under an optic rated on XP LEDs may come out wider (EST); what widening eats the 30 deg margin at t 0.326 mm?
lo, hi = 15.0, 25.0
for _ in range(60):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if smear_mil(mid, T_EST) < 2.5 else (lo, mid)
print(f"2.5 mil at t 0.326 mm is reached at a half-angle of {lo:.2f} deg ({2*lo:.1f} deg full): "
      f"30 deg has {2*lo - 30:.1f} deg of room for widening, 25 deg has {2*lo - 25:.1f} deg")

print("\n== XL6009 load (no listing read: Amazon blocks agents)")
r_load = v_out / i_out
print(f"dummy load {v_out} V / {i_out:.4f} A = {r_load:.1f} ohm at {v_out*i_out:.2f} W; "
      f"loss at 85 % (EST) = {p_in:.2f} - {p_out:.2f} = {p_in - p_out:.2f} W in the module")
print(f"average input at 11.75 V: {p_in/11.75:.2f} A = {p_in/11.75/4:.0%} of a 4 A peak-input listing rating")
