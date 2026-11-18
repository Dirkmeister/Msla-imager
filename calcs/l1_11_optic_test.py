# L1: L1.11 optic test analysis (rotation rig): T-UV-7 eta by flux integration of angular scans, T-UV-6 FWHM vs height from 12 and 18 in scans, profile tails, pointing of all 9, the 10-90 % edge half-width at the resist (calc §5), C21 or C28, build-optics line. Readings: calcs/l1_11_optic_readings.csv. Run: python3 calcs/l1_11_optic_test.py [--selftest | --skeleton] (stdlib only)
"""
Method (light/l1_11/README.md, sections 4 and 5; proposed to the lead as a change to imager-06):
the board turns about a vertical axis through the center optic's exit face; the detector (a spare CUN0LF1B,
read as mV across RL or as uA) faces the axis from D = 4, 12 or 18 in. A scan is readings vs dial angle.

Readings CSV columns: test, pass, config, axis, D_in, shim_mm, led, angle_deg, reading, unit, kind, notes
  test   TUV7 (eta), TUV6H (FWHM vs height), TUV6P (full profile), POINT (pointing)
  config bare | optic      axis x (board at 0 deg: scan along the rows, 20.00 mm pitch) | y (board at 90 deg, 22.68 mm)
  D_in   4 | 12 | 18       shim_mm holder height above seated (0, 0.25, 0.50 ...)     led 1-9, row-major, 5 = center
  angle_deg dial reading (zero is found from the data)    kind scan | dark (UV off; subtracted from its group)
Every result is a ratio or an angle, so the detector needs no calibration; keep RL and the unit fixed within a test.

Formulas:
  flux through the sphere of radius D about the axis: Phi = 2 pi D^2 Int_0^90 E(phi) sin(phi) dphi, with E the
    mean of the four half-profiles (two axes, both sides of the peak); tail past the last angle taken to fall
    linearly to zero at 90 deg. eta = Phi_optic / Phi_bare, same D, alternating passes.
    The bare LED sits h_exit behind the axis; at D = 4 in that tilts its light on the detector by at most
    atan(h_exit / D) = 5.6 deg, a cosine error under 0.5 % (EST), ignored.
  far-field half angle from the half-max angles at D1 = 12 in and D2 = 18 in:
    tan(theta) = (D2 tan(phi2) - D1 tan(phi1)) / (D2 - D1); FWHM = 2 theta (the difference removes the 20 mm aperture).
  edge at the resist (calc §5 edge metric): a ray at air angle a moves t tan(asin(sin a / n)) across the stack.
    The beam is rebuilt in 2D from the x and y profiles (azimuth-weighted, cos^2 / sin^2), projected onto x
    (and y), and the edge-spread function's 10 % and 90 % points give the half-width (u90 - u10) / 2 in mil.
    Check: a Gaussian of FWHM 15 deg gives 1.2816 t tan(asin(sin sigma / n)) = 1.22 mil at t 0.326 mm (calc §5).
  pointing: LED k sits s_k off the axis along the scan; at the peak's dial angle phi_c its beam points
    delta_k = atan2(-s_k cos phi_c, D + s_k sin phi_c) - phi_c off its optic's axis. The sign of s (which way the
    board faces) is taken as the one with the smaller spread; the script says which.
Inputs: n = 1.5 (calc §1); REQ-008 2.5 mil; t 0.0128 in (0.326 mm, L2.1 EST) and 0.0285 in (0.725 mm, old basis)
until T-LCD-4 measures it; h_exit 10.0 mm (EST until the holder is drawn).
"""
import csv
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "l1_11_optic_readings.csv")
INCH = 25.4
N = 1.5
BUDGET = 2.5                     # mil, REQ-008
T_LIST = [0.3258, 0.725]         # mm: L2.1 EST, old basis
K1090 = 1.2816
F2S = 2 * math.sqrt(2 * math.log(2))
PITCH = {"x": [-20.0, 0.0, 20.0], "y": [-22.68, 0.0, 22.68]}
COLS = ["test", "pass", "config", "axis", "D_in", "shim_mm", "led", "angle_deg", "reading", "unit", "kind", "notes"]
ETA_MIN = 0.50                   # T-UV-7 pass, EST (L1.3's low end)


def _sym(pos):
    return sorted({-x for x in pos} | set(pos))


# scan plans: dial angles in degrees, relative to where the peak is expected (light/l1_11/README.md, section 4)
PLAN_BARE = _sym([5.0 * i for i in range(18)])                                      # 0..85 every 5: 35 readings
PLAN_T7 = _sym([1.0 * i for i in range(16)] + [17.5 + 2.5 * i for i in range(10)]
               + [45.0 + 5 * i for i in range(9)])                                  # 1 to 15, 2.5 to 40, 5 to 85: 69
PLAN_6H = _sym([0.0] + [4.0 + i for i in range(9)])                                 # on axis, 4..12 every 1: 19
PLAN_6P = _sym([0.5 * i for i in range(21)] + [11.0 + i for i in range(10)]
               + [22.5 + 2.5 * i for i in range(8)])                                # 0.5 to 10, 1 to 20, 2.5 to 40: 77
PLAN_PT = [-9.0, -6.0, -3.0, 0.0, 3.0, 6.0, 9.0]                                     # around -atan(s/D): 7


def mil(mm):
    return mm / INCH * 1000


def shift_mil(a_deg, t_mm):
    """lateral move across the stack for an air angle a (calc §5), mil"""
    return mil(t_mm) * math.tan(math.asin(math.sin(math.radians(a_deg)) / N))


def interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            f = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + f * (ys[i] - ys[i - 1])
    return ys[-1]


def interp_log(xs, ys, x):
    """log-linear between positive neighbours (follows Gaussian-like flanks); linear otherwise"""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            f = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            y0, y1 = ys[i - 1], ys[i]
            if y0 > 0 and y1 > 0:
                return math.exp(math.log(y0) + f * (math.log(y1) - math.log(y0)))
            return y0 + f * (y1 - y0)
    return ys[-1]


def half_max(ang, val):
    """left and right half-max angles by linear interpolation outward from the peak"""
    pts = sorted(zip(ang, val))
    a = [p[0] for p in pts]
    v = [p[1] for p in pts]
    k = max(range(len(v)), key=lambda i: v[i])
    h = v[k] / 2
    left = right = None
    for i in range(k, 0, -1):
        if v[i - 1] <= h <= v[i]:
            left = a[i - 1] + (h - v[i - 1]) / (v[i] - v[i - 1]) * (a[i] - a[i - 1])
            break
    for i in range(k, len(v) - 1):
        if v[i + 1] <= h <= v[i]:
            right = a[i] + (v[i] - h) / (v[i] - v[i + 1]) * (a[i + 1] - a[i])
            break
    return left, right, a[k], v[k]


def fold(ang, val, step=0.25, log=False):
    """centre on the half-max midpoint and average both sides onto 0..max (deg); log-linear for optic beams"""
    left, right, _, _ = half_max(ang, val)
    c = (left + right) / 2 if left is not None and right is not None else 0.0
    pts = sorted(zip(ang, val))
    a = [p[0] - c for p in pts]
    v = [p[1] for p in pts]
    reach = min(-a[0], a[-1])
    g = [i * step for i in range(int(reach / step) + 1)]
    f = interp_log if log else interp
    e = [(f(a, v, x) + f(a, v, -x)) / 2 for x in g]
    return g, e, c


def sphere_flux(g, e, d_mm):
    """2 pi D^2 Int E sin(phi) dphi; tail to 90 deg linear to zero"""
    g = list(g)
    e = list(e)
    if g[-1] < 90:
        g.append(90.0)
        e.append(0.0)
    s = 0.0
    for i in range(1, len(g)):
        p0, p1 = math.radians(g[i - 1]), math.radians(g[i])
        s += (e[i - 1] * math.sin(p0) + e[i] * math.sin(p1)) / 2 * (p1 - p0)
    return 2 * math.pi * d_mm ** 2 * s


def mean_profile(profiles):
    """average folded profiles on the shortest common grid"""
    n = min(len(p[0]) for p in profiles)
    g = profiles[0][0][:n]
    return g, [sum(p[1][i] for p in profiles) / len(profiles) for i in range(n)]


def frac_outside(g, e, theta):
    tot = out = 0.0
    for i in range(1, len(g)):
        w = (e[i - 1] * math.sin(math.radians(g[i - 1])) + e[i] * math.sin(math.radians(g[i]))) / 2 * (g[i] - g[i - 1])
        tot += w
        if g[i] > theta:
            out += w
    return out / tot


def _marginal(gx, ex, gy, ey, along, step):
    """2D beam rebuilt from two folded profiles (uniform grids), projected onto one axis"""
    amax = min(gx[-1], gy[-1])
    n = int(amax / step + 1e-9)
    axis = [i * step for i in range(-n, n + 1)]
    sx, sy = gx[1] - gx[0], gy[1] - gy[0]

    def look(g_step, e, rho):
        f = rho / g_step
        i = int(f)
        if i >= len(e) - 1:
            return e[-1]
        return e[i] + (f - i) * (e[i + 1] - e[i])

    marg = []
    for a in axis:
        s = 0.0
        for b in axis:
            rho = math.hypot(a, b)
            if rho > amax:
                continue
            ca2 = (a * a) / (rho * rho) if rho > 0 else 0.5
            if along == "y":
                ca2 = 1 - ca2
            s += ca2 * look(sx, ex, rho) + (1 - ca2) * look(sy, ey, rho)
        marg.append(s)
    return axis, marg


_MCACHE = {}


def edge_halfwidth(gx, ex, gy, ey, t_mm, along="x", step=0.25):
    """10-90 % half-width (mil) of the edge's spread, from the 2D beam rebuilt from two profiles"""
    key = (id(ex), id(ey), along, step)
    if key not in _MCACHE:
        _MCACHE[key] = _marginal(gx, ex, gy, ey, along, step)
    axis, marg = _MCACHE[key]
    tot = sum(marg)
    cdf, acc = [], 0.0
    for m in marg:
        acc += m
        cdf.append(acc / tot)
    u = [shift_mil(a, t_mm) for a in axis]
    u10 = interp(cdf, u, 0.10)
    u90 = interp(cdf, u, 0.90)
    return (u90 - u10) / 2


def fit_centre(ang, val, ref_g, ref_e, span=15.0, step=0.02):
    """shift c and scale k minimising sum (v - k ref(|a - c|))^2; returns c (deg)"""
    best = None
    a0 = sum(ang) / len(ang)
    for i in range(int(2 * span / step) + 1):
        c = a0 - span + i * step
        r = [interp(ref_g, ref_e, abs(a - c)) for a in ang]
        rr = sum(x * x for x in r)
        if rr <= 0:
            continue
        k = sum(v * x for v, x in zip(val, r)) / rr
        res = sum((v - k * x) ** 2 for v, x in zip(val, r))
        if best is None or res < best[0]:
            best = (res, c)
    return best[1]


def gaussian_halfwidth(fwhm, t_mm):
    return K1090 * shift_mil(fwhm / F2S, t_mm)


def pointing(phi_c_deg, s_mm, d_mm):
    p = math.radians(phi_c_deg)
    return math.degrees(math.atan2(-s_mm * math.cos(p), d_mm + s_mm * math.sin(p)) - p)


# ---------------------------------------------------------------- data
def load(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if not (r.get("reading") or "").strip():
                continue
            r["reading"] = float(r["reading"])
            r["angle_deg"] = float(r["angle_deg"]) if (r.get("angle_deg") or "").strip() else None
            r["D_in"] = float(r["D_in"])
            r["shim_mm"] = float(r["shim_mm"]) if (r.get("shim_mm") or "").strip() else None   # blank = set height
            r["led"] = int(r["led"] or 5)
            r["pass"] = int(r["pass"] or 1)
            r["kind"] = (r.get("kind") or "scan").strip() or "scan"
            rows.append(r)
    return rows


def groups(rows, test):
    out = {}
    for r in rows:
        if r["test"] != test:
            continue
        key = (r["pass"], r["config"], r["axis"], r["D_in"], r["shim_mm"], r["led"])
        out.setdefault(key, {"scan": [], "dark": []})[r["kind"]].append(r)
    res = {}
    for key, g in out.items():
        if not g["scan"]:
            continue
        dark = sum(r["reading"] for r in g["dark"]) / len(g["dark"]) if g["dark"] else 0.0
        res[key] = ([r["angle_deg"] for r in g["scan"]], [r["reading"] - dark for r in g["scan"]], dark)
    return res


# ---------------------------------------------------------------- synthetic data for --selftest
def synth(eta=0.85, fwhm_ff=15.0, tail=0.03, tail_fwhm=50.0, seed=7):
    """a Lambertian bare LED and a TIR beam (Gaussian core + wide tail) through a 20 mm aperture; mV readings"""
    rng = random.Random(seed)
    rows = []
    phi_b = 210.0                       # bare flux, arbitrary units
    sc, st = fwhm_ff / F2S, tail_fwhm / F2S

    def far(a, sc_, st_):               # un-normalised intensity of the optic's beam
        return (1 - tail) * math.exp(-a * a / (2 * sc_ * sc_)) + tail * math.exp(-a * a / (2 * st_ * st_))

    def beam(a, d_mm, true_c=0.0):
        sa = math.degrees(math.atan(10 / d_mm)) / 2          # aperture blur, EST quadrature model
        sc_, st_ = math.hypot(sc, sa), math.hypot(st, sa)
        return far(a - true_c, sc_, st_)

    def norm(d_mm):                     # scale so the optic's flux through the sphere is eta x bare
        g = [i * 0.05 for i in range(1801)]
        return eta * phi_b / sphere_flux(g, [beam(x, d_mm) for x in g], d_mm)

    def read(v):
        return round(v * (1 + rng.gauss(0, 0.002)) + rng.gauss(0, 0.05), 1)   # 0.1 mV steps

    gain = 4.0e5                        # arbitrary detector + RL scale, mV per unit irradiance
    d4, d12 = 4 * INCH, 12 * INCH
    offs = rng.uniform(-3, 3)           # unknown dial zero

    def add(test, p, cfg, ax, d_in, shim, led, a_dial, v):
        rows.append(dict(test=test, **{"pass": p}, config=cfg, axis=ax, D_in=float(d_in), shim_mm=shim, led=led,
                         angle_deg=a_dial + offs, reading=read(v), kind="scan"))

    for p in (1, 2, 3):
        for ax in ("x", "y") if p == 1 else ("x",):
            for a in PLAN_BARE:
                add("TUV7", p, "bare", ax, 4, 0.0, 5, a, gain * phi_b / (math.pi * d4 ** 2) * math.cos(math.radians(a)))
            k = norm(d4)
            for a in PLAN_T7:
                add("TUV7", p, "optic", ax, 4, 0.0, 5, a, gain * k * beam(a, d4))
    for shim, widen in ((0.0, 1.25), (0.25, 1.08), (0.5, 1.0), (0.75, 1.1)):
        for d_in in ((12, 18) if shim == 0.5 else (12,)):
            d = d_in * INCH
            k = norm(d)
            for ax in (("x", "y") if shim == 0.5 else ("x",)):
                for a in PLAN_6H:
                    add("TUV6H", 1, "optic", ax, d_in, shim, 5, a, gain * k * beam(a / widen, d))
    k = norm(d12)
    for ax in ("x", "y"):
        for a in PLAN_6P:
            add("TUV6P", 1, "optic", ax, 12, 0.5, 5, a, gain * k * beam(a, d12))
    true_tilt = {}
    for ax in ("x", "y"):
        for led in range(1, 10):
            col, row = (led - 1) % 3, (led - 1) // 3
            s = PITCH[ax][col if ax == "x" else row]
            dlt = 0.0 if led == 5 else rng.gauss(0, 0.6)
            true_tilt[(led, ax)] = dlt
            lo, hi = -15.0, 15.0                     # dial angle where LED k's tilted beam points at the detector
            for _ in range(60):
                mid = (lo + hi) / 2
                if pointing(mid, s, d12) - dlt > 0:
                    lo = mid
                else:
                    hi = mid
            pc = (lo + hi) / 2
            expect = -math.degrees(math.atan(s / d12))
            for a in PLAN_PT:
                add("POINT", 1, "optic", ax, 12, 0.5, led, expect + a, gain * k * beam(expect + a - pc, d12))
    for r in rows:
        r.setdefault("unit", "mV")
        r.setdefault("notes", "synthetic")
    return rows, true_tilt


# ---------------------------------------------------------------- analysis
def resolve_set_height(rows):
    """rows with a blank shim take the height where the 12 in x scan is narrowest"""
    fw = {}
    for (p, c, ax, d, sh, led), (a, v, dk) in groups([r for r in rows if r["shim_mm"] is not None], "TUV6H").items():
        lft, rgt, _, _ = half_max(a, v)
        if ax == "x" and d == 12.0 and lft is not None and rgt is not None:
            fw[sh] = rgt - lft
    best = min(fw, key=fw.get) if fw else 0.0
    for r in rows:
        if r["shim_mm"] is None:
            r["shim_mm"] = best
    return best


def analyse(rows, h_exit=10.0, t_meas=None, truth=None):
    t_list = [t_meas] if t_meas else T_LIST
    resolve_set_height(rows)
    print("== T-UV-7: optic efficiency eta = Phi_optic / Phi_bare (flux through the sphere about the axis)")
    g7 = groups(rows, "TUV7")
    passes = sorted({k[0] for k in g7})
    etas = []
    for p in passes:
        flux = {}
        for cfg in ("bare", "optic"):
            prof = [fold(a, v, log=(cfg == "optic")) for (pp, c, ax, d, sh, led), (a, v, dk) in g7.items()
                    if pp == p and c == cfg]
            if not prof:
                continue
            d_mm = [k[3] for k in g7 if k[0] == p and k[1] == cfg][0] * INCH
            g, e = mean_profile([(x[0], x[1]) for x in prof])
            flux[cfg] = (sphere_flux(g, e, d_mm), e[0], g[-1], d_mm)
        if "bare" in flux and "optic" in flux:
            eta = flux["optic"][0] / flux["bare"][0]
            etas.append(eta)
            print(f"  pass {p}: Phi_bare = 2 pi D^2 Int E sin = {flux['bare'][0]:.4g}, Phi_optic = {flux['optic'][0]:.4g} "
                  f"(D {flux['bare'][3]:.1f} mm, scans to {flux['bare'][2]:.0f} / {flux['optic'][2]:.0f} deg) -> eta {eta:.3f}; "
                  f"on-axis gain {flux['optic'][1] / flux['bare'][1]:.1f} (40.5 eta = {40.5 * eta:.1f} if far field, EST)")
    if etas:
        m = sum(etas) / len(etas)
        print(f"  eta = mean of {len(etas)} passes = {m:.3f} (range {min(etas):.3f} to {max(etas):.3f}); "
              f"{'PASS' if m >= ETA_MIN else 'FAIL: stop and report'} against >= {ETA_MIN} (EST)")
        e_img = 21 * 210 * m / (140 * 68.04 / 100)
        print(f"  C21 mean on the image (EST, typ flux, lossless walls, before T_LCD): 21 x 210 mW x {m:.3f} / 95.26 cm^2 "
              f"= {e_img:.1f} mW/cm^2 (L1.3's 50-80 % capture gave 23.1-37.0)")
    else:
        m = None
        print("  no TUV7 readings yet")

    print("\n== T-UV-6: FWHM vs holder height (half-max angles; 12 in ranks the heights, 12 and 18 in give the far field)")
    g6 = groups(rows, "TUV6H")
    fw = {}                                                      # (shim, axis, D_in) -> FWHM at that distance, deg
    for (p, c, ax, d, sh, led), (a, v, dk) in g6.items():
        lft, rgt, _, _ = half_max(a, v)
        if lft is not None and rgt is not None:
            fw[(sh, ax, d)] = rgt - lft
    shims = sorted({k[0] for k in fw})
    for sh in shims:
        txt = ", ".join(f"{ax} {fw[(sh, ax, d)]:.2f} deg at {d:.0f} in" for ax in ("x", "y") for d in (12.0, 18.0)
                        if (sh, ax, d) in fw)
        print(f"  shim {sh:.2f} mm ({sh / INCH:.3f} in): {txt}")
    best = None
    rank = [(fw[(sh, "x", 12.0)], sh) for sh in shims if (sh, "x", 12.0) in fw]
    if rank:
        best = min(rank)[1]
        print(f"  narrowest at 12 in (x): shim {best:.2f} mm ({best / INCH:.3f} in) above seated -> set height")
        d1, d2 = 12 * INCH, 18 * INCH
        for ax in ("x", "y"):
            if (best, ax, 12.0) in fw and (best, ax, 18.0) in fw:
                p1, p2 = math.radians(fw[(best, ax, 12.0)] / 2), math.radians(fw[(best, ax, 18.0)] / 2)
                th = math.degrees(math.atan((d2 * math.tan(p2) - d1 * math.tan(p1)) / (d2 - d1)))
                print(f"  far field, {ax}: tan(theta) = ({d2:.1f} tan {math.degrees(p2):.2f} - {d1:.1f} tan {math.degrees(p1):.2f}) "
                      f"/ {d2 - d1:.1f} -> FWHM {2 * th:.2f} deg")
    else:
        print("  no TUV6H readings yet")

    print("\n== T-UV-6: full profile at the set height (12 in): tails and the edge at the resist")
    gp = groups(rows, "TUV6P")
    prof = {}
    for (p, c, ax, d, s_, led), (a, v, dk) in gp.items():
        prof[ax] = fold(a, v, log=True)
    hw = {}
    if "x" in prof and "y" in prof:
        for ax in ("x", "y"):
            g, e, c0 = prof[ax]
            sym_a = [-x for x in g[::-1]] + g[1:]          # unfold to -max..max for the half-max
            sym_v = e[::-1] + e[1:]
            lft, rgt, _, _ = half_max(sym_a, sym_v)
            fw = rgt - lft
            print(f"  {ax}: FWHM {fw:.2f} deg; flux outside 7.5 deg {frac_outside(g, e, 7.5):.1%}, outside 15 deg "
                  f"{frac_outside(g, e, 15):.1%} (Gaussian of that FWHM: {math.exp(-(7.5 / (fw / F2S)) ** 2 / 2):.1%}, "
                  f"{math.exp(-(15 / (fw / F2S)) ** 2 / 2):.1%})")
            hw[ax] = fw
        for t in t_list:
            hx = edge_halfwidth(prof["x"][0], prof["x"][1], prof["y"][0], prof["y"][1], t, "x")
            hy = edge_halfwidth(prof["x"][0], prof["x"][1], prof["y"][0], prof["y"][1], t, "y")
            gx = gaussian_halfwidth(hw["x"], t)
            print(f"  t {t / INCH:.4f} in ({t:.3f} mm): 10-90 % half-width {hx:.2f} mil (edges across x), {hy:.2f} mil (across y); "
                  f"Gaussian of the x FWHM {gx:.2f} mil; budget {BUDGET} mil (REQ-008) -> {'holds' if max(hx, hy) <= BUDGET else 'over'}")
    else:
        print("  no TUV6P readings yet")

    print("\n== T-UV-6: pointing of all 9 (12 in)")
    gq = groups(rows, "POINT")
    tilts = {}
    for ax in ("x", "y"):
        found = {}
        for (p, c, a_, d, s_, led), (a, v, dk) in gq.items():
            if a_ != ax:
                continue
            if ax in prof:
                found[led] = (fit_centre(a, v, prof[ax][0], prof[ax][1]), d * INCH)
            else:
                lft, rgt, _, _ = half_max(a, v)
                if lft is None or rgt is None:
                    continue
                found[led] = ((lft + rgt) / 2, d * INCH)
        if not found:
            continue
        zero = found.get(5, (0.0, 0.0))[0]              # center LED defines the dial zero
        best_s = None
        for sign in (1, -1):
            dl = {}
            for led, (pc, d_mm) in found.items():
                col, row = (led - 1) % 3, (led - 1) // 3
                s = sign * PITCH[ax][col if ax == "x" else row]
                dl[led] = pointing(pc - zero, s, d_mm) - pointing(0.0, 0.0, d_mm)
            rms = math.sqrt(sum(x * x for x in dl.values()) / len(dl))
            if best_s is None or rms < best_s[0]:
                best_s = (rms, sign, dl)
        rms, sign, dl = best_s
        tilts[ax] = dl
        spread = max(dl.values()) - min(dl.values())
        print(f"  {ax}: tilt per LED (deg, relative to LED 5) " + ", ".join(f"{k}:{dl[k]:+.2f}" for k in sorted(dl))
              + f"; spread {spread:.2f} deg, RMS {rms:.2f} (s sign {'+' if sign > 0 else '-'})")
        if truth:
            err = max(abs(dl[k] - (truth[(k, ax)] - truth[(5, ax)])) for k in dl)
            print(f"     self-test: largest error against the planted tilts {err:.3f} deg")
    if not tilts:
        print("  no POINT readings yet")

    print("\n== C21 or C28, and the build optics")
    if m is None or not hw:
        print("  waits on T-UV-7 and the T-UV-6 profile")
        return
    worst = {t: max(edge_halfwidth(prof["x"][0], prof["x"][1], prof["y"][0], prof["y"][1], t, ax) for ax in ("x", "y"))
             for t in t_list}
    ok = {t: worst[t] <= BUDGET for t in t_list}
    if m < ETA_MIN:
        print(f"  eta {m:.3f} < {ETA_MIN}: stop, report (UV-absorbing grade or a poor fit on the 3528)")
    elif all(ok.values()):
        print("  C21: the 20XPS holds REQ-008 at " + " and ".join(f"t {t:.3f} mm ({worst[t]:.2f} mil)" for t in t_list))
    elif any(ok.values()):
        print("  C21 if T-LCD-4's t lands thin: " + "; ".join(f"t {t:.3f} mm {worst[t]:.2f} mil {'ok' if ok[t] else 'over'}"
                                                             for t in t_list))
    else:
        print("  over 2.5 mil at every t: C21 fails on smear with this optic; C28 or a narrower optic (calc §6c)")
    n_buy = 21 + 4 - 9
    print(f"  build optics for C21: 21 + 4 spares - 9 reusable test optics = {n_buy}; LEDSupply listing seen 2026-11-17: "
          f"$1.69 each (sale; $1.94 regular), 2.5 % off at 10-99 -> {n_buy} x 1.69 x 0.975 = ${n_buy * 1.69 * 0.975:.2f} "
          f"before shipping (EST: confirm at order)")


def skeleton(path):
    """write the readings sheet: every planned dial angle in bench order; fill only the reading column"""
    rows = []

    def scan(test, p, cfg, ax, d_in, shim, led, plan, centre=0.0, note=""):
        rows.append([test, p, cfg, ax, d_in, shim, led, "", "", "mV", "dark", "UV off " + note])
        for a in plan:
            dial = round((centre + a) * 2) / 2                      # the scale reads to 0.5 deg
            rows.append([test, p, cfg, ax, d_in, shim, led, f"{dial:g}", "", "mV", "scan", note])

    # session A: T-UV-7 at 4 in, RL fixed for the whole session
    for p in (1, 2, 3):
        axes = ("x", "y") if p == 1 else ("x",)
        for ax in axes:
            scan("TUV7", p, "bare", ax, 4, 0, 5, PLAN_BARE, note="holder off; string 2 on")
            scan("TUV7", p, "optic", ax, 4, 0, 5, PLAN_T7, note="optic on D5, blanks on D4 D6")
    # session B: T-UV-6 at the set height
    for shim in (0, 0.25, 0.5, 0.75):
        scan("TUV6H", 1, "optic", "x", 12, shim, 5, PLAN_6H, note=f"shims {shim} mm")
    for ax, d in (("x", 18), ("y", 12), ("y", 18)):
        scan("TUV6H", 1, "optic", ax, d, "", 5, PLAN_6H, note="set height (blank shim)")
    for ax in ("x", "y"):
        scan("TUV6P", 1, "optic", ax, 12, "", 5, PLAN_6P, note="set height, full profile")
    for ax in ("x", "y"):
        for led in range(1, 10):
            col, row = (led - 1) % 3, (led - 1) // 3
            sk = PITCH[ax][col if ax == "x" else row]
            expect = -math.degrees(math.atan(sk / (12 * INCH)))
            scan("POINT", 1, "optic", ax, 12, "", led, PLAN_PT, centre=expect,
                 note=f"D{led} alone: its optic on, blanks on its row-mates")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(rows)
    n = sum(1 for r in rows if r[10] == "scan")
    print(f"wrote {path}: {n} readings + {len(rows) - n} dark readings, in bench order")


def main():
    if "--skeleton" in sys.argv:
        skeleton(CSV)
        return
    if "--selftest" in sys.argv or not load(CSV):
        if "--selftest" not in sys.argv:
            print("(no readings in calcs/l1_11_optic_readings.csv yet: running the self-test on synthetic data)\n")
        print("== Self-test of the edge metric against calc §5: a Gaussian of FWHM 15 deg, no tails")
        sc = 15 / F2S
        g = [i * 0.25 for i in range(161)]
        e = [math.exp(-x * x / (2 * sc * sc)) for x in g]
        for t in T_LIST:
            print(f"  t {t:.3f} mm: 2D rebuild {edge_halfwidth(g, e, g, e, t):.3f} mil; calc §5 closed form "
                  f"1.2816 x {mil(t):.2f} x tan(asin(sin {sc:.2f}/1.5)) = {gaussian_halfwidth(15, t):.3f} mil")
        rows, truth = synth()
        print("\n== Self-test on synthetic scans (planted: eta 0.85, far-field FWHM 15 deg core + 3 % at 50 deg, "
              "narrowest at shim 0.50 mm, random tilts; readings per plan: bare "
              f"{len(PLAN_BARE)}, optic {len(PLAN_T7)}, height {len(PLAN_6H)}, profile {len(PLAN_6P)}, pointing {len(PLAN_PT)})")
        print("   Interpolation bias on eta, checked separately on these plans: optic -0.04 % (log-linear), "
              "bare -0.07 % (linear, 5 deg steps), so eta +0.03 %\n")
        analyse(rows, truth=truth)
        return
    analyse(load(CSV))


if __name__ == "__main__":
    main()
