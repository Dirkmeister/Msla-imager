#!/usr/bin/env -S python3 # L2 LCD mask
"""show_png.py: show a 1-bit PNG on the imager LCD at exactly 1:1.

IMG L2 hand-off to L4 (MSLA PRINTER Project). The converter does all geometry
(imager-03 design rules), so this script never scales, rotates, mirrors or
anti-aliases. It refuses a PNG whose size differs from the framebuffer, and a
PNG with grey or transparent pixels, so a wrong file fails loudly instead of
exposing a wrong image.

On the Pi (root, so it can take the console out of text mode):
    sudo python3 show_png.py layer.png              # hold until Ctrl-C, then blank
    sudo python3 show_png.py layer.png --hold 30    # hold 30 s, then blank
    sudo python3 show_png.py layer.png --writes 20 --hold 5   # time 20 more frame writes
Dry run anywhere (no framebuffer needed):
    python3 show_png.py layer.png --sim 1440x2560x16 --out frame.raw

Prints the PNG decode, pack and framebuffer write times; --writes N repeats the
write N times and prints min, median and max (L4.2's frame-change time, REQ-012).
Setup and the T-LCD-2 steps: lcd/README.md.

Needs Pillow (Raspberry Pi OS: sudo apt install python3-pil).
"""

import argparse
import fcntl
import os
import signal
import statistics
import struct
import sys
import time

NATIVE = (1440, 2560)  # LS055R1SX04 portrait, 47.25 um pixels (imager-04 section 2)
FBIOGET_VSCREENINFO = 0x4600
KDSETMODE, KD_TEXT, KD_GRAPHICS = 0x4B3A, 0x00, 0x01

# Channel layout (offset, length) for red, green, blue, alpha when there is no real
# framebuffer to ask (--sim). 16 bpp is the firmware default (RGB565).
SIM_FIELDS = {
    16: ((11, 5), (5, 6), (0, 5), (0, 0)),
    24: ((16, 8), (8, 8), (0, 8), (0, 0)),
    32: ((16, 8), (8, 8), (0, 8), (24, 8)),
}


class Geometry:
    """Framebuffer geometry plus the only two pixel values this project uses."""

    def __init__(self, xres, yres, bpp, stride, fields, xoffset=0, yoffset=0,
                 name="sim", virtual=None):
        if bpp not in (16, 24, 32):
            raise SystemExit(f"framebuffer is {bpp} bpp; only 16, 24 or 32 handled")
        self.xres, self.yres, self.bpp, self.stride = xres, yres, bpp, stride
        self.fields, self.xoffset, self.yoffset = fields, xoffset, yoffset
        self.name, self.virtual = name, virtual or (xres, yres)
        self.bytes_pp = bpp // 8
        if stride < xres * self.bytes_pp:
            raise SystemExit(f"stride {stride} is shorter than one row of pixels")
        (ro, rl), (go, gl), (bo, bl), (ao, al) = fields
        alpha = ((1 << al) - 1) << ao if al else 0
        lit = alpha
        for off, length in ((ro, rl), (go, gl), (bo, bl)):
            lit |= ((1 << length) - 1) << off
        self.lit = lit.to_bytes(self.bytes_pp, "little")     # all colour bits on, opaque
        self.dark = alpha.to_bytes(self.bytes_pp, "little")  # all colour bits off, opaque

    @property
    def size(self):
        return (self.xres, self.yres)

    def describe(self):
        (ro, rl), (go, gl), (bo, bl), (ao, al) = self.fields
        return (f"{self.name}: {self.xres}x{self.yres} visible, "
                f"{self.virtual[0]}x{self.virtual[1]} virtual, offset "
                f"{self.xoffset},{self.yoffset}, {self.bpp} bpp "
                f"(R {ro}/{rl} G {go}/{gl} B {bo}/{bl} A {ao}/{al}), "
                f"stride {self.stride} B, lit {self.lit.hex()} dark {self.dark.hex()}")


def _read(path, default):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def probe(fbdev="/dev/fb0"):
    """Read the live framebuffer geometry: FBIOGET_VSCREENINFO plus the sysfs stride."""
    fd = os.open(fbdev, os.O_RDONLY)
    try:
        raw = fcntl.ioctl(fd, FBIOGET_VSCREENINFO, bytes(160))
    finally:
        os.close(fd)
    v = struct.unpack("=40I", raw)
    xres, yres, xvirt, yvirt, xoff, yoff, bpp = v[:7]
    fields = tuple((v[8 + 3 * i], v[9 + 3 * i]) for i in range(4))  # R, G, B, transp
    node = os.path.join("/sys/class/graphics", os.path.basename(fbdev))
    stride = int(_read(os.path.join(node, "stride"), xvirt * bpp // 8))
    name = _read(os.path.join(node, "name"), os.path.basename(fbdev))
    return Geometry(xres, yres, bpp, stride, fields, xoff, yoff, name, (xvirt, yvirt))


def sim_geometry(spec, stride=None):
    """'1440x2560x16' -> Geometry for a dry run (no framebuffer)."""
    try:
        w, h, bpp = (int(n) for n in spec.lower().split("x"))
    except ValueError:
        raise SystemExit(f"--sim wants WxHxBPP, e.g. 1440x2560x16, not {spec!r}")
    if bpp not in SIM_FIELDS:
        raise SystemExit("--sim depth must be 16, 24 or 32")
    return Geometry(w, h, bpp, stride or w * bpp // 8, SIM_FIELDS[bpp])


def frame_from_mask(geom, mask):
    """Pack a W*H mask (one byte per pixel, nonzero = lit) into framebuffer bytes."""
    w, h, n = geom.xres, geom.yres, geom.bytes_pp
    if len(mask) != w * h:
        raise ValueError(f"mask has {len(mask)} pixels, framebuffer has {w * h}")
    packed = bytearray(w * h * n)
    for k in range(n):  # one byte plane at a time, all in C
        packed[k::n] = mask.translate(bytes([geom.dark[k]] + [geom.lit[k]] * 255))
    row = w * n
    if geom.stride == row:
        return packed
    frame = bytearray(geom.stride * h)
    for y in range(h):
        frame[y * geom.stride:y * geom.stride + row] = packed[y * row:(y + 1) * row]
    return frame


def write_frame(fbdev, geom, frame, out=None):
    """Write one frame to the framebuffer (or to `out` for a dry run). Returns seconds."""
    t0 = time.monotonic()
    if out:
        with open(out, "wb") as f:
            f.write(frame)
        return time.monotonic() - t0
    fd = os.open(fbdev, os.O_WRONLY)
    try:
        os.lseek(fd, geom.yoffset * geom.stride + geom.xoffset * geom.bytes_pp, os.SEEK_SET)
        view = memoryview(frame)
        while view:
            view = view[os.write(fd, view):]
    finally:
        os.close(fd)
    return time.monotonic() - t0


class ConsoleGraphics:
    """Console in graphics mode, so the kernel stops drawing text and the cursor on the LCD."""

    def __init__(self, tty="/dev/tty0"):
        self.tty, self.fd = tty, None

    def __enter__(self):
        try:
            self.fd = os.open(self.tty, os.O_RDWR | os.O_NOCTTY)
            fcntl.ioctl(self.fd, KDSETMODE, KD_GRAPHICS)
        except OSError as e:
            print(f"warning: console left in text mode ({e}); run with sudo or the "
                  "cursor and console text can draw over the image", file=sys.stderr)
            if self.fd is not None:
                os.close(self.fd)
            self.fd = None
        return self

    def __exit__(self, *exc):
        if self.fd is not None:
            try:
                fcntl.ioctl(self.fd, KDSETMODE, KD_TEXT)
            finally:
                os.close(self.fd)
        return False


def hold(seconds=None):
    """Block until Ctrl-C or SIGTERM, or for `seconds`. Returns the time held."""
    stop = []
    old = {s: signal.signal(s, lambda signum, frame: stop.append(signum))
           for s in (signal.SIGINT, signal.SIGTERM)}
    t0 = time.monotonic()
    try:
        while not stop and (seconds is None or time.monotonic() - t0 < seconds):
            time.sleep(0.1)
    finally:
        for s, handler in old.items():
            signal.signal(s, handler)
    return time.monotonic() - t0


def load_png(path, size, threshold=None):
    """PNG -> W*H mask (0 or 255 per pixel). Refuses a wrong size, alpha, or grey pixels."""
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("needs Pillow: sudo apt install python3-pil")
    img = Image.open(path)
    img.load()
    if img.size != size:
        hint = " (rotated 90 degrees?)" if img.size == size[::-1] else ""
        raise SystemExit(f"{path}: {img.size[0]}x{img.size[1]} px but the framebuffer is "
                         f"{size[0]}x{size[1]}{hint}. The converter outputs native size; "
                         "nothing here scales or rotates.")
    if "A" in img.getbands() or "transparency" in img.info:
        raise SystemExit(f"{path}: has transparency. Save 1-bit (or 8-bit grey) with no alpha.")
    grey = img.convert("L")
    n_grey = sum(grey.histogram()[1:255])
    if n_grey and threshold is None:
        raise SystemExit(f"{path}: {n_grey} grey pixels (anti-aliasing?). Expected only black "
                         "and white; pass --threshold N to binarize on purpose.")
    if threshold is not None:
        grey = grey.point(lambda v: 255 if v >= threshold else 0)
    return grey.tobytes()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Show a 1-bit PNG on the imager LCD at 1:1.")
    ap.add_argument("png")
    ap.add_argument("--hold", type=float, metavar="S", help="seconds to hold (default: until Ctrl-C)")
    ap.add_argument("--fb", default="/dev/fb0")
    ap.add_argument("--tty", default="/dev/tty0", help="console to put in graphics mode")
    ap.add_argument("--threshold", type=int, metavar="N", help="binarize grey at N (0-255) instead of refusing")
    ap.add_argument("--writes", type=int, default=0, metavar="N",
                    help="after showing, rewrite the frame N times and print min/median/max write time")
    ap.add_argument("--sim", metavar="WxHxBPP", help="dry run without a framebuffer, e.g. 1440x2560x16")
    ap.add_argument("--out", metavar="FILE", help="with --sim: write the packed frame here")
    args = ap.parse_args(argv)

    geom = sim_geometry(args.sim) if args.sim else probe(args.fb)
    if geom.size != NATIVE:
        raise SystemExit(f"framebuffer is {geom.xres}x{geom.yres}, panel native is "
                         f"{NATIVE[0]}x{NATIVE[1]}: the display path would scale. Fix config.txt "
                         "first: lcd/README.md, T-LCD-2 (and run `sudo python3 lcd/fbtest.py info`).")
    t0 = time.monotonic()
    mask = load_png(args.png, geom.size, args.threshold)
    t1 = time.monotonic()
    lit = len(mask) - mask.count(0)
    frame = frame_from_mask(geom, mask)
    dark = frame_from_mask(geom, bytes(len(mask)))
    t2 = time.monotonic()
    prep = f"decode {(t1 - t0) * 1e3:.0f} ms, pack {(t2 - t1) * 1e3:.0f} ms"
    if args.sim:
        dt = write_frame(None, geom, frame, out=args.out or os.devnull)
        print(f"sim: {args.png} packed to {len(frame)} B ({lit / len(mask):.1%} lit); {prep}; "
              f"write to file {dt * 1e3:.0f} ms")
        return 0
    with ConsoleGraphics(args.tty):
        dt = write_frame(args.fb, geom, frame)
        print(f"showing {args.png} 1:1 on {args.fb} ({geom.xres}x{geom.yres}, {geom.bpp} bpp, "
              f"{lit / len(mask):.1%} lit); {prep}; write {dt * 1e3:.0f} ms. Ctrl-C blanks and exits.")
        if args.writes > 0:
            times = [write_frame(args.fb, geom, frame) * 1e3 for _ in range(args.writes)]
            print(f"{args.writes} more writes of {len(frame)} B: min {min(times):.1f} ms, median "
                  f"{statistics.median(times):.1f} ms, max {max(times):.1f} ms")
        held = hold(args.hold)
        write_frame(args.fb, geom, dark)
    print(f"held {held:.1f} s; LCD blanked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
