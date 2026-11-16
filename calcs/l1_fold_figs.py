# L1: L1.3 figures for the fold question (2026-11-16). Draws, to scale, (1) A tower vs A folded vs C side views and (2) folded A side and top views, from the same geometry as calcs/l1_buy_checks.py (fold section, uncut 156 x 102 mm mirror). Writes two SVG fragments for the chat widget (host CSS classes). Run: python3 calcs/l1_fold_figs.py OUT_DIR
import math
import os
import sys

MM = 25.4
R_SRC, P, A_HALF, B_HALF, CLR = 11.19, 0.975 * 260.0, 2.8 * MM / 2, 4.9 * MM / 2, 0.2 * MM
WALL, SINK, BASE, HOLDER = 0.12 * MM, 1.25 * MM, 0.12 * MM, 0.12 * MM
T_FRES, GAP, T_LCDF = 0.08 * MM, 0.4 * MM, 0.24 * MM          # LCD + frame = T_LCD + T_COVER
MIR_FACE, MIR_ACROSS, MIR_T = 102.0, 156.0, 2.0                # mm, uncut mirror
IMG_X, IMG_Y = 68.04, 120.96                                   # image short side along the fold

# fold geometry (see l1_buy_checks.py): q, L_h, hits, L_v
q = (A_HALF - R_SRC) / P
L_H = (P - CLR) * (1 - q) - R_SRC
K = R_SRC + q * L_H
U_TOP, U_BOT = K / (1 - q), -K / (1 + q)
L_V = U_TOP + CLR

# side-view coordinates, mm, origin at the box's outer bottom-left
LED_X = WALL + SINK
XM = LED_X + L_H                                   # mirror center x
MIR_BOT_Z = BASE + HOLDER                          # uncut mirror's bottom edge sits on the holder
ZM = MIR_BOT_Z + MIR_FACE / math.sqrt(2) - U_TOP   # beam axis height: mirror top edge at u_top
Z_F = ZM + L_V                                     # Fresnel underside
Z_LCD = Z_F + T_FRES + GAP
H_BOX = Z_LCD + T_LCDF
L_BOX = LED_X + L_H + A_HALF + CLR + WALL
W_BOX = (MIR_ACROSS + 2.0) + 2 * WALL


def y_env(s):
    return R_SRC * (1 - s / P) + B_HALF * s / P


AMB, AMB_D, TEAL, TEAL_D, GRAY_D = "#EF9F27", "#BA7517", "#1D9E75", "#0F6E56", "#888780"
DEFS = ('<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
        'orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round"/></marker></defs>')


def f(v):
    return f"{v:.1f}"


class View:
    def __init__(self, x0, y_floor, s):
        self.x0, self.yf, self.s = x0, y_floor, s

    def X(self, x):
        return self.x0 + x * self.s

    def Y(self, z):
        return self.yf - z * self.s

    def pts(self, ps):
        return " ".join(f"{f(self.X(x))},{f(self.Y(z))}" for x, z in ps)

    def rect(self, x1, z1, x2, z2, cls=None, extra=""):
        c = f' class="{cls}"' if cls else ""
        return (f'<rect{c} x="{f(self.X(x1))}" y="{f(self.Y(z2))}" width="{f((x2-x1)*self.s)}" '
                f'height="{f((z2-z1)*self.s)}" {extra}/>')

    def poly(self, ps, extra):
        return f'<polygon points="{self.pts(ps)}" {extra}/>'

    def line(self, ps, extra):
        return f'<polyline points="{self.pts(ps)}" fill="none" {extra}/>'


def folded_side(v, labels):
    o = []
    o.append(v.rect(0, 0, L_BOX, H_BOX, extra='fill="none" stroke="var(--s)" stroke-width="1"'))
    o.append(v.rect(WALL, ZM - 25, LED_X - 1.6, ZM + 25, "c-gray", 'rx="2" stroke-width="0.5"'))
    o.append(v.rect(LED_X - 1.6, ZM - 15, LED_X, ZM + 15, "c-gray", 'stroke-width="0.5"'))
    top_hit = (XM + U_TOP, ZM + U_TOP)
    bot_hit = (XM + U_BOT, ZM + U_BOT)
    o.append(v.poly([(LED_X, ZM + R_SRC), top_hit, bot_hit, (LED_X, ZM - R_SRC)],
                    f'fill="{AMB}" fill-opacity="0.28"'))
    o.append(v.poly([bot_hit, top_hit, (XM + A_HALF, Z_F), (XM - A_HALF, Z_F)],
                    f'fill="{AMB}" fill-opacity="0.32"'))
    o.append(v.rect(XM - A_HALF, Z_F + T_FRES, XM + A_HALF, Z_LCD, extra=f'fill="{AMB}" fill-opacity="0.45"'))
    o.append(v.rect(LED_X, ZM - R_SRC, LED_X + 1.6, ZM + R_SRC, extra=f'fill="{AMB_D}"'))
    u0, u1 = U_TOP - MIR_FACE / math.sqrt(2), U_TOP
    d = MIR_T / math.sqrt(2)
    o.append(v.poly([(XM + u0, ZM + u0), (XM + u1, ZM + u1), (XM + u1 + d, ZM + u1 - d), (XM + u0 + d, ZM + u0 - d)],
                    f'fill="{TEAL}" fill-opacity="0.35" stroke="{TEAL}" stroke-width="1.5"'))
    o.append(v.rect(XM - A_HALF - CLR, Z_F, XM + A_HALF + CLR, Z_F + T_FRES, "c-teal", 'stroke-width="0.5"'))
    o.append(v.rect(XM - IMG_X / 2 - 4, Z_LCD, XM + IMG_X / 2 + 4, H_BOX, "c-teal", 'stroke-width="0.5"'))
    if labels:
        # black baffles: upper hugs the beam's top edge 3 mm clear and drops to the Fresnel frame (stray-light stop)
        slope_t = (top_hit[1] - (ZM + R_SRC)) / (top_hit[0] - LED_X)
        x_fin = XM - A_HALF - 3.0
        z_fin = ZM + R_SRC + slope_t * (x_fin - LED_X) + 2.5
        o.append(v.line([(LED_X + 1.6, ZM + R_SRC + 3), (x_fin, z_fin), (x_fin, Z_F)],
                        f'stroke="{GRAY_D}" stroke-width="2.5" stroke-linejoin="round"'))
        slope_b = (bot_hit[1] - (ZM - R_SRC)) / (bot_hit[0] - LED_X)
        # lower baffle 3 mm under the beam's bottom edge until it meets the mirror face
        x_b = ((ZM - R_SRC - 3) - slope_b * LED_X - (ZM - XM)) / (1 - slope_b)
        o.append(v.line([(LED_X + 1.6, ZM - R_SRC - 3), (x_b, x_b + ZM - XM)],
                        f'stroke="{GRAY_D}" stroke-width="2.5"'))
        o.append(f'<polyline points="{v.pts([(LED_X + 2, ZM), (XM, ZM), (XM, Z_F - 2)])}" fill="none" '
                 f'stroke="{AMB_D}" stroke-width="1" stroke-dasharray="4 3" marker-end="url(#arrow)"/>')
    return o, (top_hit, bot_hit)


def fig_fold():
    s = 42 / MM
    v = View(28, 214, s)
    o = [f'<svg width="100%" viewBox="0 0 680 562" role="img"><title>Folded light engine A, side and top views to scale</title>'
         f'<desc>A 45 degree first-surface mirror under the Fresnel turns the 10 inch light path sideways: '
         f'8.4 inches horizontal plus 1.6 inches up. Box about 11.5 by 6.5 by 4.0 inches.</desc>', DEFS]
    o.append(f'<text class="ts" x="28" y="26">Side view</text>')
    side, (top_hit, bot_hit) = folded_side(v, True)
    o += side
    # labels inside
    o.append(f'<text class="ts" x="{f(v.X((LED_X + XM) / 2 - 14))}" y="{f(v.Y(ZM + 8.4))}" text-anchor="middle" dominant-baseline="central">{L_H/MM:.1f} in</text>')
    o.append(f'<text class="ts" x="{f(v.X(XM - 5.2))}" y="{f(v.Y(ZM + 23))}" text-anchor="end" dominant-baseline="central">{L_V/MM:.1f} in</text>')
    o.append(f'<text class="ts" x="{f(v.X(120))}" y="{f(v.Y(84))}" text-anchor="middle" dominant-baseline="central">controller bay</text>')
    o.append(f'<text class="ts" x="{f(v.X(95))}" y="{f(v.Y(12))}" text-anchor="middle" dominant-baseline="central">driver bay</text>')
    # right-margin labels
    xl = v.X(L_BOX) + 14
    lcd_y = v.Y(Z_LCD + T_LCDF / 2)
    o.append(f'<line class="leader" x1="{f(v.X(XM + IMG_X/2 + 4))}" y1="{f(lcd_y)}" x2="{f(xl - 4)}" y2="{f(lcd_y)}"/>')
    o.append(f'<text class="ts" x="{f(xl)}" y="{f(lcd_y)}" dominant-baseline="central">LCD + platen</text>')
    fy = v.Y(Z_F + T_FRES / 2)
    o.append(f'<line class="leader" x1="{f(v.X(XM + A_HALF + CLR))}" y1="{f(fy)}" x2="{f(xl - 4)}" y2="{f(fy + 10)}"/>')
    o.append(f'<text class="ts" x="{f(xl)}" y="{f(fy + 10)}" dominant-baseline="central">Fresnel, trimmed</text>')
    mpx, mpy = v.X(XM + 10), v.Y(ZM + 10)
    o.append(f'<line class="leader" x1="{f(mpx)}" y1="{f(mpy)}" x2="{f(xl - 4)}" y2="{f(mpy + 16)}"/>')
    o.append(f'<text class="ts" x="{f(xl)}" y="{f(mpy + 16)}" dominant-baseline="central">45° mirror,</text>')
    o.append(f'<text class="ts" x="{f(xl)}" y="{f(mpy + 32)}" dominant-baseline="central">first-surface</text>')
    # below: LED label and overall size
    hx = v.X(WALL + 12)
    o.append(f'<line class="leader" x1="{f(hx)}" y1="{f(v.Y(ZM - 25))}" x2="{f(hx)}" y2="{f(v.yf + 14)}"/>')
    o.append(f'<text class="ts" x="28" y="{f(v.yf + 24)}" dominant-baseline="central">LED cluster + heatsink</text>')
    o.append(f'<text class="ts" x="{f(v.X(L_BOX) - 60)}" y="{f(v.yf + 24)}" text-anchor="middle" dominant-baseline="central">'
             f'{L_BOX/MM:.1f} x {W_BOX/MM:.1f} x {H_BOX/MM:.1f} in tall (EST)</text>')
    # top view
    t0 = 270
    o.append(f'<text class="ts" x="28" y="{t0 - 12}">Top view</text>')
    tv = View(28, t0, s)

    def T(x, y):
        return f"{f(tv.X(x))},{f(t0 + y * s)}"

    yc = W_BOX / 2
    o.append(f'<rect x="{f(tv.X(0))}" y="{f(t0)}" width="{f(L_BOX*s)}" height="{f(W_BOX*s)}" fill="none" stroke="var(--s)" stroke-width="1"/>')
    o.append(f'<rect class="c-gray" x="{f(tv.X(WALL))}" y="{f(t0 + (yc-25)*s)}" width="{f((SINK-1.6)*s)}" height="{f(50*s)}" rx="2" stroke-width="0.5"/>')
    w_far = y_env(L_H + U_TOP)
    o.append(f'<polygon points="{T(LED_X, yc - R_SRC)} {T(XM + U_TOP, yc - w_far)} {T(XM + U_TOP, yc + w_far)} {T(LED_X, yc + R_SRC)}" '
             f'fill="{AMB}" fill-opacity="0.28"/>')
    o.append(f'<rect x="{f(tv.X(LED_X))}" y="{f(t0 + (yc - R_SRC)*s)}" width="{f(1.6*s)}" height="{f(2*R_SRC*s)}" fill="{AMB_D}"/>')
    u0 = U_TOP - MIR_FACE / math.sqrt(2)
    o.append(f'<rect x="{f(tv.X(XM + u0))}" y="{f(t0 + (yc - MIR_ACROSS/2)*s)}" width="{f((MIR_FACE/math.sqrt(2) + MIR_T/math.sqrt(2))*s)}" '
             f'height="{f(MIR_ACROSS*s)}" fill="none" stroke="{TEAL}" stroke-width="1" stroke-dasharray="4 3"/>')
    o.append(f'<rect class="c-teal" x="{f(tv.X(XM - IMG_X/2))}" y="{f(t0 + (yc - IMG_Y/2)*s)}" width="{f(IMG_X*s)}" height="{f(IMG_Y*s)}" '
             f'fill-opacity="0.55" stroke-width="0.5"/>')
    px1, px2 = XM - 4.5 * MM / 2, XM + 4.5 * MM / 2
    o.append(f'<rect x="{f(tv.X(px1))}" y="{f(t0 + (yc - 3*MM)*s)}" width="{f(4.5*MM*s)}" height="{f(6*MM*s)}" fill="none" '
             f'stroke="var(--s)" stroke-width="1" stroke-dasharray="5 3"/>')
    xl2 = tv.X(px2) + 12
    py = t0 + (yc - 3 * MM) * s + 16
    o.append(f'<line class="leader" x1="{f(tv.X(px2))}" y1="{f(py)}" x2="{f(xl2 - 4)}" y2="{f(py)}"/>')
    o.append(f'<text class="ts" x="{f(xl2)}" y="{f(py)}" dominant-baseline="central">4.5 x 6 in panel</text>')
    ly = t0 + yc * s
    o.append(f'<line class="leader" x1="{f(tv.X(XM + IMG_X/2))}" y1="{f(ly)}" x2="{f(xl2 - 4)}" y2="{f(ly)}"/>')
    o.append(f'<text class="ts" x="{f(xl2)}" y="{f(ly)}" dominant-baseline="central">LCD image area</text>')
    my0 = t0 + (yc + MIR_ACROSS / 2 - 3) * s
    o.append(f'<line class="leader" x1="{f(tv.X(XM + 2))}" y1="{f(my0)}" x2="{f(xl2 - 4)}" y2="{f(my0 - 14)}"/>')
    o.append(f'<text class="ts" x="{f(xl2)}" y="{f(my0 - 14)}" dominant-baseline="central">mirror (below)</text>')
    o.append('</svg>')
    return "\n".join(o)


def fig_compare():
    s = 22 / MM
    yb = 292
    o = [f'<svg width="100%" viewBox="0 0 680 356" role="img"><title>Three light engines at the same scale</title>'
         f'<desc>A as a tower is about 12.1 inches tall; A folded with one mirror is about 4.0 inches tall and 11.5 inches long; '
         f'C, the lens matrix, is about 4.5 inches tall.</desc>', DEFS]
    o.append(f'<line x1="36" y1="{yb}" x2="644" y2="{yb}" stroke="var(--b)" stroke-width="0.5"/>')
    # tower A
    wt, ht = 4.5 * MM + 2 * WALL, BASE + SINK + P + T_FRES + GAP + T_LCDF
    v = View(50, yb, s)
    c = wt / 2
    o.append(v.rect(0, 0, wt, ht, extra='fill="none" stroke="var(--s)" stroke-width="1"'))
    o.append(v.rect(c - 25, BASE, c + 25, BASE + SINK, "c-gray", 'stroke-width="0.5"'))
    z0 = BASE + SINK
    o.append(v.poly([(c - R_SRC, z0), (c + R_SRC, z0), (c + A_HALF, z0 + P), (c - A_HALF, z0 + P)], f'fill="{AMB}" fill-opacity="0.3"'))
    o.append(v.rect(c - R_SRC, z0, c + R_SRC, z0 + 2, extra=f'fill="{AMB_D}"'))
    o.append(v.rect(c - A_HALF - CLR, z0 + P, c + A_HALF + CLR, z0 + P + T_FRES, "c-teal", 'stroke-width="0.5"'))
    o.append(v.rect(c - A_HALF, z0 + P + T_FRES, c + A_HALF, z0 + P + T_FRES + GAP, extra=f'fill="{AMB}" fill-opacity="0.45"'))
    o.append(v.rect(c - IMG_X / 2 - 4, ht - T_LCDF, c + IMG_X / 2 + 4, ht, "c-teal", 'stroke-width="0.5"'))
    o.append(f'<text class="th" x="{f(v.X(c))}" y="{yb + 20}" text-anchor="middle" dominant-baseline="central">A tower</text>')
    o.append(f'<text class="ts" x="{f(v.X(c))}" y="{yb + 40}" text-anchor="middle" dominant-baseline="central">{ht/MM:.1f} in tall</text>')
    # folded A
    v2 = View(50 + wt * s + 40, yb, s)
    side, _ = folded_side(v2, False)
    o += side
    cx2 = v2.X(L_BOX / 2)
    o.append(f'<text class="th" x="{f(cx2)}" y="{yb + 20}" text-anchor="middle" dominant-baseline="central">A folded</text>')
    o.append(f'<text class="ts" x="{f(cx2)}" y="{yb + 40}" text-anchor="middle" dominant-baseline="central">{H_BOX/MM:.1f} in tall, {L_BOX/MM:.1f} in long</text>')
    # C, 3 x 7 TIR at 15 deg
    v3 = View(v2.X(L_BOX) + 40, yb, s)
    row = IMG_X / 3
    gap15 = row / (2 * math.tan(math.radians(7.5)))
    plate, board, optic = 0.25 * MM, 1.6, 0.45 * MM
    hc = BASE + plate + board + optic + gap15 + T_LCDF
    c3 = wt / 2
    o.append(v3.rect(0, 0, wt, hc, extra='fill="none" stroke="var(--s)" stroke-width="1"'))
    o.append(v3.rect(c3 - 40, BASE, c3 + 40, BASE + plate + board, "c-gray", 'stroke-width="0.5"'))
    zo = BASE + plate + board
    for k in (-1, 0, 1):
        xc = c3 + k * row
        o.append(v3.poly([(xc - 10, zo + optic), (xc + 10, zo + optic), (xc + 3, zo), (xc - 3, zo)],
                         f'fill="{TEAL}" fill-opacity="0.35" stroke="{TEAL}" stroke-width="0.8"'))
        spread = 10 + gap15 * math.tan(math.radians(7.5))
        o.append(v3.poly([(xc - 10, zo + optic), (xc + 10, zo + optic), (xc + spread, zo + optic + gap15), (xc - spread, zo + optic + gap15)],
                         f'fill="{AMB}" fill-opacity="0.22"'))
        o.append(v3.rect(xc - 2, zo, xc + 2, zo + 1.5, extra=f'fill="{AMB_D}"'))
    o.append(v3.rect(c3 - IMG_X / 2 - 4, hc - T_LCDF, c3 + IMG_X / 2 + 4, hc, "c-teal", 'stroke-width="0.5"'))
    o.append(f'<text class="th" x="{f(v3.X(c3))}" y="{yb + 20}" text-anchor="middle" dominant-baseline="central">C, lens matrix</text>')
    o.append(f'<text class="ts" x="{f(v3.X(c3))}" y="{yb + 40}" text-anchor="middle" dominant-baseline="central">{hc/MM:.1f} in tall</text>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    print(f"L_H {L_H:.2f}, L_V {L_V:.2f}, ZM {ZM:.2f}, Z_F {Z_F:.2f}, H {H_BOX/MM:.2f} in, L {L_BOX/MM:.2f} in, W {W_BOX/MM:.2f} in")
    open(os.path.join(out, "fig_compare.svg"), "w").write(fig_compare())
    open(os.path.join(out, "fig_fold.svg"), "w").write(fig_fold())
