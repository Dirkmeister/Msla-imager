#!/usr/bin/env -S python3 # L2 LCD mask
"""fbtest.py: IMG L2 test patterns for the imager LCD (T-LCD-1, -2, -3, -5).

On the Pi:
    sudo python3 fbtest.py info                     # what the firmware actually set; PASS/FAIL
    sudo python3 fbtest.py info --clock 206000000   # check against a clock not in config.txt
    sudo python3 fbtest.py checker                  # T-LCD-2, holds until Ctrl-C
    sudo python3 fbtest.py PATTERN [--mirror x|y] [--hold S]
Dry run anywhere:
    python3 fbtest.py f --mirror x --sim 1440x2560x16 --png f_mirror_x.png

Framebuffer pixel (0,0) is the first pixel in memory; x runs along the 1440 px side,
y along the 2560 px side.

  white    every pixel lit                                   T-LCD-1 loupe
  black    every pixel dark
  checker  1 px checkerboard, (0,0) lit                      T-LCD-2
  lines    1 px vertical and horizontal line patches, 256 px square, at the
           center and 4 corners, plus a 1 px border          T-LCD-2
  border   1 px line on the outermost rows and columns only  active-area edges for L5
  ruler    1 px lines on rows 80 and 2480 (2400 px apart) and
           columns 120 and 1320 (1200 px apart)              T-LCD-3
  f        F target, a 64 px block on pixel (0,0), 1 px border   T-LCD-5

--mirror x reflects about the long centerline (x -> 1439 - x); --mirror y about the
short centerline (y -> 2559 - y). Patterns need no packages; --png needs Pillow.

info PASS needs both: the framebuffer at native 1440 x 2560, and `vcgencmd
measure_clock pixel` within 1% of the timing line's clock. The size alone isn't
enough: the firmware can apply framebuffer_width/height, ignore hdmi_timings, and
scale the framebuffer onto whatever mode it picked. The line comes from `vcgencmd
get_config hdmi_timings`, else the last active hdmi_timings= in config.txt, else
--clock. Exit 0 PASS, 2 FAIL, 3 no clock to check against.
"""

import argparse
import os
import re
import subprocess
import sys

from show_png import (NATIVE, ConsoleGraphics, frame_from_mask, hold, probe,
                      sim_geometry, write_frame)

PATTERNS = ("white", "black", "checker", "lines", "border", "ruler", "f")


class Canvas:
    """One byte per pixel, 1 = lit."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h)

    def _rows(self, x0, y0, x1, y1):
        x0, x1, y0, y1 = max(0, x0), min(self.w, x1), max(0, y0), min(self.h, y1)
        return (x0, x1, range(y0, y1)) if x0 < x1 and y0 < y1 else (0, 0, range(0))

    def rect(self, x0, y0, x1, y1, val=1):
        """Fill x0 <= x < x1, y0 <= y < y1."""
        x0, x1, ys = self._rows(x0, y0, x1, y1)
        seg = bytes([val]) * (x1 - x0)
        for y in ys:
            self.px[y * self.w + x0:y * self.w + x1] = seg

    def vlines(self, x0, y0, x1, y1):
        """1 px vertical lines: lit where x is even."""
        x0, x1, ys = self._rows(x0, y0, x1, y1)
        seg = bytes(int(x % 2 == 0) for x in range(x0, x1))
        for y in ys:
            self.px[y * self.w + x0:y * self.w + x1] = seg

    def hlines(self, x0, y0, x1, y1):
        """1 px horizontal lines: lit where y is even."""
        x0, x1, ys = self._rows(x0, y0, x1, y1)
        on, off = bytes([1]) * (x1 - x0), bytes(x1 - x0)
        for y in ys:
            self.px[y * self.w + x0:y * self.w + x1] = on if y % 2 == 0 else off

    def checker(self):
        even = bytes(int(x % 2 == 0) for x in range(self.w))
        odd = bytes(1 - b for b in even)
        for y in range(self.h):
            self.px[y * self.w:(y + 1) * self.w] = even if y % 2 == 0 else odd

    def border(self):
        w, h = self.w, self.h
        for r in ((0, 0, w, 1), (0, h - 1, w, h), (0, 0, 1, h), (w - 1, 0, w, h)):
            self.rect(*r)

    def mirror(self, axis):
        w, h, px = self.w, self.h, self.px
        if axis == "x":
            for y in range(h):
                px[y * w:(y + 1) * w] = px[y * w:(y + 1) * w][::-1]
        elif axis == "y":
            self.px = bytearray().join(px[(h - 1 - y) * w:(h - y) * w] for y in range(h))


def pattern(name, w, h):
    c = Canvas(w, h)
    if name == "white":
        c.rect(0, 0, w, h)
    elif name == "checker":
        c.checker()
    elif name == "border":
        c.border()
    elif name == "lines":
        p = 256
        for x0, y0 in ((0, 0), (w - p, 0), (0, h - p), (w - p, h - p),
                       ((w - p) // 2, (h - p) // 2)):
            c.vlines(x0, y0, x0 + p // 2, y0 + p)
            c.hlines(x0 + p // 2, y0, x0 + p, y0 + p)
        c.border()
    elif name == "ruler":
        if h < 2401 or w < 1201:
            raise SystemExit("ruler needs at least 1201 x 2401 px")
        y0, x0 = (h - 2400) // 2, (w - 1200) // 2
        for y in (y0, y0 + 2400):
            c.rect(0, y, w, y + 1)
        for x in (x0, x0 + 1200):
            c.rect(x, 0, x + 1, h)
    elif name == "f":
        u = w // 12                                  # 120 px on the native panel
        left, top = w // 2 - 5 * u // 2, h // 2 - 5 * u
        c.rect(left, top, left + u, top + 10 * u)                        # stem
        c.rect(left, top, left + 5 * u, top + u)                         # top arm
        c.rect(left, top + 9 * u // 2, left + 4 * u, top + 11 * u // 2)  # middle arm
        c.rect(0, 0, 64, 64)                                             # pixel (0,0)
        c.border()
    return c


def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (r.stdout + r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return f"({' '.join(cmd)}: {e})"


CLOCK_TOL = 0.01  # lead note 5 (L2, 2026-11-15): measured pixel clock within 1% of the line


def parse_timings(text):
    """17 ints from 'hdmi_timings=...' or a bare line, else None."""
    m = re.search(r"(?:hdmi_timings\s*=\s*)?((?:\d+\s+){16}\d+)", text or "")
    return [int(n) for n in m.group(1).split()] if m else None


def timing_line(cfg_paths=("/boot/firmware/config.txt", "/boot/config.txt")):
    """(17 ints, source) for the active hdmi_timings line, or (None, why)."""
    out = _run(["vcgencmd", "get_config", "hdmi_timings"])
    t = parse_timings(out) if "hdmi_timings" in out else None
    if t:
        return t, "vcgencmd get_config"
    for path in cfg_paths:
        if os.path.exists(path):
            active = [l for l in open(path).read().splitlines()
                      if l.strip().startswith("hdmi_timings")]
            t = parse_timings(active[-1]) if active else None
            return (t, f"last active line in {path}") if t else (None, f"no hdmi_timings in {path}")
    return None, "no config.txt found"


def timing_summary(t):
    """Totals, clock and refresh implied by a 17-field hdmi_timings line."""
    htot = t[0] + t[2] + t[3] + t[4]            # active + front porch + sync + back porch
    vtot = t[5] + t[7] + t[8] + t[9]
    return htot, vtot, t[15], t[15] / (htot * vtot)


def measured_hz(text):
    """'frequency(29)=206000000' -> 206000000, else None."""
    m = re.search(r"=\s*(\d+)", text or "")
    return int(m.group(1)) if m else None


def info(fbdev, clock=None):
    g = probe(fbdev)
    print("model:       ", open("/proc/device-tree/model").read().rstrip("\x00")
          if os.path.exists("/proc/device-tree/model") else "?")
    print("framebuffer: ", g.describe())
    print("tvservice -s:", _run(["tvservice", "-s"]))
    t, src = timing_line()
    tot = None
    if t:
        htot, vtot, pclk, hz = tot = timing_summary(t)
        print(f"timing:       hdmi_timings={' '.join(map(str, t))} ({src})")
        print(f"              total {htot} x {vtot}; {pclk / 1e6:.3f} MHz / ({htot} x {vtot}) "
              f"= {hz:.3f} Hz")
    else:
        print(f"timing:       none ({src})")
    raw = {w: _run(["vcgencmd", "measure_clock", w]) for w in ("pixel", "hdmi", "core")}
    for what, out in raw.items():
        print(f"clock {what:6}:", out)
    cfg = [l for l in _run(["vcgencmd", "get_config", "str"]).splitlines() if "hdmi" in l]
    cfg += [l for l in _run(["vcgencmd", "get_config", "int"]).splitlines()
            if any(k in l for k in ("hdmi", "framebuffer", "overscan", "hvs", "gpu_mem",
                                    "transpose"))]
    print("firmware config:", *cfg, sep="\n  ")
    kern = [l for l in _run(["dmesg"]).splitlines()
            if any(k in l for k in ("bcm2708_fb", "simple-framebuffer", "simplefb", "vc4"))]
    print("kernel:", *(kern or ["(none matched; run with sudo)"]), sep="\n  ")

    size_ok = g.size == NATIVE
    want = clock or (tot[2] if tot else None)
    got = measured_hz(raw["pixel"])
    print()
    print(f"{'ok  ' if size_ok else 'FAIL'} framebuffer {g.xres}x{g.yres}, panel native "
          f"{NATIVE[0]}x{NATIVE[1]}")
    if not want:
        print("---- no clock to check: no hdmi_timings line and no --clock")
        print("NO VERDICT: pass --clock HZ (the mode's pixel clock) to check it")
        return 3
    if not got:
        print(f"FAIL pixel clock unreadable ({raw['pixel']!r}); expected {want / 1e6:.3f} MHz")
        return 2
    err = got / want - 1
    clock_ok = abs(err) <= CLOCK_TOL
    refresh = f", {got / (tot[0] * tot[1]):.3f} Hz on this line's totals" if tot else ""
    print(f"{'ok  ' if clock_ok else 'FAIL'} pixel clock {got / 1e6:.3f} MHz vs "
          f"{want / 1e6:.3f} MHz: ({got} / {want} - 1) = {err:+.3%}, limit ±{CLOCK_TOL:.0%}"
          f"{refresh}")
    ok = size_ok and clock_ok
    print(f"{'PASS' if ok else 'FAIL'}: "
          + ("native framebuffer and the line's pixel clock" if ok else
             "the firmware is not running this line at native size (scaled, or another mode)"))
    return 0 if ok else 2


def preview(geom, frame, path):
    """Decode a packed frame back to a 1-bit PNG, to check the packing in a dry run."""
    from PIL import Image
    n, w, h = geom.bytes_pp, geom.xres, geom.yres
    k = next(i for i in range(n) if geom.lit[i] != geom.dark[i])
    rows = b"".join(frame[y * geom.stride:y * geom.stride + w * n] for y in range(h))
    plane = bytes(rows[k::n]).translate(bytes(255 if v == geom.lit[k] else 0 for v in range(256)))
    Image.frombytes("L", (w, h), plane).convert("1").save(path)


def readback_ok(fbdev, geom, frame):
    """Read the framebuffer back and compare the visible bytes of every row."""
    start = geom.yoffset * geom.stride + geom.xoffset * geom.bytes_pp
    got = bytearray()
    with open(fbdev, "rb", buffering=0) as f:
        f.seek(start)
        while len(got) < len(frame):
            chunk = f.read(len(frame) - len(got))
            if not chunk:
                return False
            got += chunk
    row = geom.xres * geom.bytes_pp
    return all(got[y * geom.stride:y * geom.stride + row] == frame[y * geom.stride:y * geom.stride + row]
               for y in range(geom.yres))


def main(argv=None):
    ap = argparse.ArgumentParser(description="IMG L2 LCD test patterns.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 2)[2])
    ap.add_argument("pattern", choices=("info",) + PATTERNS)
    ap.add_argument("--mirror", choices=("none", "x", "y"), default="none")
    ap.add_argument("--hold", type=float, metavar="S", help="seconds to hold (default: until Ctrl-C)")
    ap.add_argument("--fb", default="/dev/fb0")
    ap.add_argument("--tty", default="/dev/tty0")
    ap.add_argument("--clock", type=int, metavar="HZ",
                    help="info: expected pixel clock, instead of the hdmi_timings line's")
    ap.add_argument("--force", action="store_true", help="draw even if the framebuffer is not native size")
    ap.add_argument("--sim", metavar="WxHxBPP", help="dry run without a framebuffer, e.g. 1440x2560x16")
    ap.add_argument("--stride", type=int, help="with --sim: row stride in bytes (test padding)")
    ap.add_argument("--png", metavar="FILE", help="with --sim: save what the panel would show")
    ap.add_argument("--out", metavar="FILE", help="with --sim: save the packed frame")
    args = ap.parse_args(argv)

    if args.pattern == "info":
        return info(args.fb, args.clock)
    geom = sim_geometry(args.sim, args.stride) if args.sim else probe(args.fb)
    if geom.size != NATIVE and not args.force:
        raise SystemExit(f"FAIL: framebuffer is {geom.xres}x{geom.yres}, not {NATIVE[0]}x{NATIVE[1]}. "
                         "The firmware is scaling or ignored config.txt; run `fbtest.py info`. "
                         "--force draws anyway.")
    canvas = pattern(args.pattern, geom.xres, geom.yres)
    canvas.mirror(args.mirror)
    frame = frame_from_mask(geom, canvas.px)
    label = f"{args.pattern}" + ("" if args.mirror == "none" else f", mirrored {args.mirror}")
    if args.sim:
        write_frame(None, geom, frame, out=args.out or os.devnull)
        if args.png:
            preview(geom, frame, args.png)
        print(f"sim {geom.xres}x{geom.yres}x{geom.bpp}: {label}"
              + (f" -> {args.png}" if args.png else ""))
        return 0
    dark = frame_from_mask(geom, bytes(geom.xres * geom.yres))
    with ConsoleGraphics(args.tty):
        dt = write_frame(args.fb, geom, frame)
        ok = readback_ok(args.fb, geom, frame)
        print(f"showing {label} on {args.fb} ({geom.xres}x{geom.yres}, {geom.bpp} bpp); "
              f"write {dt * 1e3:.0f} ms; readback {'OK' if ok else 'MISMATCH'}. Ctrl-C blanks and exits.")
        held = hold(args.hold)
        write_frame(args.fb, geom, dark)
    print(f"held {held:.1f} s ({held / 60:.1f} min); LCD blanked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
