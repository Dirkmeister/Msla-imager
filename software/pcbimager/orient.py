"""Side handling (REQ-004): which layer is mirrored, about which axis, and how.

The LCD faces up and the face being imaged lies face-down on it, so the LCD works like a rubber
stamp: what the screen shows (seen from above) is the mirror of what lands on the face, as read
from that face. Copper text reads mirrored on screen for both sides.

KiCad data is in top view (both copper layers drawn as seen from above the top face):
  top layer:    imaged with the top face down, i.e. after a flip about the flip axis -> mirrored
  bottom layer: imaged with the top face up -> shown as-is
(machine.mirrored_side = 'top'. It stays a parameter only so a T-LCD-5 result can overrule it.)

flip_axis 'long': the panel turns over about its long centreline (D-14 option B): v -> -v,
                  screen rows j -> H-1-j.
flip_axis 'short': about its short centreline: u -> -u, screen columns i -> W-1-i.

The mirror is done as an exact pixel-array flip of a render made with the mirrored calibration
(Calibration.flipped). So the mirrored image is pixel-for-pixel the mirror of a render, and a
feature whose centre sits exactly on a snap tie lands at the same board position on both faces.
"""
import numpy as np

from .geom import Affine, transform
from .machine import Calibration
from .raster import Canvas


def flip(machine):
    if machine.flip_axis == "long":
        return Affine.mirror_y()
    if machine.flip_axis == "short":
        return Affine.mirror_x()
    raise ValueError(f"flip_axis must be 'long' or 'short', not {machine.flip_axis!r}")


def flip_pixels(img, machine):
    return np.ascontiguousarray(np.flipud(img) if machine.flip_axis == "long" else np.fliplr(img))


def is_mirrored(machine, side):
    if side not in ("top", "bottom"):
        raise ValueError(side)
    return side == machine.mirrored_side


def render_topview(machine, layer, side, calibration=None, canvas_log=None):
    """KiCad top-view geometry on `side` -> screen image (image frame, bool)."""
    cal = calibration or Calibration()
    if is_mirrored(machine, side):
        c = Canvas(machine, cal.flipped(machine.flip_axis)).render(layer)
        img = flip_pixels(c.img, machine)
    else:
        c = Canvas(machine, cal).render(layer)
        img = c.img
    if canvas_log is not None:
        canvas_log.update(c.log)
    return img


def face_to_top_view(machine, side):
    """Affine taking content authored as read on `side` to KiCad top view."""
    return Affine() if side == "top" else flip(machine)


def topview_to_screen_affine(machine, side):
    """Geometric equivalent of render_topview's side handling (for positions/metadata)."""
    return flip(machine) if is_mirrored(machine, side) else Affine()
