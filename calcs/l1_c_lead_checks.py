# L1: lead checks on L1.3 (D-12 = C, lens matrix): smear with the beam's tails at both stack t, C21 stack with its heatsink, edge falloff and side walls, string-current mismatch, C thermal budget and REQ-033's NTC, LCD absorbed power, optic-test drive, XL6009 dummy load. Run: python3 calcs/l1_c_lead_checks.py (stdlib only)
"""
Lead checks on L1.3's packet (77f61d2), for the L1 lane packet of 2026-11-16.

Inputs, as used in imager-04 and by L1.3:
  n = 1.5 (calc §1 assumption); REQ-008 budget 2.5 mil; t 0.725 mm (old basis) and 0.3258 mm (L2.1 EST).
  CUN0LF1B DS Rev3.0: 210 mW typ at 180 mA (G5 bin 0.19-0.21 W); Vf 3.1-3.5 V (Z2-Z5); RthJ-S 17.4 C/W;
    Tj <= 95 C; IF 50-250 mA.
  Sinks (calc §9): VBE 0.609/0.689/0.729 V over 3.9 ohm -> 156/177/187 mA.
  ATS-CPX060060025-132-C2-R0 (ATS DS): 2.70 C/W at 100 LFM, 1.40 at 200 LFM, unducted; 25 mm tall.
  NTC B57621C5103K062: 10 kohm +-10 % at 25 C, B25/85 3510 K.
  C21 (L1.3): 7 x 3 at 20.00 x 22.68 mm, 20 mm PMMA TIR optics, 15 deg FWHM rated on XP LEDs.
  L1.3's EST stack items, in: BASE 0.12, PLATE 0.25, BOARD 1.6 mm, OPTIC 0.45, T_LCD 0.12, T_COVER 0.12.
EST throughout: Gaussian beam with the rated FWHM; the 20 mm exit aperture folded in as a Gaussian of
sigma r/2; walls specular, R 0.85 (aluminum foil tape at 400 nm, not measured); 100 LFM through each ATS.
"""
import math

MM = 25.4
N = 1.5
BUDGET = 2.5                              # mil, REQ-008
T_BASIS, T_EST = 0.725, 0.3258            # mm
K1090 = 1.2816                            # Gaussian CDF: 10 % and 90 % at -/+1.2816 sigma
F2S = 2 * math.sqrt(2 * math.log(2))      # FWHM / sigma = 2.3548


def mil(mm):
    return mm / MM * 1000


def tan_glass(a_deg):
    """tan of the in-glass angle for an air angle a (calc §5)"""
    return math.tan(math.asin(math.sin(math.radians(a_deg)) / N))


def alpha_max(t):
    """hard-edge half-angle that smears exactly 2.5 mil at stack t (calc §5)"""
    return math.degrees(math.asin(N * math.sin(math.atan(BUDGET / mil(t)))))


def s_hard(a_deg, t):
    """calc §5: s = t tan(asin(sin a / n)), mil"""
    return mil(t) * tan_glass(a_deg)


def s_gauss(fwhm, t):
    """10-90 % half-width of the edge under a Gaussian beam of this FWHM, mil (EST)"""
    return K1090 * s_hard(fwhm / F2S, t)


def fwhm_max(t):
    """largest Gaussian FWHM whose 10-90 % half-width is 2.5 mil at t, deg (EST)"""
    th = math.atan(BUDGET / K1090 / mil(t))
    return math.degrees(math.asin(N * math.sin(th))) * F2S


def t_lim_hard(a_deg):
    return BUDGET / tan_glass(a_deg) / 1000 * MM          # mm


def t_lim_gauss(fwhm):
    return BUDGET / (K1090 * tan_glass(fwhm / F2S)) / 1000 * MM   # mm


print("== 1. Smear: hard edge at the half-maximum angle (L1.3's reading) vs the beam's tails (Gaussian, EST)")
print(f"alpha_max = asin(1.5 sin(atan(2.5/t))): {alpha_max(T_BASIS):.2f} deg at t 0.725 mm; "
      f"{alpha_max(T_EST):.2f} deg at t 0.326 mm (EST t)")
for t in (0.25, 0.5, 1.0):
    print(f"  check calc §5's list: {alpha_max(t):.1f} deg at t {t} mm")
print("calc §5 table, new column t 0.0128 in (0.326 mm, EST):")
for a in (1, 3, 10, 60):
    print(f"  alpha {a:>2} deg: {mil(T_EST):.2f} x tan(asin(sin {a}/1.5)) = {s_hard(a, T_EST):.2f} mil")
print("Gaussian beam: sigma = FWHM/2.3548; per-axis edge sigma_x = t tan(asin(sin sigma/1.5)); "
      "10-90 % half-width = 1.2816 sigma_x")
for fw in (10, 15, 20, 25, 30):
    print(f"  FWHM {fw:>2} deg: hard edge at {fw/2:.1f} deg {s_hard(fw/2, T_BASIS):.2f} mil at 0.725 mm, "
          f"{s_hard(fw/2, T_EST):.2f} at 0.326 mm | tails (10-90 %) {s_gauss(fw, T_BASIS):.2f} mil at 0.725 mm, "
          f"{s_gauss(fw, T_EST):.2f} at 0.326 mm")
sig15 = 15 / F2S
th90 = sig15 * math.sqrt(2 * math.log(10))
print(f"15 deg FWHM: sigma {sig15:.2f} deg; 90 % of the flux inside {th90:.2f} deg (2.146 sigma); "
      f"that angle as a hard edge: {s_hard(th90, T_BASIS):.2f} mil at 0.725 mm, {s_hard(th90, T_EST):.2f} at 0.326 mm")
print(f"15 deg FWHM holds 2.5 mil up to t = {t_lim_hard(7.5):.3f} mm ({t_lim_hard(7.5)/MM:.4f} in) read as a hard edge, "
      f"{t_lim_gauss(15):.3f} mm ({t_lim_gauss(15)/MM:.4f} in) with tails (EST)")
print(f"Largest Gaussian FWHM inside 2.5 mil (EST): {fwhm_max(T_BASIS):.1f} deg at t 0.725 mm, "
      f"{fwhm_max(T_EST):.1f} deg at t 0.326 mm")
print(f"calc §6d at t 0.326 mm: cone bound sin^2 {alpha_max(T_EST):.2f} = "
      f"{math.sin(math.radians(alpha_max(T_EST)))**2:.2%}; square cell tan^2/pi = "
      f"{math.tan(math.radians(alpha_max(T_EST)))**2/math.pi:.2%}")

print("\n== 2. C21 one-cell gap and stack (L1.3's EST items), with and without the heatsink")
BASE, PLATE, BOARD, OPTIC, T_LCD, T_COVER = 0.12, 0.25, 1.6 / MM, 0.45, 0.12, 0.12
ATS_H = 25 / MM
ROW = 68.04 / 3      # 22.68 mm
for fw in (15, 10):
    gap = ROW / (2 * math.tan(math.radians(fw / 2)))
    st = BASE + PLATE + BOARD + OPTIC + gap / MM + T_LCD + T_COVER
    print(f"FWHM {fw} deg: gap {ROW:.2f}/(2 tan {fw/2:.1f}) = {gap:.1f} mm ({gap/MM:.2f} in); "
          f"stack {BASE} + {PLATE} + {BOARD:.3f} + {OPTIC} + {gap/MM:.2f} + {T_LCD} + {T_COVER} = {st:.2f} in on a plate; "
          f"+ {ATS_H:.3f} in ATS under the plate = {st + ATS_H:.2f} in")

print("\n== 3. Uniformity over the image, C21 (EST model, see header)")
XS = [-60 + 20 * i for i in range(7)]          # mm, columns
YS = [-ROW, 0.0, ROW]                          # mm, rows
WX, WY = 70.0, 34.02                           # cell boundaries: 7 x 20 / 2; 3 x 22.68 / 2
IX, IY = 60.48, 34.02                          # image half-sizes


def grid(lo, hi, step=1.0):
    n = int(round((hi - lo) / step))
    return [lo + (hi - lo) * k / n for k in range(n + 1)]


GX, GY = grid(-IX, IX), grid(-IY, IY)


def sigma_fp(gap, fwhm):
    s_pos = gap * math.tan(math.radians(fwhm / F2S))
    return math.sqrt(s_pos ** 2 + 5.0 ** 2)


def profile(c, w, r, sig, pts, orders=3):
    out = []
    for p in pts:
        v = 0.0
        for k in range(-orders, orders + 1):
            if r == 0 and k != 0:
                continue
            ck = (-1) ** (k % 2) * c + 2 * k * w
            v += (r ** abs(k)) * math.exp(-((p - ck) ** 2) / (2 * sig * sig))
        out.append(v)
    return out


def emap(gap, fwhm, r, weights):
    sig = sigma_fp(gap, fwhm)
    fx = {x: profile(x, WX, r, sig, GX) for x in XS}
    fy = {y: profile(y, WY, r, sig, GY) for y in YS}
    e = [[0.0] * len(GY) for _ in GX]
    for (x, y), w in weights.items():
        ax, ay = fx[x], fy[y]
        for i in range(len(GX)):
            a = w * ax[i]
            row = e[i]
            for j in range(len(GY)):
                row[j] += a * ay[j]
    return e, sig


def stats(e):
    flat = [v for row in e for v in row]
    mx = max(flat)
    inner = [e[i][j] for i, x in enumerate(GX) for j, y in enumerate(GY) if abs(x) <= 50 and abs(y) <= ROW]
    ec = e[GX.index(min(GX, key=abs))][-1]          # long-edge center
    se = e[-1][GY.index(min(GY, key=abs))]          # short-edge center
    co = e[-1][-1]
    return min(flat) / mx, min(inner) / max(inner), ec / mx, se / mx, co / mx


ones = {(x, y): 1.0 for x in XS for y in YS}
GAP15 = ROW / (2 * math.tan(math.radians(7.5)))
for label, r in (("no walls", 0.0), ("walls R 0.85", 0.85), ("walls R 0.92", 0.92)):
    e, sig = emap(GAP15, 15, r, ones)
    mn, inn, ec, se, co = stats(e)
    print(f"gap {GAP15:.1f} mm, {label}: footprint sigma sqrt(({GAP15:.1f} tan {15/F2S:.2f})^2 + 5^2) = {sig:.2f} mm; "
          f"min/max {mn:.3f}; interior {inn:.3f}; long-edge center {ec:.3f}; short-edge center {se:.3f}; corner {co:.3f}")
for g in (55.0, 65.0, 75.0, 100.0, 120.0):
    e, sig = emap(g, 15, 0.85, ones)
    mn, inn, ec, se, co = stats(e)
    print(f"  ripple vs gap, walls R 0.85: gap {g:.0f} mm ({g/MM:.2f} in): min/max {mn:.3f}, interior {inn:.3f}")

print("String currents at the sinks' spread (calc §9: 156/177/187 mA), walls R 0.85, gap 86.1 mm:")
import itertools
cur = (156.0, 177.0, 187.0)
worst_rows, worst_diag = 1.0, 1.0
for perm in itertools.permutations(cur):
    w_rows = {(x, y): perm[k] for k, y in enumerate(YS) for x in XS}
    w_diag = {(x, y): perm[(i + k) % 3] for k, y in enumerate(YS) for i, x in enumerate(XS)}
    worst_rows = min(worst_rows, stats(emap(GAP15, 15, 0.85, w_rows)[0])[0])
    worst_diag = min(worst_diag, stats(emap(GAP15, 15, 0.85, w_diag)[0])[0])
print(f"  one string per row, worst order: min/max {worst_rows:.3f}")
print(f"  strings interleaved on the diagonals ((column + row) mod 3), worst order: min/max {worst_diag:.3f}")
for tr in (0.01, 0.02):
    trim = ((1 - tr) * 177, 177.0, (1 + tr) * 177)
    worst = 1.0
    for perm in itertools.permutations(trim):
        w_trim = {(x, y): perm[(i + k) % 3] for k, y in enumerate(YS) for i, x in enumerate(XS)}
        worst = min(worst, stats(emap(GAP15, 15, 0.85, w_trim)[0])[0])
    print(f"  trimmed to +-{tr:.0%} and interleaved, worst order: min/max {worst:.3f}")
print("LED flux spread inside one bin (G5 0.19-0.21 W: uniform +-5 %), strings trimmed to +-1 %, walls R 0.85, "
      "200 random draws (seed 1):")
import random
rng = random.Random(1)
res = []
for _ in range(200):
    w = {(x, y): (1 + rng.uniform(-0.01, 0.01)) * (1 + rng.uniform(-0.05, 0.05)) for x in XS for y in YS}
    res.append(stats(emap(GAP15, 15, 0.85, w)[0])[0])
res.sort()
print(f"  min/max: median {res[100]:.3f}, 5th percentile {res[10]:.3f}, worst {res[0]:.3f}")

print("\n== 4. C thermal (REQ-030: solder point <= 75 C at Ta 35 C, so 40 C of rise)")
q_typ = 3.3 * 0.180 - 0.210
q_max = 3.5 * 0.187 - 0.190
Q_typ, Q_max = 21 * q_typ, 21 * q_max
print(f"heat per LED = Vf x I - Phi: {q_typ:.3f} W typ, {q_max:.4f} W worst; 21 LEDs {Q_typ:.2f} / {Q_max:.2f} W")
for label, th in (("one ATS, 100 LFM", 2.70), ("three ATS in parallel, 100 LFM", 2.70 / 3),
                  ("one ATS, 200 LFM", 1.40), ("three ATS, 200 LFM", 1.40 / 3)):
    rise = Q_max * th
    print(f"  {label}: plate rise {Q_max:.2f} x {th:.3f} = {rise:.1f} C; each LED's solder point to plate "
          f"<= (40 - {rise:.1f})/{q_max:.4f} = {(40 - rise)/q_max:.1f} C/W")
tj_lim = 75 + q_max * 17.4
print(f"Tj at the 75 C board limit: 75 + {q_max:.4f} x 17.4 = {tj_lim:.1f} C (REQ-030 85, DS 95)")
print("REQ-033's 80 C trip, by NTC position (worst-case LED):")
print(f"  on the board at the center LED: Tj = 80 + {q_max*17.4:.2f} = {80 + q_max*17.4:.1f} C")
for th_sp in (29.4, 67.2):
    sp = 80 + q_max * th_sp
    print(f"  on the plate, solder point {th_sp} C/W above it: solder point 80 + {q_max:.4f} x {th_sp} = {sp:.1f} C, "
          f"Tj {sp + q_max*17.4:.1f} C")
B, R25 = 3510.0, 10000.0


def r_ntc(tc):
    return R25 * math.exp(B * (1 / (tc + 273.15) - 1 / 298.15))


def t_ntc(r):
    return 1 / (1 / 298.15 + math.log(r / R25) / B) - 273.15


r80 = r_ntc(80)
print(f"NTC trip resistance at 80 C: {r80:.0f} ohm; a +10 % part trips at {t_ntc(r80/1.1):.1f} C, "
      f"a -10 % part at {t_ntc(r80/0.9):.1f} C (B taken as exact, EST); Tj at the late trip "
      f"{t_ntc(r80/1.1) + q_max*17.4:.1f} C")

print("\n== 5. Light and LCD heat (L1.3's C mean, EST capture 50-80 %, before walls and T_LCD)")
A_IMG, A_BOX = 120.96 * 68.04 / 100, 140 * 68.04 / 100
for cap in (0.5, 0.8):
    e = 21 * 210 * cap / A_BOX
    print(f"  capture {cap:.0%}: 21 x 210 mW x {cap} / {A_BOX:.2f} cm^2 = {e:.1f} mW/cm^2 = {e/1.76:.1f}x A's 1.76; "
          f"onto the LCD's {A_IMG:.2f} cm^2 image: {e*A_IMG/1000:.2f} W, all heat if T_LCD -> 0")
print(f"  A for comparison: 1.76 x {A_IMG:.2f} = {1.76*A_IMG/1000:.3f} W")

print("\n== 6. Optic-test drive: 3 strings of 3 from the 12 V brick, one ballast resistor each (EST)")
r_b = (12.0 - 3 * 3.3) / 0.180
print(f"R = (12.0 - 3 x 3.3)/0.180 = {r_b:.2f} ohm -> 12 ohm (E12)")
for v in (12.0, 11.75):
    cs = [(v - 3 * vf) / 12.0 for vf in (3.1, 3.3, 3.5)]
    print(f"  at {v} V: I = {cs[0]*1000:.0f} / {cs[1]*1000:.0f} / {cs[2]*1000:.0f} mA at Vf 3.1 / 3.3 / 3.5 V "
          f"(DS max IF 250 mA); P_R typ {cs[1]**2*12:.2f} W, max {cs[0]**2*12:.2f} W")
print(f"  with the calc §9 sinks from 12 V instead: VCE = 12 - 3 x 3.3 - 0.689 = {12-9.9-0.689:.2f} V typ, "
      f"12 - 3 x 3.5 - 0.729 = {12-10.5-0.729:.2f} V at the top bin")
print(f"  test-board heat: 9 x {q_max:.4f} = {9*q_max:.2f} W worst at 187 mA")

print("\n== 7. XL6009 dummy load (L1.3: 46.7 ohm = 26.2 / 0.5608 A)")
r_d = 2 * 24
print(f"two 24 ohm in series = {r_d} ohm: {26.2/r_d:.4f} A, {26.2**2/r_d:.2f} W total, {26.2**2/r_d/2:.2f} W each; "
      f"{26.2**2/r_d/(26.2**2/46.7):.1%} of L1.3's 14.69 W")

print("\n== 8. Optic-test expectations (EST)")
s_rad = math.radians(15 / F2S)
print(f"On-axis gain of a 15 deg FWHM Gaussian beam over the bare LED (m = 1, I0 = Phi/pi): "
      f"eta / (2 sigma^2) = eta / (2 x {s_rad:.4f}^2) = {1/(2*s_rad**2):.1f} eta")
print(f"Far field: 12 in (305 mm) = {305/20:.1f} optic diameters")
