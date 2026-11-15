"""1-bit rasterizer in the image frame, implementing the REQ-023 rounding rule (units.py).

Panel mm -> image px (calibration rotation theta, CCW from above, offset (dx, dy)):
    x = W/2 + dx + ( u cos(theta) - v sin(theta)) / p
    y = H/2 + dy - ( u sin(theta) + v cos(theta)) / p
The calibration rotation moves feature positions (track ends, pad centres, region vertices);
pad shapes stay pixel-aligned. Error from that: theta x pad half-size, 0.05 mil at 1 mrad on a
50 mil pad.
"""
import math
import zlib
import struct

import numpy as np
from PIL import Image

from .geom import Affine, Track, Flash, Region
from .machine import Machine, Calibration
from .units import px_count, snap_center


class Canvas:
    def __init__(self, machine=None, calibration=None):
        self.m = machine or Machine()
        self.cal = calibration or Calibration()
        self.img = np.zeros((self.m.image_h, self.m.image_w), dtype=bool)
        p = self.m.pitch_mm
        th = self.cal.rotation_mrad / 1000.0
        c, s = math.cos(th), math.sin(th)
        cx = self.m.image_w / 2 + self.cal.offset_px[0]
        cy = self.m.image_h / 2 + self.cal.offset_px[1]
        self.T = Affine(c / p, -s / p, -s / p, -c / p, cx, cy)
        self.log = {"tracks": 0, "flashes": 0, "regions": 0, "thin": 0}

    # ------------------------------------------------------------ public
    def render(self, layer):
        for prim in layer:
            if isinstance(prim, Track):
                self.track(prim)
            elif isinstance(prim, Flash):
                self.flash(prim)
            elif isinstance(prim, Region):
                self.region(prim)
            else:
                raise TypeError(prim)
        return self

    def n_px(self, size_mm):
        n = px_count(size_mm, self.m.pitch_mm)
        if size_mm / self.m.pitch_mm < 0.5:
            self.log["thin"] += 1
        return n

    def track(self, t):
        self.log["tracks"] += 1
        n = self.n_px(t.w)
        (x0, y0), (x1, y1) = self.T(t.p0), self.T(t.p1)
        if t.snap:
            # bias: axis-aligned tracks only (S-3 stripe response)
            if abs(y1 - y0) < 1e-9:
                n = max(1, n + self.m.bias_px_v)
            elif abs(x1 - x0) < 1e-9:
                n = max(1, n + self.m.bias_px_u)
            x0, x1 = snap_center(x0, n), snap_center(x1, n)
            y0, y1 = snap_center(y0, n), snap_center(y1, n)
        self._capsule(x0, y0, x1, y1, n / 2.0, t.dark)

    def flash(self, f):
        self.log["flashes"] += 1
        x, y = self.T(f.c)
        if f.shape == "circle":
            n = self.n_px(f.w)
            self._capsule(snap_center(x, n), snap_center(y, n), snap_center(x, n), snap_center(y, n),
                          n / 2.0, f.dark)
        elif f.shape == "rect":
            nw = max(1, self.n_px(f.w) + self.m.bias_px_u)
            nh = max(1, self.n_px(f.h) + self.m.bias_px_v)
            self._rect(snap_center(x, nw), snap_center(y, nh), nw, nh, f.dark)
        elif f.shape == "obround":
            n = self.n_px(min(f.w, f.h))
            L = abs(f.w - f.h) / self.m.pitch_mm / 2.0
            if f.w >= f.h:
                xa, xb = snap_center(x - L, n), snap_center(x + L, n)
                yy = snap_center(y, n)
                self._capsule(xa, yy, xb, yy, n / 2.0, f.dark)
            else:
                ya, yb = snap_center(y - L, n), snap_center(y + L, n)
                xx = snap_center(x, n)
                self._capsule(xx, ya, xx, yb, n / 2.0, f.dark)
        else:
            raise ValueError(f.shape)

    def region(self, r):
        self.log["regions"] += 1
        rings = [[self.T(q) for q in ring] for ring in r.rings]
        self._fill(rings, r.dark)

    # ------------------------------------------------------------ primitives in px
    def _bounds(self, xmin, ymin, xmax, ymax):
        H, W = self.img.shape
        i0 = max(0, int(math.floor(xmin - 0.5)))
        i1 = min(W, int(math.ceil(xmax + 0.5)) + 1)
        j0 = max(0, int(math.floor(ymin - 0.5)))
        j1 = min(H, int(math.ceil(ymax + 0.5)) + 1)
        return i0, i1, j0, j1

    def _capsule(self, x0, y0, x1, y1, r, dark):
        i0, i1, j0, j1 = self._bounds(min(x0, x1) - r, min(y0, y1) - r, max(x0, x1) + r, max(y0, y1) + r)
        if i0 >= i1 or j0 >= j1:
            return
        X = np.arange(i0, i1) + 0.5
        Y = (np.arange(j0, j1) + 0.5)[:, None]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        if L2 == 0:
            d2 = (X - x0) ** 2 + (Y - y0) ** 2
        else:
            t = ((X - x0) * dx + (Y - y0) * dy) / L2
            t = np.clip(t, 0.0, 1.0)
            d2 = (X - (x0 + t * dx)) ** 2 + (Y - (y0 + t * dy)) ** 2
        mask = d2 < r * r
        self.img[j0:j1, i0:i1][mask] = dark

    def _rect(self, x, y, nw, nh, dark):
        # pixels whose centres lie strictly inside |X-x| < nw/2, |Y-y| < nh/2
        H, W = self.img.shape
        ia = int(math.floor(x - nw / 2.0 + 0.5 + 1e-9))
        ja = int(math.floor(y - nh / 2.0 + 0.5 + 1e-9))
        ib, jb = ia + nw, ja + nh
        ia, ib = max(0, ia), min(W, ib)
        ja, jb = max(0, ja), min(H, jb)
        if ia < ib and ja < jb:
            self.img[ja:jb, ia:ib] = dark

    def _fill(self, rings, dark):
        """Scanline fill, nonzero winding, pixel-centre sampling, half-open spans."""
        H, W = self.img.shape
        E = []
        for ring in rings:
            n = len(ring)
            for k in range(n):
                xa, ya = ring[k]
                xb, yb = ring[(k + 1) % n]
                if ya != yb:
                    E.append((xa, ya, xb, yb))
        if not E:
            return
        E = np.asarray(E, dtype=float)
        x0, y0, x1, y1 = E.T
        ylo, yhi = np.minimum(y0, y1), np.maximum(y0, y1)
        dirs = np.where(y1 > y0, 1, -1)
        j0 = max(0, int(math.floor(ylo.min() - 0.5)))
        j1 = min(H - 1, int(math.ceil(yhi.max() - 0.5)))
        slope = (x1 - x0) / (y1 - y0)
        for j in range(j0, j1 + 1):
            yc = j + 0.5
            act = (ylo <= yc) & (yc < yhi)
            if not act.any():
                continue
            xc = x0[act] + (yc - y0[act]) * slope[act]
            d = dirs[act]
            o = np.argsort(xc, kind="stable")
            xc, d = xc[o], d[o]
            wnd = np.cumsum(d)[:-1]
            inside = wnd != 0
            if not inside.any():
                continue
            a = np.ceil(xc[:-1][inside] - 0.5).astype(int)
            b = np.ceil(xc[1:][inside] - 0.5).astype(int)
            a = np.clip(a, 0, W)
            b = np.clip(b, 0, W)
            diff = np.zeros(W + 1, dtype=int)
            np.add.at(diff, a, 1)
            np.add.at(diff, b, -1)
            row = np.cumsum(diff)[:W] > 0
            if dark:
                self.img[j] |= row
            else:
                self.img[j] &= ~row


# ---------------------------------------------------------------- output

def to_native(img, machine):
    out = np.rot90(img, k=(machine.native_rot_ccw // 90) % 4)
    if machine.native_mirror:
        out = np.fliplr(out)
    return np.ascontiguousarray(out)


def from_native(nat, machine):
    out = nat
    if machine.native_mirror:
        out = np.fliplr(out)
    return np.ascontiguousarray(np.rot90(out, k=-(machine.native_rot_ccw // 90) % 4))


def save_png_1bit(arr, path):
    """Write a bool array as a 1-bit grayscale PNG (lit = 1 = white)."""
    im = Image.fromarray(np.asarray(arr, dtype=bool))
    assert im.mode == "1"
    im.save(path, optimize=True)


def load_png_bool(path):
    im = Image.open(path)
    if im.mode != "1":
        im = im.convert("L").point(lambda v: 255 if v >= 128 else 0).convert("1")
    return np.asarray(im, dtype=bool)


def png_header(path):
    """(width, height, bit_depth, color_type) from IHDR."""
    with open(path, "rb") as f:
        sig = f.read(8)
        assert sig == b"\x89PNG\r\n\x1a\n"
        ln, typ = struct.unpack(">I4s", f.read(8))
        assert typ == b"IHDR"
        w, h, bd, ct = struct.unpack(">IIBB", f.read(10))
    return w, h, bd, ct
