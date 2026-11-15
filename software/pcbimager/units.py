"""Units and the REQ-023 pixel rounding rule.

Internal length unit: millimetres (KiCad's native unit). Helpers convert mil and inch.

Rounding rule (REQ-023, imager-04 §2), applied in the image frame (pixel edges at integers,
pixel centres at k + 0.5):

  R1  Stroked and flashed features (tracks, round/rect/obround pads, text strokes) keep their
      size: n = round_half_up(size / pitch), minimum 1 px. The centre line or centre point snaps
      to the nearest pixel centre when n is odd and the nearest pixel edge when n is even, so the
      feature is exactly n px wide wherever it sits. Spaces take the remainder.
  R2  Regions (pours, polygons, macro pads, SVG fills) and rotated shapes: a pixel is lit when its
      centre is strictly inside the shape. Edges land on the nearest pixel boundary, +/- 0.5 px.
  R3  A pixel is lit when its centre is strictly inside the (snapped) shape. No anti-aliasing.
  R4  Arcs and text strokes keep the R1 width but are not snapped (curves have no single centre line).
"""
import math

MIL_MM = 0.0254
INCH_MM = 25.4
PITCH_MM_DEFAULT = 0.04725  # 47.25 um, LS055R1SX04 (imager-03)

_EPS = 1e-9
_SNAP_EPS = 1e-6  # px. Breaks exact ties (feature centre exactly on a snap boundary) consistently
                  # toward +x / +y, and absorbs float error from mm -> px division.


def mil(x):
    """mil -> mm"""
    return x * MIL_MM


def inch(x):
    """inch -> mm"""
    return x * INCH_MM


def mm_to_mil(x):
    return x / MIL_MM


def mm_to_in(x):
    return x / INCH_MM


def round_half_up(x):
    return math.floor(x + 0.5 + _EPS)


def px_count(size_mm, pitch_mm=PITCH_MM_DEFAULT):
    """R1: whole-pixel size of a feature. Never less than 1 px."""
    return max(1, round_half_up(size_mm / pitch_mm))


def snap_center(c_px, n):
    """R1: snap a centre coordinate (pixel units) so an n-px feature covers whole pixels.
    Odd n -> nearest pixel centre (k + 0.5). Even n -> nearest pixel edge (k)."""
    if n % 2:
        return math.floor(c_px + _SNAP_EPS) + 0.5
    return float(math.floor(c_px + 0.5 + _SNAP_EPS))
