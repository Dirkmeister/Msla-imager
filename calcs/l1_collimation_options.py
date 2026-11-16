# L1: D-06 options at the Fresnel focus, rev 2 (3528 Lambertian cluster vs one 6868: flux on image, corner/center, max source span, 6 x 6 cluster smear and power; reproduces calc §6 flux). Run: python3 calcs/l1_collimation_options.py (needs scipy)
import math
from scipy import integrate

W, H = 4.762, 2.679          # image, in (calc §2)
a, b = W/2, H/2
corner = math.hypot(a, b)
print(f"half dims {a:.4f} x {b:.4f} in, corner r = {corner:.4f} in")

def frac_on_image(m, f):
    """Fraction of a cos^m source's flux whose ray, launched at the lens plane distance f,
    falls inside the image rectangle (collimator maps direction -> position x = f tan).
    Intensity I = I0 cos^m(th), total flux = 2*pi*I0/(m+1)."""
    # integrate over image-plane coords x,y: dOmega = f*dx*dy/R^3, R = sqrt(x^2+y^2+f^2), cos th = f/R
    g = lambda y, x: (f/math.hypot(math.hypot(x, y), f))**m * f/(math.hypot(math.hypot(x, y), f))**3
    val, _ = integrate.dblquad(g, -a, a, lambda x: -b, lambda x: b)
    return val*(m+1)/(2*math.pi)

m60 = -math.log(2)/math.log(math.cos(math.radians(30)))
print(f"m for 60 deg full angle = {m60:.3f}")
print("check vs calc §6 (m=4.82): f, flux on image")
for f in (6, 8, 10, 12):
    print(f"  f {f}: {frac_on_image(m60, f)*100:.1f}%")

print("\n3528, Lambertian m=1, at the Fresnel focus")
for f in (8, 9, 10, 12):
    th = math.atan(corner/f)
    cc = math.cos(th)**4          # cos^(m+3), m=1
    fr = frac_on_image(1, f)
    smax = 2*f*math.tan(math.radians(7.5))
    print(f"  f {f} in: theta_corner {math.degrees(th):.2f} deg, corner/center cos^4 = {cc:.3f}, "
          f"flux on image {fr*100:.2f}%, max source span 2 f tan7.5 = {smax:.2f} in ({smax*25.4:.1f} mm)")
# f needed for corner/center >= 0.84 with m=1
c = 0.84**0.25
th = math.acos(c)
print(f"  0.84 needs cos th >= {c:.4f} -> th <= {math.degrees(th):.2f} deg -> f >= {corner/math.tan(th):.2f} in")

print("\n6 x 6 cluster of 3528 at 0.200 in pitch")
pkg = 3.5/25.4
span = 5*0.2 + pkg
print(f"  span = 5 x 0.200 + {pkg:.4f} = {span:.3f} in ({span*25.4:.1f} mm)")
t = 0.725/25.4*1000   # mil
for f in (9, 10, 12):
    alpha = math.degrees(math.atan(span/2/f))
    inside = math.asin(math.sin(math.radians(alpha))/1.5)
    s = t*math.tan(inside)
    print(f"  f {f}: half-angle atan({span/2:.3f}/{f}) = {alpha:.2f} deg; smear at t 0.725 mm = {t:.2f} mil x tan({math.degrees(inside):.2f}) = {s:.2f} mil")
P_e = 36*3.3*0.180
P_r = 36*0.210
print(f"  electrical 36 x 3.3 V x 0.180 A = {P_e:.2f} W; radiant 36 x 0.210 W = {P_r:.2f} W")
area_cm2 = W*H*6.4516
print(f"  image area {W} x {H} = {W*H:.3f} in2 = {area_cm2:.2f} cm2")
for f in (9, 10, 12):
    fr = frac_on_image(1, f)
    print(f"  f {f}: on image {P_r:.2f} x {fr:.4f} = {P_r*fr:.3f} W -> mean {P_r*fr*1000/area_cm2:.2f} mW/cm2 before the LCD")

print("\nOne bought 6868 (IBT D4 listing: 6.2 W out at 1400 mA, 7 V), m=4.82 assumed")
for f in (10, 12):
    fr = frac_on_image(m60, f)
    th = math.atan(corner/f)
    print(f"  f {f}: on image 6.2 x {fr:.4f} = {6.2*fr:.3f} W -> mean {6.2*fr*1000/area_cm2:.2f} mW/cm2; corner/center cos^(m+3) = {math.cos(th)**(m60+3):.3f}; electrical 1.4 x 7 = {1.4*7:.1f} W")
