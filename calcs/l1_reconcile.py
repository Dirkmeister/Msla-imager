# L1: L1.1 light-engine reconcile (old L1 rev 2 + diagram rev 3 -> one packet). Re-derives every number diagram rev 3 states, rev 2's hand-worked numbers (>= 50.25 W, 0.55 % = tan^2(7.5 deg)/pi, 1/7) and the L1.1 packet's new numbers; rebuilds the imager-04 formulas it uses (imager_calcs.py is not in calcs/). Run: python3 calcs/l1_reconcile.py (needs numpy). CHECK lines compare each recomputed value with the packet's printed value.
"""
Sections
  A  Inputs, with sources
  B  imager-04 formulas, rebuilt
  C  Rev 2's scripted numbers (ce543be), recomputed independently
  D  Rev 2's hand-worked numbers: >= 50.25 W, 0.55 %, 1/7, the 6 x 6 diagonal
  E  Every number diagram rev 3 states (cluster, 6b table, levers, power, thermal,
     reflector, lens matrix, diffuse-array model)
  F  L1.1's new numbers: UV allocation, string headroom, sink drift, heatsink target,
     Fresnel spec, LED-height tolerance, L1.5 methods, stack-thickness sensitivity
  G  Check summary
EST marks an estimate. DS = datasheet. Units: in first, mm in brackets where printed.
"""
import math
import numpy as np

IN = 25.4            # mm per in
MIL = 0.0254         # mm per mil
CHECKS = []
trapz = getattr(np, "trapezoid", None) or np.trapz      # numpy 2.x or 1.x
print("# L1: output of calcs/l1_reconcile.py (package L1.1). Regenerate: python3 calcs/l1_reconcile.py > calcs/l1_reconcile_out.txt")


def check(src, label, value, packet, tol=None):
    """Compare value with the packet's printed string. Default tolerance: half a unit
    in the packet's last printed digit (so the value rounds to the packet's figure)."""
    p = float(packet)
    dec = len(packet.split(".")[1]) if "." in packet else 0
    if tol is None:
        tol = 0.5 * 10 ** (-dec) + 1e-9
    ok = abs(value - p) <= tol
    CHECKS.append((src, label, ok))
    print(f"  CHECK [{src}] {label}: {value:.{dec + 2}f} vs packet {packet} -> {'OK' if ok else 'DIFF'}")
    return ok


def head(title):
    print("\n" + "=" * 100 + f"\n{title}\n" + "=" * 100)


# ---------------------------------------------------------------------------------------------
head("A. Inputs")
PX_MM = 0.04725                                   # 47.25 um pixel (vendor; imager-04 §2)
W_MM, H_MM = 2560 * PX_MM, 1440 * PX_MM           # image, long x short
W_IN, H_IN = W_MM / IN, H_MM / IN
DIAG_IN = math.hypot(W_IN, H_IN)
CORNER_MM = math.hypot(W_MM, H_MM) / 2
CORNER_IN = CORNER_MM / IN
AREA_CM2 = (W_MM / 10) * (H_MM / 10)
print(f"image 2560 x {PX_MM} = {W_MM:.2f} mm ({W_IN:.4f} in); 1440 x {PX_MM} = {H_MM:.2f} mm ({H_IN:.4f} in)")
print(f"diagonal {DIAG_IN:.3f} in ({DIAG_IN * IN:.1f} mm); corner radius {CORNER_IN:.3f} in ({CORNER_MM:.2f} mm); area {AREA_CM2:.2f} cm2")

T_EST = 0.725            # mm, stack t estimate (imager-04 §1, EST until L2.1)
N_GL = 1.5               # glass/polarizer index (assumption, imager-04 §1)
BUDGET = 2.5             # mil, REQ-008

# CUN0LF1B, Seoul Viosys DS Rev3.0 (2021-07-02), Ts 25 C, IF 180 mA
PHI = 0.210              # W typ (+-10 % measurement tolerance)
PHI_BINS = {"G5": (0.19, 0.21), "H1": (0.21, 0.24), "H2": (0.24, 0.27), "H3": (0.27, 0.30),
            "H4": (0.30, 0.33), "H5": (0.33, 0.36)}
VF = 3.3                 # V typ
VF_BINS = {"Z2": (3.1, 3.2), "Z3": (3.2, 3.3), "Z4": (3.3, 3.4), "Z5": (3.4, 3.5)}
VF_MIN, VF_MAX = 3.1, 3.5
IF_DS, IF_ABS_MIN, IF_ABS_MAX = 0.180, 0.050, 0.250
TJ_MAX_DS = 95.0         # C
RTH_JS = 17.4            # C/W, junction to solder (metal PCB, 2 W/m.K, 2 oz)
HALF_ANGLE = 60.0        # deg (120 deg radiation angle)
PKG = (3.5, 2.8)         # mm, 3528 body (nominal; DS outline not readable)
PKG_HALF_DIAG = math.hypot(*PKG) / 2
print(f"CUN0LF1B (DS Rev3.0): {PHI * 1000:.0f} mW typ at {IF_DS * 1000:.0f} mA; flux bins G5 0.19-0.21 .. H5 0.33-0.36 W; "
      f"Vf {VF} V typ, bins {VF_MIN}-{VF_MAX} V; 120 deg; IF {IF_ABS_MIN * 1000:.0f}-{IF_ABS_MAX * 1000:.0f} mA; Tj <= {TJ_MAX_DS:.0f} C; "
      f"RthJ-S {RTH_JS} C/W")
print(f"3528 body {PKG[0]} x {PKG[1]} mm: half-diagonal sqrt({PKG[0]}^2 + {PKG[1]}^2)/2 = {PKG_HALF_DIAG:.3f} mm ({PKG_HALF_DIAG / IN:.4f} in)")

# p.88 sink as corrected (imager-04 §9): BD139 pass, BC547 sense, 3.9 ohm
VBE = (0.609, 0.689, 0.729)      # V at ~2 mA, min/typ/max (DS NXP + VT ln 3, EST)
R_SENSE = 3.9
I_SINK = tuple(v / R_SENSE for v in VBE)
print(f"sink current VBE/R: {VBE[0]}/3.9 = {I_SINK[0] * 1000:.1f}, {VBE[1]}/3.9 = {I_SINK[1] * 1000:.1f}, {VBE[2]}/3.9 = {I_SINK[2] * 1000:.1f} mA")

VS = 26.2                # V, boost setting (imager-04 §8)
ETA = 0.85               # boost efficiency (p.81, measured at 23.4 W out on the old light; EST here)
RDS = 0.044              # ohm, IRF540N (DS IR, imager-04 §9)
OTHERS = {"switch MOSFET (2.34 A, RDS doubled)": 0.48, "7805 rail": 1.02, "Pi 5 V 2.5 A / 0.85": 5 * 2.5 / 0.85,
          "VS-CXMIPI-V1 5 V 1 A / 0.85": 5 * 1.0 / 0.85, "fans": 3.00}
NON_UV = sum(OTHERS.values())
print("non-UV lines (imager-04 §10, ratings basis): " + " + ".join(f"{v:.2f}" for v in OTHERS.values()) + f" = {NON_UV:.2f} W")
LIMIT = 48.0             # W, REQ-029
UV_AVAIL = LIMIT - NON_UV
print(f"UV available at 12 V on that basis: {LIMIT:.0f} - {NON_UV:.2f} = {UV_AVAIL:.2f} W; at the strings x {ETA}: {UV_AVAIL * ETA:.2f} W")
TA, TB_LIM, TJ_LIM = 35.0, 75.0, 85.0   # C: ambient (EST), REQ-030 board and junction limits


# ---------------------------------------------------------------------------------------------
head("B. imager-04 formulas, rebuilt")


def smear(alpha_deg, t_mm=T_EST, n=N_GL):
    """§5: s = t tan(asin(sin a / n)), mil."""
    return t_mm / MIL * math.tan(math.asin(math.sin(math.radians(alpha_deg)) / n))


def alpha_max(t_mm=T_EST, b=BUDGET, n=N_GL):
    """§5: alpha_max = asin(n sin(atan(b/t))), deg."""
    return math.degrees(math.asin(n * math.sin(math.atan(b * MIL / t_mm))))


def t_limit(alpha_deg, b=BUDGET, n=N_GL):
    """Largest t (mm) that keeps a source half-angle inside b."""
    return b * MIL / math.tan(math.asin(math.sin(math.radians(alpha_deg)) / n))


def m_of(half_deg):
    """§3: m = -ln 2 / ln cos(half angle)."""
    return -math.log(2) / math.log(math.cos(math.radians(half_deg)))


def ratio(f_in, m):
    """§6: corner/center = cos^(m+3)(atan(corner/f))."""
    return math.cos(math.atan(CORNER_IN / f_in)) ** (m + 3)


def f_for_ratio(target, m):
    return CORNER_IN / math.tan(math.acos(target ** (1 / (m + 3))))


def G(A, B):
    """Closed form of the m = 1 quadrant integral of 1/(1+x^2+y^2)^2 over [0,A]x[0,B]; odd in A and B."""
    sa, sb = math.sqrt(1 + A * A), math.sqrt(1 + B * B)
    return 0.5 * (A / sa * math.atan(B / sa) + B / sb * math.atan(A / sb))


def frac_m1(f_in):
    """Share of a Lambertian (m = 1) source's flux on the image, source at the focus: 4 G / pi."""
    return 4 * G(W_IN / 2 / f_in, H_IN / 2 / f_in) / math.pi


_gx, _gw = np.polynomial.legendre.leggauss(160)


def frac_m(f_in, m):
    """General m: (m+1)/(2 pi) x integral of f^(m+1)/R^(m+3) over the image (Gauss-Legendre)."""
    a, b = W_IN / 2, H_IN / 2
    x = (_gx + 1) * a / 2
    y = (_gx + 1) * b / 2
    X, Y = np.meshgrid(x, y)
    R2 = X ** 2 + Y ** 2 + f_in ** 2
    integrand = f_in ** (m + 1) / R2 ** ((m + 3) / 2)
    val = (np.outer(_gw, _gw) * integrand).sum() * (a / 2) * (b / 2) * 4
    return (m + 1) / (2 * math.pi) * val


def e0_per_w(f_in, m):
    """On-axis irradiance per W of flux, mW/cm2: 1000 (m+1) / (2 pi f^2), f in cm."""
    return 1000 * (m + 1) / (2 * math.pi * (f_in * 2.54) ** 2)


def rect_frac(x1, x2, y1, y2, z):
    """m = 1: share of one LED's flux landing on the rectangle [x1,x2]x[y1,y2] (LED-relative, mm) at height z."""
    return (G(x2 / z, y2 / z) - G(x1 / z, y2 / z) - G(x2 / z, y1 / z) + G(x1 / z, y1 / z)) / math.pi


m1 = m_of(HALF_ANGLE)
print(f"m for 120 deg (half angle 60): -ln2/ln cos60 = {m1:.3f}")
print(f"alpha_max at t {T_EST} mm: asin(1.5 sin(atan({BUDGET}/{T_EST / MIL:.2f}))) = {alpha_max():.2f} deg")
print(f"m = 1 closed form vs Gauss-Legendre at f 10 in: {frac_m1(10) * 100:.4f} % vs {frac_m(10, 1) * 100:.4f} %")
AMAX = alpha_max()


# ---------------------------------------------------------------------------------------------
head("C. Rev 2's scripted numbers (ce543be scripts), recomputed independently")
for f, r_p, fr_p, sp_p in ((8, "0.802", "5.89", "2.11"), (9, "0.838", "4.73", "2.37"),
                           (10, "0.866", "3.87", "2.63"), (12, "0.904", "2.73", "3.16")):
    span = 2 * f * math.tan(math.radians(7.5))
    print(f" f {f} in: cos^4(atan({CORNER_IN:.3f}/{f})) = {ratio(f, 1):.3f}; on image {frac_m1(f) * 100:.2f} %; "
          f"span 2 x {f} x tan 7.5 = {span:.2f} in")
    check("rev 2", f"corner/center f {f}", ratio(f, 1), r_p)
    check("rev 2", f"flux on image % f {f}", frac_m1(f) * 100, fr_p)
    check("rev 2", f"max source span in f {f}", span, sp_p)
check("rev 2", "f for 0.84, m = 1 (in)", f_for_ratio(0.84, 1), "9.05")
span66 = 5 * 0.200 + PKG[0] / IN
a66 = math.degrees(math.atan(span66 / 2 / 10))
print(f" 6 x 6 at 0.200 in: span 5 x 0.200 + {PKG[0] / IN:.4f} = {span66:.3f} in; half side atan({span66 / 2:.3f}/10) = {a66:.2f} deg; "
      f"smear {smear(a66):.2f} mil")
check("rev 2", "6x6 span in", span66, "1.138")
check("rev 2", "6x6 half-side angle deg", a66, "3.26")
check("rev 2", "6x6 smear half side mil", smear(a66), "1.08")
check("rev 2", "36 x 3.3 x 0.180 W", 36 * VF * IF_DS, "21.4")
check("rev 2", "6.8 mm package in", 6.8 / IN, "0.268")
for vd in (58.0, 55.0):                       # same EST as l1_m0_calcs.py: two-term Cauchy from nd 1.49
    nd, lF, lC, ld = 1.49, 0.4861, 0.6563, 0.5876
    B = (nd - 1) / vd / (1 / lF ** 2 - 1 / lC ** 2)
    A = nd - B / ld ** 2
    n405, n550 = A + B / 0.405 ** 2, A + B / 0.550 ** 2
    print(f" PMMA EST (nd 1.49, Vd {vd:.0f}): n405 {n405:.4f}, n550 {n550:.4f}, f405/f550 = {(n550 - 1) / (n405 - 1):.4f}")
FSHIFT = (0.9742, 0.9755)     # EST range from the two lines above


# ---------------------------------------------------------------------------------------------
head("D. Rev 2's hand-worked numbers")
print("D1. '>= 50.25 W': not printed in the rev 2 packet; it is the packet's 21.4 W of LED power taken to the 12 V input")
p_led36 = 36 * VF * IF_DS
p_in36 = p_led36 / ETA
print(f"  36 x {VF} x {IF_DS} = {p_led36:.3f} W at the LEDs; / {ETA} boost = {p_in36:.3f} W at 12 V; + {NON_UV:.3f} non-UV = {p_in36 + NON_UV:.3f} W")
check("rev 2 via HQ", "rev 2 cluster total W", p_in36 + NON_UV, "50.25")
s6 = 6 * VF_MAX + VBE[2] + 1.0
p6 = 6 * IF_DS * s6 / ETA
print(f"  '>=': the 21.38 W leaves out the sinks. Example, 6 strings of 6 at {s6:.2f} V (6 x 3.5 + 0.729 + 1.0): "
      f"6 x 0.18 x {s6:.2f} / 0.85 = {p6:.2f} W in, total {p6 + NON_UV:.2f} W")
n_led_max = UV_AVAIL * ETA / (VF * IF_DS)
n_str_max = math.floor(UV_AVAIL * ETA / (IF_DS * VS))
print(f"  most LEDs at 180 mA inside 48 W, ratings basis: LEDs alone {UV_AVAIL * ETA:.2f} / ({VF} x {IF_DS}) = {n_led_max:.1f}; "
      f"strings of 7 at {VS} V: floor({UV_AVAIL * ETA:.2f} / ({IF_DS} x {VS})) = {n_str_max} strings = {7 * n_str_max} LEDs")

print("D2. Option D's 0.55 %: the louver geometry")
a75 = math.tan(math.radians(7.5))
louver = a75 ** 2 / math.pi
print(f"  Square-cell absorbing louver, cell width w, wall height L, w/L = tan 7.5 = {a75:.5f} (cutoff 7.5 deg along a cell axis).")
print("  A ray with projected tangents (tx, ty) passes T = (1 - |tx|/a)(1 - |ty|/a). A Lambertian source sends equal flux per unit")
print("  projected solid angle, and that element is dtx dty / (1 + tx^2 + ty^2)^2, about dtx dty here, out of pi in total. So")
print(f"  share = (1/pi) [integral of (1 - |t|/a) dt]^2 = a^2 / pi = {a75:.5f}^2 / pi = {louver * 100:.3f} %")
check("rev 2", "louver square cell %", louver * 100, "0.55")
gx = np.linspace(-a75, a75, 2001)
TX, TY = np.meshgrid(gx, gx)
T = (1 - np.abs(TX) / a75) * (1 - np.abs(TY) / a75)
exact = trapz(trapz(T / (1 + TX ** 2 + TY ** 2) ** 2, gx, axis=1), gx) / math.pi
cone = math.sin(math.radians(7.5)) ** 2
print(f"  same integral without the small-angle step: {exact * 100:.3f} %")
print(f"  ideal cone, everything inside 7.5 deg passes and nothing outside: sin^2 7.5 = {cone * 100:.3f} %  (lead's figure)")
check("lead", "cone sin^2 7.5 %", cone * 100, "1.70")
print(f"  louver / cone = {louver / cone:.3f} (about 1/pi = {1 / math.pi:.3f}): the cell walls vignette linearly in each axis")
print("  Any cell shape: share = cell area / (pi L^2); its cutoff is (widest cell width)/L. Held to 7.5 deg in every direction:")
sq_diag = 0.5 * a75 ** 2 / math.pi
hexa = (3 * math.sqrt(3) / 8) * a75 ** 2 / math.pi
tube = (math.pi / 4) * a75 ** 2 / math.pi
print(f"    square cell, 7.5 deg on its diagonal (45 deg edges): 0.5 a^2/pi = {sq_diag * 100:.3f} %; "
      f"diagonal cutoff of the axis-held cell atan(sqrt2 a) = {math.degrees(math.atan(math.sqrt(2) * a75)):.2f} deg")
print(f"    hex cell, 7.5 deg corner to corner: (3 sqrt3/8) a^2/pi = {hexa * 100:.3f} %;  round tube: (pi/4) a^2/pi = {tube * 100:.3f} %")

print("D3. The 1/7 ratio = D's 0.55 % over the cluster's share on the image at f = 10 in")
fr10 = frac_m1(10)
print(f"  {louver * 100:.4f} / {fr10 * 100:.4f} = {louver / fr10:.4f} = 1/{fr10 / louver:.2f}")
check("rev 2", "1/x of the 1/7 ratio", fr10 / louver, "7", tol=0.1)
print(f"  cone bound {cone * 100:.3f} / {fr10 * 100:.3f} = 1/{fr10 / cone:.2f}; hex all directions 1/{fr10 / hexa:.1f}; "
      f"square on its diagonal 1/{fr10 / sq_diag:.1f}. D is darker than A in every case.")

print("D4. Rev 2's 6 x 6 cluster on the diagonal (HQ's rule: largest radius, package included)")
r66 = 2.5 * 0.200 * math.sqrt(2) + PKG_HALF_DIAG / IN
a66d = math.degrees(math.atan(r66 / 10))
print(f"  corner LED centre 2.5 x 0.200 x sqrt2 = {2.5 * 0.2 * math.sqrt(2):.4f} in + {PKG_HALF_DIAG / IN:.4f} = {r66:.4f} in; "
      f"atan({r66:.4f}/10) = {a66d:.2f} deg; smear {smear(a66d):.2f} mil")
check("HQ", "6x6 smear on the diagonal mil", smear(a66d), "1.51")


# ---------------------------------------------------------------------------------------------
head("E. Diagram rev 3: every stated number")
print("E1. Cluster geometry (5 x 5 less corners at 4.0 mm; 28-LED variant)")
P = 4.0
g5 = [(i * P, j * P) for i in range(-2, 3) for j in range(-2, 3) if not (abs(i) == 2 and abs(j) == 2)]
far21 = max(math.hypot(x, y) for x, y in g5)
R21 = far21 + PKG_HALF_DIAG
g6 = [((i - 2.5) * P, (j - 2.5) * P) for i in range(6) for j in range(6)]
g6 = [p for p in g6 if not (abs(p[0]) == 10 and abs(p[1]) == 10)]          # 4 corners out
g6 = [p for p in g6 if not (abs(p[0]) == 10 and abs(p[1]) == 6)]           # one 11.66 mm site per corner out
far28 = max(math.hypot(x, y) for x, y in g6)
R28 = far28 + PKG_HALF_DIAG
print(f"  21 sites: {len(g5)}; farthest centre sqrt(8^2 + 4^2) = {far21:.2f} mm; + {PKG_HALF_DIAG:.2f} = {R21:.2f} mm "
      f"({R21 / IN:.3f} in), {2 * R21:.1f} mm ({2 * R21 / IN:.2f} in) across")
print(f"  28 sites: {len(g6)}; farthest centre sqrt(10^2 + 6^2) = {far28:.2f} mm; r = {R28:.2f} mm")
check("rev 3", "farthest centre 21 mm", far21, "8.94")
check("rev 3", "package half-diagonal mm", PKG_HALF_DIAG, "2.24")
check("rev 3", "r 21 mm", R21, "11.19")
check("rev 3", "farthest centre 28 mm", far28, "11.66")
check("rev 3", "r 28 mm", R28, "13.90")
F84 = f_for_ratio(0.84, 1)
for f, a_p, s_p in ((6, "4.20", "1.39"), (F84, "2.79", "0.93"), (10, "2.52", "0.84"), (12, "2.10", "0.70")):
    a = math.degrees(math.atan(R21 / (f * IN)))
    print(f"  f {f:5.2f} in: atan({R21:.2f}/{f * IN:.1f}) = {a:.2f} deg, smear {smear(a):.2f} mil")
    check("rev 3", f"cluster half-angle deg f {f:.2f}", a, a_p)
    check("rev 3", f"cluster smear mil f {f:.2f}", smear(a), s_p)
check("rev 3", "alpha_max deg", AMAX, "7.52")
check("rev 3", "allowed radius at f 10 mm", 10 * IN * math.tan(math.radians(AMAX)), "33.5")
for f, s_p in ((10, "1.04"), (6, "1.73")):
    check("rev 3", f"28-LED smear mil f {f}", smear(math.degrees(math.atan(R28 / (f * IN)))), s_p)

print("E2. §6b table, m = 1, 21 LEDs x 0.210 W = 4.41 W; 28 LEDs x 0.210 = 5.88 W")
FLUX21, FLUX28 = 21 * PHI, 28 * PHI
for f, r_p, fr_p, mean_p, dim_p, m28_p in ((6, "0.686", "9.93", "5.32", "4.15", "7.09"), (8, "0.802", "5.89", "3.16", "2.73", "4.21"),
                                           (F84, "0.840", "4.67", "2.50", "2.23", "3.34"), (10, "0.866", "3.87", "2.07", "1.88", "2.76"),
                                           (12, "0.904", "2.73", "1.46", "1.37", "1.95")):
    r = ratio(f, 1)
    fr = frac_m1(f)
    mean_w = fr * 1000 / AREA_CM2
    dim_w = e0_per_w(f, 1) * r
    a_f = math.degrees(math.atan(R21 / (f * IN)))
    print(f"  f {f:5.2f} in ({f * IN:5.1f} mm): ratio {r:.3f}; on image {fr * 100:.2f} %; mean {mean_w:.3f}/W x {FLUX21:.2f} = {mean_w * FLUX21:.2f}; "
          f"dimmest E0 {e0_per_w(f, 1):.3f} x {r:.3f} = {dim_w:.3f}/W x {FLUX21:.2f} = {dim_w * FLUX21:.2f} mW/cm2; 28 LEDs mean {mean_w * FLUX28:.2f}; "
          f"cluster {a_f:.2f} deg, {smear(a_f):.2f} mil")
    check("rev 3", f"6b ratio f {f:.2f}", r, r_p)
    check("rev 3", f"6b on image % f {f:.2f}", fr * 100, fr_p)
    check("rev 3", f"6b mean 21 f {f:.2f}", mean_w * FLUX21, mean_p)
    check("rev 3", f"6b dimmest 21 f {f:.2f}", dim_w * FLUX21, dim_p)
    check("rev 3", f"6b mean 28 f {f:.2f}", mean_w * FLUX28, m28_p)
F707 = f_for_ratio(2 ** -0.5, 1)
check("rev 3", "f for 0.840 in", F84, "9.05")
check("rev 3", "f for 0.840 mm", F84 * IN, "229.9")
check("rev 3", "f for 0.707 in", F707, "6.28")
d6, d84 = e0_per_w(6, 1) * ratio(6, 1), e0_per_w(F84, 1) * ratio(F84, 1)
print(f"  masking 9.05 -> 6 in: dimmest per W {d6:.3f} / {d84:.3f} = {d6 / d84:.2f}x")
check("rev 3", "masking gain", d6 / d84, "1.86")
check("rev 3", "28/21 scale", 28 / 21, "1.33")
# §4's best diffuse layout, recomputed: 7 x 3 at 25 x 38 mm, z 32 mm, centred on the image
L2538 = [((i - 3) * 25.0, (j - 1) * 38.0) for i in range(7) for j in range(3)]
fr2538 = sum(rect_frac(-W_MM / 2 - x, W_MM / 2 - x, -H_MM / 2 - y, H_MM / 2 - y, 32.0) for x, y in L2538) / 21
print(f"  §4 grid-search layout on the image: {fr2538 * 100:.1f} % of flux; mean {FLUX21:.2f} x {fr2538:.4f} x 1000 / {AREA_CM2:.2f} = "
      f"{FLUX21 * fr2538 * 1000 / AREA_CM2:.1f} mW/cm2; vs the cluster at f 10: {fr2538 * 100:.1f} / {fr10 * 100:.2f} = {fr2538 / fr10:.1f}x")
check("rev 3", "§4 layout on image %", fr2538 * 100, "32.8", tol=0.1)
check("rev 3", "§4 layout mean mW/cm2", FLUX21 * fr2538 * 1000 / AREA_CM2, "17.6")
check("rev 3", "32.8/3.87", 32.8 / 3.87, "8.5")

print("E3. LED-part levers")
m60 = m_of(30.0)
f84_60 = f_for_ratio(0.84, m60)
fr60 = frac_m(f84_60, m60)
fr_cun84 = frac_m1(F84)
print(f"  60 deg full angle: m = -ln2/ln cos30 = {m60:.2f}; 0.84 at f = {f84_60:.2f} in; on image {fr60 * 100:.2f} %; "
      f"CUN at {F84:.2f} in {fr_cun84 * 100:.2f} %; {fr60 / fr_cun84:.2f}x")
check("rev 3", "m 60 full", m60, "4.82")
check("rev 3", "f 0.84 at m 4.82 in", f84_60, "12.79")
check("rev 3", "on image % m 4.82", fr60 * 100, "6.81")
check("rev 3", "narrow-beam gain", fr60 / fr_cun84, "1.46")
wpe = PHI / (VF * IF_DS)
print(f"  CUN wall-plug {PHI} / ({VF} x {IF_DS}) = {wpe:.3f}; strings' share of 48 W: ({LIMIT:.0f} - {NON_UV:.2f}) x {ETA} = {UV_AVAIL * ETA:.2f} W")
check("rev 3", "WPE %", wpe * 100, "35")
check("rev 3", "string budget W", UV_AVAIL * ETA, "19.47")

print("E4. Power, strings of 7 at 180 mA, 26.2 V, 85 %")
for ns, in_p, tot_p, sw_p in ((3, "16.64", "41.73", "1.39"), (4, "22.19", "47.28", "1.85"), (5, "27.74", "52.83", "2.31")):
    out = ns * IF_DS * VS
    inp = out / ETA
    print(f"  {ns} strings: {ns} x {IF_DS} x {VS} = {out:.2f} W out; / {ETA} = {inp:.2f} W in; total {inp + NON_UV:.2f} W; "
          f"{inp / 12:.2f} A at 12 V; {ns * IF_DS:.2f} A out")
    check("rev 3", f"{ns} strings in W", inp, in_p)
    check("rev 3", f"{ns} strings total W", inp + NON_UV, tot_p)
    check("rev 3", f"{ns} strings switch A", inp / 12, sw_p)
check("rev 3", "4 strings out W", 4 * IF_DS * VS, "18.86")
check("rev 3", "3 strings out A", 3 * IF_DS, "0.54")
check("rev 3", "4 strings out A", 4 * IF_DS, "0.72")
check("rev 3", "coarse wedge top s (15 x 2^(11/2))", 15 * 2 ** 5.5, "679", tol=0.5)
check("rev 3", "p.81 out W", 25.7 * 0.91, "23.39")
check("rev 3", "§10 3-string A", (3 * IF_DS * VS / ETA + NON_UV) / 12, "3.48")
check("rev 3", "§10 3-string % of 60 W", (3 * IF_DS * VS / ETA + NON_UV) / 60 * 100, "70", tol=0.5)
check("rev 3", "§10 margin W", LIMIT - (3 * IF_DS * VS / ETA + NON_UV), "6.27")
check("rev 3", "IBT input W (p.81)", 11.75 * 2.34, "27.50")
check("rev 3", "IBT-era total W", 11.75 * 2.34 + NON_UV, "52.58")
check("atlas", "old §10 3528 total less switch W", 3 * IF_DS * VS / ETA + NON_UV - 0.48, "41.25")

print("E5. Thermal and switch")
q21, q28 = 21 * (VF * IF_DS - PHI), 28 * (VF * IF_DS - PHI)
r21 = (TJ_LIM - TA - (VF * IF_DS - PHI) * RTH_JS) / q21
r28 = (TJ_LIM - TA - (VF * IF_DS - PHI) * RTH_JS) / q28
print(f"  21 x ({VF} x {IF_DS} - {PHI}) = {q21:.2f} W, Rth <= (85 - 35 - {VF * IF_DS - PHI:.3f} x 17.4) / {q21:.2f} = {r21:.2f} C/W; "
      f"28: {q28:.2f} W, {r28:.2f} C/W")
check("rev 3", "heat 21 W", q21, "8.06")
check("rev 3", "Rth 21", r21, "5.37")
check("rev 3", "heat 28 W", q28, "10.75")
check("rev 3", "Rth 28", r28, "4.03")
check("rev 3", "REQ-030 junction check C", 75 + (VF * IF_DS - PHI) * RTH_JS, "81.7")
for i_a, p_p, d_p in ((1.39, "0.085", "0.17"), (1.85, "0.15", "0.30")):
    check("rev 3", f"gate loss at {i_a} A", i_a ** 2 * RDS, p_p)
    check("rev 3", f"gate loss doubled at {i_a} A", 2 * i_a ** 2 * RDS, d_p)
check("rev 3", "0.48 W switch line", 2 * 2.34 ** 2 * RDS, "0.48")
check("rev 3", "BD139 W at 26.2 V, min bin, typ VBE", (VS - 7 * VF_MIN - 0.69) * 0.177, "0.67")
q_ibt = 25.7 * 0.91 / 4                      # IBT record, imager-04 §11 restated by rev 3
rj_ibt = 0.6 * q_ibt                         # p.80 Rth 0.6 C/W
print(f"  IBT record: 25.7 x 0.91 / 4 = {q_ibt:.2f} W/module; junction rise 0.6 x {q_ibt:.2f} = {rj_ibt:.1f} C; "
      f"(85 - 35 - {rj_ibt:.1f} - 2) / {q_ibt:.2f} = {(50 - rj_ibt - 2) / q_ibt:.2f} C/W, four on one sink {(50 - rj_ibt - 2) / (4 * q_ibt):.2f}")
check("rev 3", "IBT W/module", q_ibt, "5.85")
check("rev 3", "IBT Rth one", (50 - 3.5 - 2) / q_ibt, "7.61")
check("rev 3", "IBT Rth four", (50 - 3.5 - 2) / (4 * q_ibt), "1.90")

print("E6. Reflector (ideal CPC, exit in the focal plane), f = 10 in. Rev 3 feeds r_in as printed (11.19, 13.9 mm); so does this check")
th_c = math.degrees(math.atan(CORNER_MM / 254))
check("rev 3", "corner angle deg", th_c, "15.28")
check("rev 3", "r_out limit 21 mm", 11.19 / math.sin(math.radians(th_c)), "42.5")
check("rev 3", "r_out limit 28 mm", 13.9 / math.sin(math.radians(th_c)), "52.7")
print(f"  unrounded r_in {R21:.3f} and {R28:.3f} mm: limits {R21 / math.sin(math.radians(th_c)):.2f} and {R28 / math.sin(math.radians(th_c)):.2f} mm; "
      f"gains at 20/25/33.5 mm {(20 / R21) ** 2:.2f}/{(25 / R21) ** 2:.2f}/{(33.5 / R21) ** 2:.2f}: third-digit changes only")
MEAN21_10 = round(frac_m1(10) * 1000 / AREA_CM2 * FLUX21, 2)
MEAN28_10 = round(frac_m1(10) * 1000 / AREA_CM2 * FLUX28, 2)
for rin, e0, rows in ((11.19, MEAN21_10, (("20", "3.19", "6.6", "4.50", "1.50", "46.2"), ("25", "4.99", "10.3", "5.62", "1.87", "72.3"),
                                          ("33.5", "8.96", "18.6", "7.51", "2.50", "126.1"))),
                      (13.9, MEAN28_10, (("25", "3.23", "8.9", "5.62", "1.87", "58.2"),))):
    for ro_s, g_p, m_p, a_p, s_p, L_p in rows:
        ro = float(ro_s)
        tho = math.degrees(math.asin(rin / ro))
        gain = (ro / rin) ** 2
        a = math.degrees(math.atan(ro / 254))
        L = (rin + ro) / math.tan(math.radians(tho))
        print(f"  r_in {rin:.2f}, r_out {ro} mm ({ro / IN:.2f} in): theta_out {tho:.2f} deg; gain ({ro}/{rin:.2f})^2 = {gain:.2f}; "
              f"mean {e0} x {gain:.2f} = {e0 * gain:.1f}; angle {a:.2f} deg, smear {smear(a):.2f} mil; length {L:.1f} mm ({L / IN:.2f} in)")
        check("rev 3", f"reflector gain {rin:.2f}/{ro}", gain, g_p)
        check("rev 3", f"reflector mean {rin:.2f}/{ro}", e0 * gain, m_p)
        check("rev 3", f"reflector angle {ro}", a, a_p)
        check("rev 3", f"reflector smear {ro}", smear(a), s_p)
        check("rev 3", f"CPC length {rin:.2f}/{ro}", L, L_p)

print("E7. Lens matrix (D-12 C)")
cw, ch = W_MM / 7, H_MM / 4
k = 1 / math.tan(math.radians(AMAX))
D_L = F_L = 17.0
beta = math.degrees(math.atan(D_L / 2 / F_L))
cap = math.sin(math.radians(beta)) ** 2
aL = math.degrees(math.atan(PKG_HALF_DIAG / F_L))
meanC = FLUX28 * cap * 1000 / AREA_CM2
corner_c = math.cos(math.atan(math.hypot(cw, ch) / 2 / F_L)) ** 4
print(f"  cell {W_MM:.2f}/7 = {cw:.2f} x {H_MM:.2f}/4 = {ch:.2f} mm; f >= {k:.2f} r_e = {k * PKG_HALF_DIAG:.2f} mm; D = f = 17: "
      f"{aL:.2f} deg, {smear(aL):.2f} mil; capture sin^2({beta:.2f}) = {cap:.3f}; mean {FLUX28:.2f} x {cap:.3f} x 1000 / {AREA_CM2:.2f} = {meanC:.2f}")
for lab, v, p in (("cell long mm", cw, "17.28"), ("cell short mm", ch, "17.01"), ("f/r_e", k, "7.57"), ("f min mm", k * PKG_HALF_DIAG, "16.98"),
                  ("lens angle deg", aL, "7.51"), ("lens smear mil", smear(aL), "2.50"), ("capture", cap, "0.200"),
                  ("on image W", FLUX28 * cap, "1.176"), ("mean mW/cm2", meanC, "14.29"), ("vs A 28", meanC / MEAN28_10, "5.2"),
                  ("aperture edge cos^4", math.cos(math.radians(beta)) ** 4, "0.64"), ("cell half-diagonal mm", math.hypot(cw, ch) / 2, "12.12"),
                  ("cell corner cos^4", corner_c, "0.44"), ("gap 7.52 mm", cw / (2 * math.tan(math.radians(AMAX))), "65.4"),
                  ("gap 7.52 in", cw / (2 * math.tan(math.radians(AMAX))) / IN, "2.58"), ("gap 4.0 mm", cw / (2 * math.tan(math.radians(4.0))), "123.6"),
                  ("gap 4.0 in", cw / (2 * math.tan(math.radians(4.0))) / IN, "4.86"), ("0.2 mm tilt deg", math.degrees(math.atan(0.2 / F_L)), "0.67"),
                  ("0.2 mm shift mil", smear(math.degrees(math.atan(0.2 / F_L))), "0.22"),
                  ("0.2 mm front-to-back mil", 2 * smear(math.degrees(math.atan(0.2 / F_L))), "0.45")):
    check("rev 3", f"C {lab}", v, p)
xtalk = math.degrees(math.atan(cw / F_L))
print(f"  new: the {100 * (1 - cap):.0f} % of each LED's flux outside its own lens enters neighbours {cw:.2f} mm off their axis and leaves "
      f"at about atan({cw:.2f}/{F_L:.0f}) = {xtalk:.1f} deg, far past {AMAX:.2f}: C needs an absorbing baffle grid between LEDs and lenses")

print("E8. Diffuse arrays (D-12 B), imager-04 §5 model: ray offsets at the mask, weighted by flat-target irradiance")


def diffuse(leds, z, t_mm, P):
    leds = np.asarray(leds, float)
    dx, dy = leds[:, 0] - P[0], leds[:, 1] - P[1]
    r = np.hypot(dx, dy)
    s = t_mm * np.tan(np.arcsin(np.sin(np.arctan2(r, z)) / N_GL)) / MIL
    ux = np.divide(dx, r, out=np.zeros_like(dx), where=r > 0)
    uy = np.divide(dy, r, out=np.zeros_like(dy), where=r > 0)
    return s * ux, s * uy, z ** 2 / (r ** 2 + z ** 2) ** 2


def pct(x, w, q):
    """Weighted percentile, step convention: smallest offset whose cumulative weight reaches q."""
    o = np.argsort(x)
    c = np.cumsum(w[o]) / w.sum()
    return x[o][np.searchsorted(c, q)]


V1 = [((i - 3) * 15.0, (j - 1) * 15.0) for i in range(7) for j in range(3)]
for name, L, z, t_mm, refs in (("V1, z 0.59 in, t 0.725", V1, 15.0, 0.725, ("30.5", "26.2", "12.1", "14.3", "15.3", "21.0")),
                               ("25 x 38, z 1.26 in, t 0.725", L2538, 32.0, 0.725, ("25.7", "31.0", "24.4", "2.8", "2.4", "3.7")),
                               ("V1, t 0.25", V1, 15.0, 0.25, ("10.5", "9.0", "4.2", "4.9", "5.3", "7.2")),
                               ("25 x 38, t 0.25", L2538, 32.0, 0.25, ("8.9", "10.7", "8.4", "1.0", "0.8", "1.3"))):
    ox, oy, w = diffuse(L, z, t_mm, (0, 0))
    cl, cs = pct(ox, w, 0.9) - pct(ox, w, 0.1), pct(oy, w, 0.9) - pct(oy, w, 0.1)
    ox2, oy2, w2 = diffuse(L, z, t_mm, (W_MM / 2, H_MM / 2))
    kl = pct(ox2, w2, 0.9) - pct(ox2, w2, 0.1)
    mx, my = abs((ox2 * w2).sum() / w2.sum()), abs((oy2 * w2).sum() / w2.sum())
    print(f"  {name}: centre 10-90 % long {cl:.1f}, short {cs:.1f}; corner long {kl:.1f}; corner shift {mx:.1f} long, {my:.1f} short, "
          f"{math.hypot(mx, my):.1f} radial (mil)")
    for lab, v, p in zip(("centre long", "centre short", "corner long", "shift long", "shift short", "shift radial"),
                         (cl, cs, kl, mx, my, math.hypot(mx, my)), refs):
        check("rev 3/§5", f"{name} {lab}", v, p)
print("  Note: the 10-90 % spreads use the step percentile; a mid-point convention moves them by up to 4 mil. B fails by 10x either way.")


# ---------------------------------------------------------------------------------------------
head("F. L1.1 new numbers")
print("F1. UV allocation, ratings basis (§10 lines as printed: Pi and driver at supply ratings, switch at its 2.34 A loss)")
alloc = {}
for lab, i in zip(("min", "typ", "max"), I_SINK):
    out_a = 3 * i
    out_w = VS * out_a
    in_w = out_w / ETA
    alloc[lab] = in_w
    print(f"  3 strings, sinks {lab} {i * 1000:.1f} mA: {out_a:.3f} A out x {VS} = {out_w:.2f} W; / {ETA} = {in_w:.2f} W in; "
          f"{in_w / 12:.2f} A at 12 V, {in_w / 11.75:.2f} A at 11.75 V; total {in_w + NON_UV:.2f} W")
UVW = alloc["max"]
print(f"  allocation {UVW:.2f} W of the {UV_AVAIL:.2f} W available; spare {UV_AVAIL - UVW:.2f} W; total {UVW + NON_UV:.2f} W = "
      f"{(UVW + NON_UV) / 12:.2f} A, {(UVW + NON_UV) / 60 * 100:.0f} % of 60 W")
in4 = 4 * I_SINK[2] * VS / ETA
sw4 = 2 * (in4 / 12) ** 2 * RDS
print(f"  4 strings at {I_SINK[2] * 1000:.1f} mA: {in4:.2f} W in, total {in4 + NON_UV:.2f} W, {in4 + NON_UV - LIMIT:+.2f} W vs 48 W. With L3's switch line "
      f"reset to {in4 / 12:.2f} A (doubled RDS {sw4:.3f} W, not 0.48): {in4 + NON_UV - 0.48 + sw4:.2f} W")
sw3 = (UVW / 12) ** 2 * RDS
print(f"  switch loss at {UVW / 12:.2f} A: {UVW / 12:.2f}^2 x {RDS} = {sw3:.3f} W, doubled {2 * sw3:.3f} W (L3's §10 line is 0.48)")
print(f"  CC backstop, if the boost has CC: above 3 x {I_SINK[2]:.3f} = {3 * I_SINK[2]:.3f} A max; set 0.60 A (EST)")

print("F2. String headroom at 26.2 V, DS Vf bins at 180 mA (Vf at 187 mA not readable from the DS)")
for lab, vf in (("Z2 min", VF_MIN), ("typ", VF), ("Z5 max", VF_MAX)):
    st = 7 * vf
    print(f"  {lab}: 7 x {vf} = {st:.1f} V; VCE = {VS} - {st:.1f} - 0.689 = {VS - st - VBE[1]:.2f} V")
vce_worst = VS - 7 * VF_MAX - VBE[2]
print(f"  worst, Z5 with VBE 0.729: {VS} - {7 * VF_MAX:.1f} - 0.729 = {vce_worst:.3f} V; 1.0 V needs {7 * VF_MAX + VBE[2] + 1.0:.2f} V, so 26.3 V if the stock is Z5")
pd = {"typ": (VS - 7 * VF - VBE[1]) * I_SINK[1], "Z2, typ VBE": (VS - 7 * VF_MIN - VBE[1]) * I_SINK[1],
      "worst (Z2, VBE 0.729)": (VS - 7 * VF_MIN - VBE[2]) * I_SINK[2]}
print("  BD139 dissipation: " + "; ".join(f"{k} {v:.3f} W" for k, v in pd.items()))
print(f"  waste in the 3 sinks plus sense at typ: 3 x ({VS} - {7 * VF:.1f}) x {I_SINK[1]:.3f} = {3 * (VS - 7 * VF) * I_SINK[1]:.2f} W")

print("F3. Sink drift (REQ-015, +-3 % over 15 min)")
tc = -2.0e-3 / VBE[1]
print(f"  I = VBE/R, VBE about -2 mV/C (silicon, EST): {tc * 100:.2f} %/C; 10 C on the BC547 = {tc * 1000:.1f} %")

print("F4. Heatsink target")
qw = VF_MAX * I_SINK[2] - PHI_BINS["G5"][0]
for n_led in (21, 28):
    qt, qx = n_led * (VF * IF_DS - PHI), n_led * qw
    print(f"  {n_led} LEDs: typ {qt:.2f} W, worst {n_led} x ({VF_MAX} x {I_SINK[2]:.3f} - 0.19) = {qx:.2f} W; board <= 75 C at 35 C: "
          f"Rth(s-a) <= 40 / Q = {40 / qt:.2f} typ, {40 / qx:.2f} worst C/W")
print(f"  Tj at a 75 C board, worst: 75 + {qw:.4f} x {RTH_JS} = {75 + qw * RTH_JS:.1f} C (REQ-030 85, DS 95); at REQ-033's 80 C cutoff: {80 + qw * RTH_JS:.1f} C")
print(f"  rev 3's 5.37 C/W puts the board at 35 + 5.37 x {q21:.2f} = {35 + 5.37 * q21:.1f} C, over its own 75 C REQ-030 line")

print("F5. Fresnel spec")
gap_in = 0.5                                       # lens-to-LCD gap assumed for the margin (in, EST)
a10 = math.degrees(math.atan(R21 / 254))
margin = gap_in * math.tan(math.radians(a10)) + 0.05
clear = DIAG_IN + 2 * margin
print(f"  clear area: diagonal {DIAG_IN:.3f} + 2 x ({gap_in} tan {a10:.2f} + 0.05 placement) = {clear:.3f} in ({clear * IN:.1f} mm) circle; "
      f"rectangle {W_IN + 2 * margin:.2f} x {H_IN + 2 * margin:.2f} in")
for g_mm in (5.0, 10.0):
    print(f"  groove wash-out: lens {g_mm:.0f} mm under the LCD blurs ring shadows over 2 x {g_mm:.0f} x tan {a10:.2f} = {2 * g_mm * math.tan(math.radians(a10)):.2f} mm")
print(f"  rev 2's '6 in circle or 5.5 x 3.5 in' clears it: {6 - clear:.2f} in spare on the circle, "
      f"{5.5 - (W_IN + 2 * margin):.2f} x {3.5 - (H_IN + 2 * margin):.2f} in on the rectangle")
print("  f trade, 21 LEDs (before Fresnel and LCD losses):")
for f in (9.05, 10.0, 11.0, 12.0):
    a = math.degrees(math.atan(R21 / (f * IN)))
    print(f"    f {f:5.2f} in ({f * IN:5.1f} mm): ratio {ratio(f, 1):.3f}, mean {frac_m1(f) * 1000 / AREA_CM2 * FLUX21:.2f}, dimmest "
          f"{e0_per_w(f, 1) * ratio(f, 1) * FLUX21:.2f} mW/cm2, smear {smear(a):.2f} mil")
print(f"  405 nm focus, EST: {FSHIFT[0]} to {FSHIFT[1]} x f(550); at 10.0 in visible: {10 * FSHIFT[0]:.2f}-{10 * FSHIFT[1]:.2f} in, "
      f"shift {10 * (1 - FSHIFT[1]):.3f}-{10 * (1 - FSHIFT[0]):.3f} in ({10 * IN * (1 - FSHIFT[1]):.1f}-{10 * IN * (1 - FSHIFT[0]):.1f} mm)")

print("F6. LED-height tolerance, f = 10 in: a defocus d tilts the edge rays by r d / f^2, a pure scale change")
per_mm = math.degrees(CORNER_MM / 254 ** 2)
d_tol = 0.25 * IN
tilt = per_mm * d_tol
k_scale = T_EST * (d_tol / 254 ** 2) / N_GL
print(f"  corner: {CORNER_MM:.2f} / 254^2 = {per_mm:.4f} deg per mm; angle budget left {AMAX:.2f} - {a10:.2f} = {AMAX - a10:.2f} deg = "
      f"{(AMAX - a10) / per_mm:.0f} mm of defocus")
print(f"  +-0.25 in ({d_tol:.2f} mm): {tilt:.3f} deg; worst corner angle {a10 + tilt:.2f} deg, smear {smear(a10 + tilt):.2f} mil; "
      f"corner shift {smear(tilt):.3f} mil (scale only)")
print(f"  front-to-back if the flip axis sits 0.2 in off the optical axis: 2 x {k_scale:.2e} x 5.08 mm = {2 * k_scale * 5.08 / MIL:.3f} mil")

print("F7. L1.5 method M1, two-hole check (EST)")
h, Dt = 50.8, 610.0
sens = 2 * Dt * h / 254 ** 2
print(f"  holes at +-2.00 in, target 24.0 in: beamlet separation changes 2 x {Dt:.0f} x {h} / 254^2 = {sens:.3f} mm per mm of LED height")
print(f"  blur, one LED (package bound {PKG_HALF_DIAG:.2f} mm): +-{PKG_HALF_DIAG / 254 * Dt:.1f} mm; whole cluster: +-{R21 / 254 * Dt:.1f} mm")
phi50 = PHI * 0.050 / IF_DS
frac_hole = math.sin(math.atan(5.08 / 254)) ** 2
print(f"  one LED at 50 mA: {phi50 * 1000:.0f} mW (EST, linear in current); a 0.40 in hole at 10 in takes sin^2(atan(5.08/254)) = {frac_hole:.2e}: "
      f"{phi50 * frac_hole * 1e6:.0f} uW per beamlet")

print("F8. L1.5 method M2, transmission (EST)")
I0 = PHI / math.pi
for z_in in (1.0, 2.0):
    print(f"  one CUN at 180 mA, detector {z_in} in away: I0 = {PHI}/pi = {I0:.4f} W/sr; E = {I0 * 1000 / (z_in * 2.54) ** 2:.2f} mW/cm2")
print(f"  film variant: half a sqrt2 step = 2^(1/4) = +{(2 ** 0.25 - 1) * 100:.1f} %; half a fine step = 2^(1/8) = +{(2 ** 0.125 - 1) * 100:.1f} %")

print("F9. Stack thickness t: what holds as L2.1 measures it")
SRC = {"A, 21 at f 10 (2.52 deg)": a10, "A+R, 25 mm exit (5.62 deg)": math.degrees(math.atan(25 / 254)),
       "C, package-bound lens (7.51 deg)": aL, "rev 2 6x6 diagonal (4.55 deg)": a66d}
print("  t, in (mm)       alpha_max   " + "  ".join(f"{k.split(' (')[0]:>18s}" for k in SRC) + "   reflector exit cap, gain")
for t_mm in (0.25, 0.50, 0.725, 1.00, 1.45):
    am = alpha_max(t_mm)
    ro = min(254 * math.tan(math.radians(am)), R21 / math.sin(math.radians(th_c)))
    print(f"  {t_mm / IN:.4f} ({t_mm:5.3f})   {am:6.2f}     " + "  ".join(f"{smear(a, t_mm):16.2f}  " for a in SRC.values())
          + f"   {ro:5.1f} mm, {(ro / R21) ** 2:5.2f}x")
for k, a in SRC.items():
    print(f"  {k}: holds 2.5 mil up to t = {t_limit(a):.3f} mm ({t_limit(a) / IN:.4f} in)")
t_corner = 0.25
lo, hi = 0.05, 2.0
for _ in range(60):                       # t where alpha_max reaches the corner-limited exit angle
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if alpha_max(mid) > math.degrees(math.atan(42.5 / 254)) else (lo, mid)
print(f"  the reflector exit reaches the 42.5 mm corner cap (alpha_max {math.degrees(math.atan(42.5 / 254)):.2f} deg) at t <= {lo:.3f} mm ({lo / IN:.4f} in)")
print(f"  louver D held to alpha_max(t), share of flux (vs A's {fr10 * 100:.2f} % at f 10 in):")
for t_mm in (0.25, 0.50, 0.725, 1.00):
    at = math.tan(math.radians(alpha_max(t_mm)))
    print(f"    t {t_mm:5.3f} mm: square on axis {at ** 2 / math.pi * 100:.2f} %, square on diagonal {0.5 * at ** 2 / math.pi * 100:.2f} %, "
          f"hex {(3 * math.sqrt(3) / 8) * at ** 2 / math.pi * 100:.2f} %, cone bound {math.sin(math.radians(alpha_max(t_mm))) ** 2 * 100:.2f} %")

print("F10. Irradiance per W for L6 (EST, f 10 in, before Fresnel and LCD losses)")
mpw, dpw = frac_m1(10) * 1000 / AREA_CM2, e0_per_w(10, 1) * ratio(10, 1)
print(f"  mean {mpw:.3f}, dimmest {dpw:.3f} mW/cm2 per W of LED flux; x {FLUX21:.2f} W = {mpw * FLUX21:.2f} and {dpw * FLUX21:.2f}; "
      f"after an 85 % Fresnel {mpw * FLUX21 * 0.85:.2f} and {dpw * FLUX21 * 0.85:.2f}")

print("F11. Flux bins (DS), against the 0.210 W typ")
for b, (lo_b, hi_b) in PHI_BINS.items():
    print(f"  {b}: {lo_b}-{hi_b} W, mid {(lo_b + hi_b) / 2 / PHI:.2f}x")


# ---------------------------------------------------------------------------------------------
head("G. Check summary")
for src in sorted({c[0] for c in CHECKS}):
    sub = [c for c in CHECKS if c[0] == src]
    print(f"  {src}: {sum(c[2] for c in sub)} of {len(sub)} match")
bad = [c for c in CHECKS if not c[2]]
print(f"  total: {len(CHECKS) - len(bad)} of {len(CHECKS)} match" + ("" if not bad else "; DIFF: " + "; ".join(f"[{s}] {l}" for s, l, _ in bad)))
