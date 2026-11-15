"""Geometry primitives (mm) and affine transforms.

A Layer is an ordered list of primitives. Dark primitives add material (lit pixels with the
default copper-lit polarity); clear primitives remove it (Gerber LPC). Order matters.
"""
import math
from dataclasses import dataclass, replace


@dataclass
class Track:
    """Straight segment with round caps. w = full width. snap=False for arcs and text (R4)."""
    p0: tuple
    p1: tuple
    w: float
    dark: bool = True
    snap: bool = True


@dataclass
class Flash:
    """Pad at centre c. shape: 'circle' (w = diameter), 'rect' or 'obround' (w along x, h along y)."""
    c: tuple
    shape: str
    w: float
    h: float = None
    dark: bool = True

    def __post_init__(self):
        if self.h is None:
            self.h = self.w


@dataclass
class Region:
    """Filled polygon(s), nonzero winding. rings: list of closed point lists."""
    rings: list
    dark: bool = True


class Layer(list):
    """Ordered list of primitives."""

    def add(self, *prims):
        for p in prims:
            if isinstance(p, (list, tuple)) and not isinstance(p, (Track, Flash, Region)):
                self.extend(p)
            else:
                self.append(p)
        return self


# ---------------------------------------------------------------- affine transforms

class Affine:
    """x' = a x + b y + tx ; y' = c x + d y + ty"""

    def __init__(self, a=1.0, b=0.0, c=0.0, d=1.0, tx=0.0, ty=0.0):
        self.a, self.b, self.c, self.d, self.tx, self.ty = a, b, c, d, tx, ty

    def __matmul__(self, o):
        """self @ o = apply o first, then self."""
        return Affine(
            self.a * o.a + self.b * o.c, self.a * o.b + self.b * o.d,
            self.c * o.a + self.d * o.c, self.c * o.b + self.d * o.d,
            self.a * o.tx + self.b * o.ty + self.tx, self.c * o.tx + self.d * o.ty + self.ty)

    def __call__(self, p):
        x, y = p
        return (self.a * x + self.b * y + self.tx, self.c * x + self.d * y + self.ty)

    @staticmethod
    def translate(tx, ty):
        return Affine(tx=tx, ty=ty)

    @staticmethod
    def rotate_deg(deg):
        r = math.radians(deg)
        q = deg % 360
        if q in (0, 90, 180, 270):  # exact for lattice rotations
            c, s = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[q]
        else:
            c, s = math.cos(r), math.sin(r)
        return Affine(c, -s, s, c)

    @staticmethod
    def mirror_x():
        """x -> -x (mirror about the y axis)"""
        return Affine(a=-1.0)

    @staticmethod
    def mirror_y():
        """y -> -y (mirror about the x axis)"""
        return Affine(d=-1.0)

    def axis_kind(self, tol=1e-12):
        """'keep' if x stays x, 'swap' if x and y exchange, else None."""
        if abs(self.b) < tol and abs(self.c) < tol:
            return "keep"
        if abs(self.a) < tol and abs(self.d) < tol:
            return "swap"
        return None


def rect_ring(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
            (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def circle_ring(cx, cy, d, seg=64):
    r = d / 2
    return [(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg))
            for k in range(seg)]


def flash_as_region(f):
    if f.shape == "circle":
        return Region([circle_ring(f.c[0], f.c[1], f.w)], f.dark)
    if f.shape == "rect":
        return Region([rect_ring(f.c[0], f.c[1], f.w, f.h)], f.dark)
    if f.shape == "obround":
        # stadium: rect plus two half discs
        cx, cy, w, h = f.c[0], f.c[1], f.w, f.h
        r = min(w, h) / 2
        pts = []
        if w >= h:
            for k in range(33):
                t = -math.pi / 2 + math.pi * k / 32
                pts.append((cx + (w / 2 - r) + r * math.cos(t), cy + r * math.sin(t)))
            for k in range(33):
                t = math.pi / 2 + math.pi * k / 32
                pts.append((cx - (w / 2 - r) + r * math.cos(t), cy + r * math.sin(t)))
        else:
            for k in range(33):
                t = math.pi * k / 32
                pts.append((cx + r * math.cos(t), cy + (h / 2 - r) + r * math.sin(t)))
            for k in range(33):
                t = math.pi + math.pi * k / 32
                pts.append((cx + r * math.cos(t), cy - (h / 2 - r) + r * math.sin(t)))
        return Region([pts], f.dark)
    raise ValueError(f.shape)


def transform(layer, T):
    """Apply an affine map to every primitive. Rects stay rects under lattice maps
    (90-degree steps, mirrors); otherwise flashes become regions (rule R2)."""
    out = Layer()
    kind = T.axis_kind()
    for p in layer:
        if isinstance(p, Track):
            out.append(replace(p, p0=T(p.p0), p1=T(p.p1)))
        elif isinstance(p, Flash):
            if p.shape == "circle" or kind == "keep":
                out.append(replace(p, c=T(p.c)))
            elif kind == "swap":
                out.append(replace(p, c=T(p.c), w=p.h, h=p.w))
            else:
                r = flash_as_region(p)
                out.append(Region([[T(q) for q in ring] for ring in r.rings], p.dark))
        elif isinstance(p, Region):
            out.append(Region([[T(q) for q in ring] for ring in p.rings], p.dark))
        else:
            raise TypeError(p)
    return out


def bbox(layer):
    xs, ys = [], []
    for p in layer:
        if isinstance(p, Track):
            r = p.w / 2
            for q in (p.p0, p.p1):
                xs += [q[0] - r, q[0] + r]
                ys += [q[1] - r, q[1] + r]
        elif isinstance(p, Flash):
            xs += [p.c[0] - p.w / 2, p.c[0] + p.w / 2]
            ys += [p.c[1] - p.h / 2, p.c[1] + p.h / 2]
        elif isinstance(p, Region):
            for ring in p.rings:
                xs += [q[0] for q in ring]
                ys += [q[1] for q in ring]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)
