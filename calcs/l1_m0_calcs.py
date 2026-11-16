# L1: M0 numbers behind rev 1 and rev 2 (PMMA chromatic focal shift EST, lamp-method f correction, image half-dims, boost dummy-load CC/CV check, package half-angle, p.80/p.81 currents vs IBT ratings). Run: python3 calcs/l1_m0_calcs.py
import math
# 1. Chromatic focal shift, PMMA, two-term Cauchy from nd and Vd (EST)
lF, lC, ld = 0.4861, 0.6563, 0.5876   # um
for Vd in (58.0, 55.0):
    nd = 1.49
    dFC = (nd-1)/Vd
    B = dFC/(1/lF**2 - 1/lC**2)
    A = nd - B/ld**2
    n405 = A + B/0.405**2
    n550 = A + B/0.550**2
    ratio = (n550-1)/(n405-1)
    print(f"Vd={Vd}: nF-nC={dFC:.5f} B={B:.5f} A={A:.5f} n405={n405:.5f} n550={n550:.5f} f405/f550={ratio:.4f} ({(ratio-1)*100:.2f}%)")
    for fv in (6, 8, 10, 12):
        print(f"   f_vis {fv} in -> f_405 {fv*ratio:.3f} in, shift {fv*(1-ratio):.3f} in")
# 2. Lamp method
for so in (180, 240, 600):
    f = 8.0
    si = 1/(1/f - 1/so)
    print(f"lamp at {so} in, true f 8 in: image at {si:.3f} in (+{si-f:.3f}); f = so*si/(so+si) = {so*si/(so+si):.3f}")
# 3. Image rectangle from the ring center
W, H = 4.762, 2.679
print("half W", W/2, "half H", H/2, "half diag", math.hypot(W, H)/2)
# 4. Dummy load
print("CV 26V on 24R:", 26/24, "A", 26**2/24, "W")
print("CC 0.91A on 24R:", 0.91*24, "V", 0.91**2*24, "W")
print("CC 1.00A on 24R:", 1.00*24, "V", 1.00**2*24, "W")
# 5. Half-angle bound, IBT 6.8 mm package vs p.80 readings, f = 6 in
for w_mm in (6.8, 6.86, 6.96):
    w_in = w_mm/25.4
    print(f"pkg {w_mm} mm = {w_in:.4f} in: atan({w_in/2:.4f}/6) = {math.degrees(math.atan(w_in/2/6)):.3f} deg")
# 6. p.80 operating points vs IBT rows
print("p.81 per module:", 25.7/4, "V at 0.91 A ->", 25.7*0.91/4, "W")
print("p.80 per module: 6.6 V at", 4.5/4, "A ->", 6.6*4.5/4, "W")
print("2.4 A x 7.2 V =", 2.4*7.2, "W; 2.4 x 7.4 =", 2.4*7.4)
print("0.91/1.4 =", 0.91/1.4, " 0.91/2.4 =", 0.91/2.4, " 1.125/1.4 =", 1.125/1.4, " 1.125/2.4 =", 1.125/2.4)
