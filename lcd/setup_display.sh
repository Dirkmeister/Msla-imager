#!/usr/bin/env -S bash # L2 LCD mask
# setup_display.sh: IMG L2, T-LCD-2. Put the Pi on the firmware (legacy) HDMI path with a
# custom timing for the LS055R1SX04 + VS-CXMIPI-V1, or put it back on the stock KMS driver.
#
#   sudo bash setup_display.sh 206                 # Waveshare's 50 Hz line, 206.0 MHz: try first
#   sudo bash setup_display.sh 180                 # Waveshare's Pi 3B/Zero line, 180 MHz = 43.69 Hz
#   sudo bash setup_display.sh custom "1440 0 ..." # any 17-field line, e.g. edid_timing.py --line
#   sudo bash setup_display.sh kms                 # undo everything this script changed in config.txt
# then: sudo reboot
#
# Why not KMS: the vc4 KMS driver caps HDMI at 162 MHz on Pi 0-3 class chips (Zero 2 W
# included), and this board needs at least 184.32 MHz for 50 Hz (imager-04 section 2).
set -euo pipefail

CFG=${IMGL2_CFG:-/boot/firmware/config.txt}
CMD=${IMGL2_CMD:-/boot/firmware/cmdline.txt}
[[ -f $CFG ]] || CFG=/boot/config.txt   # Bullseye and older
[[ -f $CMD ]] || CMD=/boot/cmdline.txt
TAG='#IMGL2#'

die() { echo "setup_display: $*" >&2; exit 1; }
[[ -f $CFG && -f $CMD ]] || die "config.txt or cmdline.txt not found"
[[ -w $CFG && -w $CMD ]] || die "run with sudo"

case ${1:-} in
  206) LINE='1440 0 10 10 140 2560 0 11 2 2 0 0 0 50 0 206000000 3' ;;
  180) LINE='1440 0 10 10 140 2560 0 11 2 2 0 0 0 50 0 180000000 3' ;;
  custom)
    LINE=${2:-}
    [[ $LINE =~ ^[0-9]+( [0-9]+){16}$ ]] || die "custom needs one quoted line of 17 integers"
    ;;
  kms) LINE= ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac

[[ -e $CFG.imgl2-orig ]] || cp "$CFG" "$CFG.imgl2-orig"
[[ -e $CMD.imgl2-orig ]] || cp "$CMD" "$CMD.imgl2-orig"

# Remove any block this script added earlier and restore the overlay lines it commented out.
sed -i '/^# IMGL2-BEGIN/,/^# IMGL2-END/d' "$CFG"
sed -i "s/^$TAG//" "$CFG"

if [[ -z $LINE ]]; then
  echo "Stock KMS path restored in $CFG (original kept as $CFG.imgl2-orig). Now: sudo reboot"
  exit 0
fi

# Firmware path: no vc4 KMS or FKMS overlay at all.
sed -i -E 's/^(dtoverlay=vc4-f?kms-v3d.*)$/'"$TAG"'\1/' "$CFG"

cat >>"$CFG" <<EOF
# IMGL2-BEGIN added by setup_display.sh (IMG L2, T-LCD-2). Undo: setup_display.sh kms
[all]
# Waveshare 5.5inch 1440x2560 LCD wiki block, as listed in imager-06 T-LCD-2
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_drive=2
hdmi_pixel_encoding=2
hdmi_pixel_freq_limit=268500000
hdmi_timings=$LINE
config_hdmi_boost=10
hvs_priority=0x32ff
# 1:1 with the panel: framebuffer at native size, no overscan, no rotation
disable_overscan=1
framebuffer_width=1440
framebuffer_height=2560
max_framebuffer_width=1440
max_framebuffer_height=2560
framebuffer_depth=16
gpu_mem=128
# IMGL2-END
EOF

# Stop the console from blanking the LCD during the 15 min hold.
grep -q 'consoleblank=' "$CMD" || sed -i '1 s/$/ consoleblank=0/' "$CMD"

echo "Firmware HDMI path set: hdmi_timings=$LINE"
echo "Originals kept as $CFG.imgl2-orig and $CMD.imgl2-orig. Now: sudo reboot"
