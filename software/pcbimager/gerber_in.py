"""Gerber (RS-274X / X2) and Excellon readers -> Layer in KiCad top view (mm, y up).

Mapping to the rounding rule:
  D01 draw with a circular aperture         -> Track (R1, snapped)
  G02/G03 arc with a circular aperture      -> chain of Tracks (R4, width kept, not snapped)
  D03 flash, circle / rect at 0 or 90 deg / obround -> Flash (R1)
  D03 flash, polygon aperture, aperture macro (KiCad roundrect etc.), rotated rect -> Region (R2)
  G36/G37 region                            -> Region (R2)
  LPC (clear polarity)                      -> clear primitives, applied in file order
"""
import math

from gerbonara import GerberFile, ExcellonFile
from gerbonara import graphic_objects as go, apertures as ap, graphic_primitives as gp
from gerbonara.utils import MM

from .geom import Layer, Track, Flash, Region, circle_ring

ARC_TOL_MM = 0.002     # chord error for arcs, well under a pixel (47.25 um)


def _arc_points(x1, y1, x2, y2, cx, cy, cw, tol=ARC_TOL_MM):
    r = math.hypot(x1 - cx, y1 - cy)
    a0 = math.atan2(y1 - cy, x1 - cx)
    a1 = math.atan2(y2 - cy, x2 - cx)
    if cw:
        sweep = a0 - a1
        if sweep <= 0:
            sweep += 2 * math.pi
        sweep = -sweep
    else:
        sweep = a1 - a0
        if sweep <= 0:
            sweep += 2 * math.pi
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        sweep = -2 * math.pi if cw else 2 * math.pi
    if r < 1e-9:
        return [(x1, y1), (x2, y2)]
    step = 2 * math.acos(max(-1.0, 1 - tol / r)) if r > tol else math.pi / 4
    n = max(2, int(math.ceil(abs(sweep) / max(step, 1e-3))) + 1)
    return [(cx + r * math.cos(a0 + sweep * k / (n - 1)), cy + r * math.sin(a0 + sweep * k / (n - 1)))
            for k in range(n)]


def _arcpoly_rings(p):
    """gerbonara ArcPoly -> list of point rings (arcs approximated)."""
    pts = []
    outline = list(p.outline)
    centers = list(p.arc_centers) if p.arc_centers else [None] * len(outline)
    n = len(outline)
    for k in range(n):
        a = outline[k]
        b = outline[(k + 1) % n]
        c = centers[k] if k < len(centers) else None
        if c is None:
            pts.append(tuple(a))
        else:
            cw, (cx, cy) = c
            seg = _arc_points(a[0], a[1], b[0], b[1], cx, cy, cw)
            pts.extend(seg[:-1])
    return [pts] if len(pts) >= 3 else []


def _prims_to_regions(prims):
    out = []
    for q in prims:
        dark = q.polarity_dark
        if isinstance(q, gp.Circle):
            out.append(Region([circle_ring(q.x, q.y, 2 * q.r, 96)], dark))
        elif isinstance(q, gp.Rectangle):
            c, s = math.cos(q.rotation), math.sin(q.rotation)
            ring = []
            for dx, dy in ((-q.w / 2, -q.h / 2), (q.w / 2, -q.h / 2), (q.w / 2, q.h / 2), (-q.w / 2, q.h / 2)):
                ring.append((q.x + dx * c - dy * s, q.y + dx * s + dy * c))
            out.append(Region([ring], dark))
        elif isinstance(q, gp.Line):
            # stadium polygon
            L = math.hypot(q.x2 - q.x1, q.y2 - q.y1)
            r = q.width / 2
            ang = math.atan2(q.y2 - q.y1, q.x2 - q.x1) if L > 0 else 0.0
            ring = []
            for k in range(33):
                t = ang - math.pi / 2 + math.pi * k / 32
                ring.append((q.x2 + r * math.cos(t), q.y2 + r * math.sin(t)))
            for k in range(33):
                t = ang + math.pi / 2 + math.pi * k / 32
                ring.append((q.x1 + r * math.cos(t), q.y1 + r * math.sin(t)))
            out.append(Region([ring], dark))
        elif isinstance(q, gp.ArcPoly):
            rings = _arcpoly_rings(q)
            if rings:
                out.append(Region(rings, dark))
        elif isinstance(q, gp.Arc):
            pts = _arc_points(q.x1, q.y1, q.x2, q.y2, q.cx, q.cy, q.clockwise)
            for a, b in zip(pts, pts[1:]):
                out.extend(_prims_to_regions([gp.Line(a[0], a[1], b[0], b[1], q.width, dark)]))
        else:
            raise TypeError(f"unhandled primitive {type(q).__name__}")
    return out


def _ap_mm(a, v):
    return MM(v, a.unit)


def read_gerber(path, stats=None):
    gf = GerberFile.open(path)
    out = Layer()
    st = stats if stats is not None else {}
    for obj in gf.objects:
        dark = obj.polarity_dark
        a = getattr(obj, "aperture", None)
        if isinstance(obj, go.Line) and isinstance(a, ap.CircleAperture):
            q = next(iter(obj.to_primitives(MM)))
            out.append(Track((q.x1, q.y1), (q.x2, q.y2), q.width, dark=dark, snap=True))
            st["track"] = st.get("track", 0) + 1
        elif isinstance(obj, go.Arc) and isinstance(a, ap.CircleAperture):
            q = next(iter(obj.to_primitives(MM)))
            pts = _arc_points(q.x1, q.y1, q.x2, q.y2, q.cx, q.cy, q.clockwise)
            for p0, p1 in zip(pts, pts[1:]):
                out.append(Track(p0, p1, q.width, dark=dark, snap=False))
            st["arc"] = st.get("arc", 0) + 1
        elif isinstance(obj, go.Flash) and isinstance(a, ap.CircleAperture):
            o = obj.converted(MM)
            out.append(Flash((o.x, o.y), "circle", _ap_mm(a, a.diameter), dark=dark))
            st["flash_circle"] = st.get("flash_circle", 0) + 1
        elif isinstance(obj, go.Flash) and isinstance(a, (ap.RectangleAperture, ap.ObroundAperture)):
            o = obj.converted(MM)
            rot = math.degrees(getattr(a, "rotation", 0) or 0) % 180
            w, h = _ap_mm(a, a.w), _ap_mm(a, a.h)
            shape = "rect" if isinstance(a, ap.RectangleAperture) else "obround"
            if abs(rot) < 1e-6 or abs(rot - 180) < 1e-6:
                out.append(Flash((o.x, o.y), shape, w, h, dark=dark))
            elif abs(rot - 90) < 1e-6:
                out.append(Flash((o.x, o.y), shape, h, w, dark=dark))
            else:
                out.extend(_prims_to_regions(obj.to_primitives(MM)))
                st["flash_rotated"] = st.get("flash_rotated", 0) + 1
                continue
            st["flash_" + shape] = st.get("flash_" + shape, 0) + 1
        else:
            out.extend(_prims_to_regions(obj.to_primitives(MM)))   # primitives carry polarity
            k = type(obj).__name__.lower() + ("_" + type(a).__name__ if a is not None else "")
            st[k] = st.get(k, 0) + 1
    return out


def read_outline_bbox(path):
    """Bounding box (mm) of an Edge.Cuts Gerber, centre lines of the outline strokes."""
    gf = GerberFile.open(path)
    xs, ys = [], []
    for obj in gf.objects:
        for q in obj.to_primitives(MM):
            if isinstance(q, gp.Line):
                xs += [q.x1, q.x2]
                ys += [q.y1, q.y2]
            elif isinstance(q, gp.Arc):
                for p in _arc_points(q.x1, q.y1, q.x2, q.y2, q.cx, q.cy, q.clockwise):
                    xs.append(p[0])
                    ys.append(p[1])
            else:
                b = q.bounding_box()
                xs += [b[0][0], b[1][0]]
                ys += [b[0][1], b[1][1]]
    return min(xs), min(ys), max(xs), max(ys)


def read_drills(path):
    """Excellon -> list of (x, y, diameter) mm, KiCad top view."""
    ef = ExcellonFile.open(path)
    out = []
    for obj in ef.objects:
        if isinstance(obj, go.Flash):
            o = obj.converted(MM)
            out.append((o.x, o.y, MM(obj.aperture.diameter, obj.aperture.unit)))
    return out
