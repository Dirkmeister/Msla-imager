#!/usr/bin/env -S python3 # L2 LCD mask
"""edid_timing.py: list the detailed timings in an EDID dump as config.txt hdmi_timings lines.

IMG L2, T-LCD-2. The VS-CXMIPI-V1's own EDID is the best source for the timing it
expects; Waveshare's line was written for a different driver board.

    cat /sys/class/drm/card*-HDMI-A-1/edid > edid.bin     # stock (KMS) boot, LCD attached
    python3 edid_timing.py edid.bin                       # report
    python3 edid_timing.py edid.bin --line                # first timing only, for setup_display.sh

hdmi_timings polarity fields: the Raspberry Pi docs define them only as "invert", so the
lines below keep 0, as in Waveshare's working line, and print the EDID's polarities as a
comment. Aspect field: 3 (16:9) for 16:9 or 9:16 modes, as in Waveshare's line.
"""

import argparse
import sys

ASPECT = {(4, 3): 1, (14, 9): 2, (16, 9): 3, (5, 4): 4, (16, 10): 5, (15, 9): 6, (21, 9): 7, (64, 27): 8}


def dtd(b):
    """Decode one 18-byte detailed timing descriptor, or None if it is not one."""
    pclk = (b[0] | b[1] << 8) * 10_000
    if pclk == 0:
        return None
    t = dict(
        pclk=pclk,
        hact=b[2] | (b[4] & 0xF0) << 4, hblank=b[3] | (b[4] & 0x0F) << 8,
        vact=b[5] | (b[7] & 0xF0) << 4, vblank=b[6] | (b[7] & 0x0F) << 8,
        hfp=b[8] | (b[11] & 0xC0) << 2, hsw=b[9] | (b[11] & 0x30) << 4,
        vfp=b[10] >> 4 | (b[11] & 0x0C) << 2, vsw=b[10] & 0x0F | (b[11] & 0x03) << 4,
        hmm=b[12] | (b[14] & 0xF0) << 4, vmm=b[13] | (b[14] & 0x0F) << 8,
        interlaced=bool(b[17] & 0x80),
    )
    t["hbp"] = t["hblank"] - t["hfp"] - t["hsw"]
    t["vbp"] = t["vblank"] - t["vfp"] - t["vsw"]
    t["htot"], t["vtot"] = t["hact"] + t["hblank"], t["vact"] + t["vblank"]
    t["hz"] = pclk / (t["htot"] * t["vtot"])
    if (b[17] >> 3) & 0x03 == 0x03:  # digital separate sync: bit 2 = V+, bit 1 = H+
        t["pol"] = ("+" if b[17] & 0x02 else "-") + "hsync " + ("+" if b[17] & 0x04 else "-") + "vsync"
    else:
        t["pol"] = f"sync type {(b[17] >> 3) & 0x03} (not digital separate)"
    return t


def hdmi_timings(t):
    w, h = t["hact"], t["vact"]
    aspect = next((code for (a, b), code in ASPECT.items() if w * b == h * a or w * a == h * b), 3)
    return (f"{w} 0 {t['hfp']} {t['hsw']} {t['hbp']} {h} 0 {t['vfp']} {t['vsw']} {t['vbp']} "
            f"0 0 0 {round(t['hz'])} {int(t['interlaced'])} {t['pclk']} {aspect}")


def descriptors(edid):
    """Yield (where, 18-byte block) for every descriptor slot in the base block and CTA extensions."""
    for i in range(4):
        yield f"base slot {i + 1}", edid[54 + 18 * i:72 + 18 * i]
    for n in range(1, len(edid) // 128):
        ext = edid[128 * n:128 * (n + 1)]
        if ext[0] == 0x02 and 4 <= ext[2] < 127:  # CTA-861: DTDs from byte d to 126
            for j, off in enumerate(range(ext[2], 127 - 17, 18)):
                yield f"CTA ext {n} DTD {j + 1}", ext[off:off + 18]


def report(edid):
    if edid[:8] != bytes.fromhex("00ffffffffffff00"):
        raise SystemExit("not an EDID (bad header). Was the LCD board powered and connected?")
    blocks = len(edid) // 128
    for n in range(blocks):
        ok = sum(edid[128 * n:128 * (n + 1)]) % 256 == 0
        tag = "base" if n == 0 else f"ext {n} tag 0x{edid[128 * n]:02x}"
        print(f"block {n} ({tag}): checksum {'OK' if ok else 'BAD'}")
    m = edid[8] << 8 | edid[9]
    mfg = "".join(chr(64 + (m >> s & 0x1F)) for s in (10, 5, 0))
    print(f"maker {mfg}, product 0x{edid[11] << 8 | edid[10]:04x}, EDID {edid[18]}.{edid[19]}, "
          f"week {edid[16]} of {1990 + edid[17]}; {edid[126]} extension block(s)")
    found = []
    for where, b in descriptors(edid):
        if len(b) < 18:
            continue
        t = dtd(b)
        if t:
            found.append(t)
            print(f"\n{where}: {t['hact']}x{t['vact']}{'i' if t['interlaced'] else ''} at "
                  f"{t['hz']:.3f} Hz, pixel clock {t['pclk'] / 1e6:.2f} MHz, "
                  f"total {t['htot']} x {t['vtot']}, {t['pol']}, image {t['hmm']} x {t['vmm']} mm")
            print(f"  h: fp {t['hfp']} sync {t['hsw']} bp {t['hbp']}   "
                  f"v: fp {t['vfp']} sync {t['vsw']} bp {t['vbp']}")
            print(f"  hdmi_timings={hdmi_timings(t)}")
        elif b[3] == 0xFC:
            print(f"{where}: name {b[5:18].decode('ascii', 'replace').strip()}")
        elif b[3] == 0xFD:
            print(f"{where}: range {b[5]}-{b[6]} Hz vertical, {b[7]}-{b[8]} kHz horizontal, "
                  f"max {b[9] * 10} MHz (offset flags 0x{b[4]:02x})")
    for n in range(1, blocks):
        if edid[128 * n] != 0x02:
            print(f"\next {n} (tag 0x{edid[128 * n]:02x}) not decoded here; see edid-decode")
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description="EDID detailed timings as hdmi_timings lines.")
    ap.add_argument("edid", help="binary EDID file")
    ap.add_argument("--line", action="store_true", help="print only the first timing's hdmi_timings value")
    args = ap.parse_args(argv)
    edid = open(args.edid, "rb").read()
    if len(edid) < 128 or len(edid) % 128:
        raise SystemExit(f"{args.edid}: {len(edid)} bytes; an EDID is a multiple of 128")
    if args.line:
        t = next((dtd(b) for _, b in descriptors(edid) if len(b) == 18 and dtd(b)), None)
        if not t:
            raise SystemExit("no detailed timing found")
        print(hdmi_timings(t))
        return 0
    if not report(edid):
        print("\nno detailed timings found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
