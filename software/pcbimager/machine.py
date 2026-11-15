"""Machine geometry and calibration.

Frames (all seen from above the LCD, operator in front):
  board   KiCad top view, mm, x right, y up (Gerber convention).
  panel   mm, origin at the panel centre (= centre of the tooling pins), u along the 6 in side
          (to the operator's right), v along the 4.5 in side (away from the operator).
  image   pixels, 2560 x 1440 landscape, x (col) right along +u, y (row) down along -v.
          Panel centre lands at (W/2 + dx, H/2 + dy).
  native  framebuffer, 1440 x 2560 portrait: image frame rotated by native_rot_ccw
          (numpy rot90 sense), then flipped left-right if native_mirror.

Sides and the stamp rule: the face being imaged lies face-down on an LCD that faces up, so the
screen must show the mirror of what should read on that face. KiCad top-view data: the top layer
is mirrored about the flip axis, the bottom layer is shown as-is. Copper text reads mirrored on
screen for both sides. See docs/orientation.md.
"""
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .units import PITCH_MM_DEFAULT, INCH_MM


@dataclass
class Machine:
    machine_id: str = "imager-v1"
    pitch_mm: float = PITCH_MM_DEFAULT
    image_w: int = 2560          # long axis, along u
    image_h: int = 1440          # short axis, along v
    native_rot_ccw: int = 90     # PENDING L2 (T-LCD-5 screen F): 90 or 270
    native_mirror: bool = False  # PENDING L2: True if the panel scans mirrored
    panel_u_in: float = 6.0
    panel_v_in: float = 4.5
    guard_in: float = 0.1        # REQ-020 starting guard per side
    flip_axis: str = "long"      # PENDING D-14 (L5): "long" -> v -> -v, "short" -> u -> -u
    mirrored_side: str = "top"   # stamp rule (docs/orientation.md); param in case T-LCD-5 says otherwise
    bias_px_u: int = 0           # S-3 stripe-bias response: extra px on widths measured along u
    bias_px_v: int = 0           # ... along v

    @property
    def native_w(self):
        return self.image_h if self.native_rot_ccw % 180 else self.image_w

    @property
    def native_h(self):
        return self.image_w if self.native_rot_ccw % 180 else self.image_h

    @property
    def image_u_mm(self):
        return self.image_w * self.pitch_mm

    @property
    def image_v_mm(self):
        return self.image_h * self.pitch_mm

    @property
    def board_area_mm(self):
        g = self.guard_in * INCH_MM
        return self.image_u_mm - 2 * g, self.image_v_mm - 2 * g

    def to_dict(self):
        return asdict(self)

    @classmethod
    def load(cls, path=None):
        if path is None:
            return cls()
        d = json.loads(Path(path).read_text())
        d = {k: v for k, v in d.items() if not k.startswith("_")}
        return cls(**d)

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n")


@dataclass
class Calibration:
    """REQ-014 calibration store contents that affect rendering. Lives on the Pi; the converter
    bakes in the values it was given and the job records them."""
    calibration_id: str = "none"
    offset_px: tuple = (0.0, 0.0)   # panel centre minus image centre, image-frame px
    rotation_mrad: float = 0.0      # LCD grid rotation vs the pin axis, CCW positive, seen from above
    nominal_s: float = None
    notes: str = ""

    def to_dict(self):
        d = asdict(self)
        d["offset_px"] = list(self.offset_px)
        return d

    def flipped(self, flip_axis):
        """Calibration of the frame that, pixel-flipped about the flip axis, gives the screen.
        long: (dx, -dy, -theta); short: (-dx, dy, -theta). Derivation in docs/orientation.md."""
        dx, dy = self.offset_px
        off = (dx, -dy) if flip_axis == "long" else (-dx, dy)
        return Calibration(self.calibration_id + "/flipped", off, -self.rotation_mrad,
                           self.nominal_s, self.notes)

    @classmethod
    def load(cls, path=None):
        if path is None:
            return cls()
        d = json.loads(Path(path).read_text())
        d = {k: v for k, v in d.items() if not k.startswith("_")}
        if "offset_px" in d:
            d["offset_px"] = tuple(d["offset_px"])
        return cls(**d)
