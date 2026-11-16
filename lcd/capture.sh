#!/usr/bin/env -S bash # L2 LCD mask
# capture.sh: IMG L2.2 bench record (T-LCD-2). Run on the Pi after each boot worth keeping:
#   sudo bash lcd/capture.sh LABEL      # e.g. stock, edid, edid-ws, 206, 206-ws, 180, 180-ws
# Writes lcd/records/L2.2/LABEL/ beside this script, in the Pi's clone of the repo:
#   os.txt           image, kernel, firmware, Python, numpy and Pillow versions (for L4)
#   config.txt       /boot config.txt, verbatim under one "# L2 LCD mask" header line
#   cmdline.txt      cmdline.txt, verbatim (one line by format, so no header)
#   edid.bin         raw EDID: tvservice -d on the firmware path, /sys/class/drm on KMS
#   edid.txt         edid_timing.py report, its --line, and a hex dump
#   display.txt      tvservice and vcgencmd: mode, clocks, config, throttling, temperature
#   fbtest_info.txt  fbtest.py info: PASS needs native size and the line's pixel clock
#   kernel.txt       dmesg lines for the framebuffer, vc4, HDMI and undervoltage
# Copy to the PC: scp -r USER@HOST:Msla-imager/lcd/records/L2.2 .
set -uo pipefail

LABEL=${1:-}
[[ $LABEL =~ ^[A-Za-z0-9._-]+$ ]] || { sed -n '2,14p' "$0"; exit 1; }
[[ $EUID -eq 0 ]] || { echo "capture: run with sudo (dmesg, tvservice, EDID)" >&2; exit 1; }

HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$HERE/records/L2.2/$LABEL
mkdir -p "$OUT"
CFG=/boot/firmware/config.txt; [[ -f $CFG ]] || CFG=/boot/config.txt
CMD=/boot/firmware/cmdline.txt; [[ -f $CMD ]] || CMD=/boot/cmdline.txt
STAMP=$(date -Is)

hdr() { echo "L2 LCD mask"; echo "# L2.2 capture '$LABEL', $STAMP, $(hostname): $1"; echo; }
run() { echo "\$ $*"; "$@" 2>&1; echo "(exit $?)"; echo; }

{ hdr "OS image and versions (for L4)"
  echo "\$ cat /proc/device-tree/model"; tr -d '\0' </proc/device-tree/model; echo; echo
  run cat /etc/rpi-issue
  run cat /etc/os-release
  run uname -a
  run vcgencmd version
  run python3 --version
  run python3 -c "import numpy; print('numpy', numpy.__version__)"
  run python3 -c "import PIL; print('Pillow', PIL.__version__)"
  run dpkg-query -W python3-numpy python3-pil raspberrypi-kernel raspberrypi-bootloader libraspberrypi-bin
  run free -m
} >"$OUT/os.txt"

{ echo "# L2 LCD mask: verbatim copy of $CFG below this line (capture.sh $LABEL, $STAMP)"
  cat "$CFG"
} >"$OUT/config.txt"
cp "$CMD" "$OUT/cmdline.txt"

rm -f "$OUT/edid.bin"
EDSRC=
tvservice -d "$OUT/edid.bin" >/dev/null 2>&1
if [[ -s $OUT/edid.bin ]]; then
  EDSRC="tvservice -d (firmware path)"
else
  for f in /sys/class/drm/card*-HDMI-A-1/edid; do   # sysfs reports size 0; read it to know
    [[ -e $f ]] || continue
    cat "$f" >"$OUT/edid.bin" 2>/dev/null
    if [[ -s $OUT/edid.bin ]]; then EDSRC="$f (KMS)"; break; fi
  done
fi
[[ -s $OUT/edid.bin ]] || rm -f "$OUT/edid.bin"

{ hdr "EDID from ${EDSRC:-nowhere}"
  if [[ -s $OUT/edid.bin ]]; then
    run python3 "$HERE/edid_timing.py" "$OUT/edid.bin"
    run python3 "$HERE/edid_timing.py" "$OUT/edid.bin" --line
    echo "hex:"; od -An -tx1 -v "$OUT/edid.bin"
  else
    echo "No EDID read. Is the driver board powered and on the Pi's HDMI?"
  fi
} >"$OUT/edid.txt"

{ hdr "display state"
  run tvservice -s
  run tvservice -n
  run tvservice -m DMT
  run tvservice -m CEA
  for c in pixel hdmi core arm; do run vcgencmd measure_clock "$c"; done
  run vcgencmd get_config int
  run vcgencmd get_config str
  run vcgencmd get_mem gpu
  run vcgencmd get_throttled
  run vcgencmd measure_temp
  run vcgencmd measure_volts core
  for a in name virtual_size bits_per_pixel stride; do run cat "/sys/class/graphics/fb0/$a"; done
} >"$OUT/display.txt"

{ hdr "fbtest.py info"
  python3 "$HERE/fbtest.py" info 2>&1
  echo "(exit $?)"
} >"$OUT/fbtest_info.txt"

{ hdr "dmesg: framebuffer, vc4, HDMI, voltage"
  dmesg | grep -iE 'bcm2708_fb|simplefb|simple-framebuffer|vc4|hdmi|drm|fb0|voltage|throttl' \
    || echo "(no matches)"
} >"$OUT/kernel.txt"

[[ -n ${SUDO_USER:-} ]] && chown -R "$SUDO_USER": "$HERE/records/L2.2"

echo "capture '$LABEL' -> $OUT"
echo "  tvservice -s: $(tvservice -s 2>&1)"
echo "  throttled:    $(vcgencmd get_throttled 2>&1)"
echo "  EDID:         ${EDSRC:-none read}"
grep -E '^(ok  |FAIL|PASS|NO VERDICT)' "$OUT/fbtest_info.txt" | sed 's/^/  /'
