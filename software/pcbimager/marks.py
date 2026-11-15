"""Marks authored as they should read on the copper: polarity "CU", orientation "F", labels.

Polarity rule (imager-08 §6, adopted by L4): every pattern and coupon carries copper text "CU".
Copper is lit, so the CU letters must etch as copper (or hold as resist after develop). Letters
showing as voids in a copper block mean the polarity is inverted somewhere.
"""
from .geom import Layer, Region, rect_ring
from .font import text, text_width_mm
from .units import inch, mil

BIG_H = inch(0.100)      # F and CU cap height
BIG_W = mil(15)          # their stroke
SMALL_H = inch(0.060)    # labels
SMALL_W = mil(10)


def id_block(name, x=0.0, y=0.0, clear_bg=True, extra=None):
    """F + CU on the first row, name (and optional extra) below. Centred on (x, y), mm.
    Returns (layer, (w, h)) with w, h the keep-out size in mm."""
    gap = inch(0.06)
    w_f = text_width_mm("F", BIG_H) + BIG_W
    w_cu = text_width_mm("CU", BIG_H) + BIG_W
    row1_w = w_f + gap + w_cu
    lines = [name] + ([extra] if extra else [])
    row_ws = [text_width_mm(s, SMALL_H) + SMALL_W for s in lines]
    w = max(row1_w, *row_ws) + 2 * inch(0.05)
    row_h1 = BIG_H + BIG_W
    row_hs = SMALL_H + SMALL_W
    vgap = inch(0.04)
    h = row_h1 + len(lines) * (row_hs + vgap) + 2 * inch(0.05)
    lay = Layer()
    if clear_bg:
        lay.append(Region([rect_ring(x, y, w, h)], dark=False))
    top = y + h / 2 - inch(0.05) - row_h1 / 2
    x0 = x - row1_w / 2
    lay.add(text("F", x0 + w_f / 2, top, BIG_H, BIG_W))
    lay.add(text("CU", x0 + w_f + gap + w_cu / 2, top, BIG_H, BIG_W))
    yy = top - row_h1 / 2 - vgap - row_hs / 2
    for s in lines:
        lay.add(text(s, x, yy, SMALL_H, SMALL_W))
        yy -= row_hs + vgap
    return lay, (w, h)


def label(s, x, y, h=SMALL_H, w=SMALL_W, anchor="c"):
    return text(s, x, y, h, w, anchor=anchor)
