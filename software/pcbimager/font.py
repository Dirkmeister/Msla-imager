"""Stroke text from the Hershey 'futural' font (the family KiCad's stroke font descends from).

Text is built as Tracks (rule R4: width kept, not snapped), in mm, y up, as it should read
on the copper face. Side transforms mirror it for the screen.
"""
from functools import lru_cache

from HersheyFonts import HersheyFonts

from .geom import Layer, Track, Affine, transform

_CAP_TOP, _BASE = -12.0, 9.0          # futural cap line and baseline, raw units (y down)
_CAP_H = _BASE - _CAP_TOP             # 21 units


@lru_cache(maxsize=1)
def _font():
    f = HersheyFonts()
    f.load_default_font("futural")
    return f


def text_width_mm(s, height):
    strokes = list(_font().strokes_for_text(s))
    xs = [p[0] for st in strokes for p in st]
    return (max(xs) - min(xs)) * height / _CAP_H if xs else 0.0


def text(s, x, y, height, stroke_w, anchor="c", rot_deg=0, dark=True):
    """Stroke text. (x, y) = anchor point, mm. height = cap height, mm.
    anchor: 'c' centre, 'l' left-middle, 'r' right-middle."""
    strokes = list(_font().strokes_for_text(s))
    if not strokes:
        return Layer()
    k = height / _CAP_H
    xs = [p[0] for st in strokes for p in st]
    xmin, xmax = min(xs), max(xs)
    ax = {"c": (xmin + xmax) / 2, "l": xmin, "r": xmax}[anchor]
    ay = (_CAP_TOP + _BASE) / 2
    out = Layer()
    for st in strokes:
        pts = [((px - ax) * k, -(py - ay) * k) for px, py in st]
        if len(pts) == 1:
            pts = pts * 2
        for a, b in zip(pts, pts[1:]):
            out.append(Track(a, b, stroke_w, dark=dark, snap=False))
    T = Affine.translate(x, y) @ Affine.rotate_deg(rot_deg)
    return transform(out, T)
