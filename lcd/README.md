L2 LCD mask
# lcd/: the imager LCD's video path (IMG L2)

The Pi Zero 2 W drives the Sharp LS055R1SX04 (1440 x 2560 portrait, 47.25 µm pixels) through the HDMI-to-MIPI driver board at native size and 50 Hz, with nothing scaling in between (REQ-002, T-LCD-2). This folder holds the config and scripts that do it, plus the bench records. Each script's docstring is its usage.

| File | What |
|---|---|
| `setup_display.sh` | Writes the firmware HDMI block into config.txt: `206` (Waveshare's 50 Hz line), `180` (43.69 Hz), `custom "LINE"`, `--ws` (Waveshare's gpu_mem=256 and extra_transpose_buffer=2), `kms` (undo) |
| `fbtest.py` | Test patterns straight to /dev/fb0. `info` passes only with a native framebuffer **and** the pixel clock within 1% of the timing line |
| `show_png.py` | Shows a 1-bit PNG at 1:1; refuses a wrong size, grey or alpha; prints decode, pack and write times. The hand-off to L4 |
| `edid_timing.py` | EDID dump to hdmi_timings lines |
| `capture.sh` | Records one boot (OS, config, EDID, mode, clocks, fbtest info) into `records/L2.2/LABEL/` |
| `records/` | L2.1 photos and readings; L2.2 captures |

## Why this path

- 50 Hz at native needs at least 1440 x 2560 x 50 = 184.32 MHz. Waveshare's line, blanking included, is (1440 + 160) x (2560 + 15) x 50 = 206.0 MHz (imager-04 §2).
- The vc4 KMS driver rejects HDMI modes above 162 MHz on Pi 0 to 3, Zero 2 W included (`drivers/gpu/drm/vc4/vc4_hdmi.c`). So no KMS overlay: the firmware drives HDMI and Linux gets a plain framebuffer, /dev/fb0.
- The firmware path that takes `hdmi_timings` is supported only through Bullseye (Raspberry Pi's legacy config.txt documentation). Current Raspberry Pi OS is Trixie and Imager's "Legacy" entry is Bookworm, so the card is Raspberry Pi OS Lite, Bullseye, from the archive.
- Full-range RGB: `hdmi_pixel_encoding=2` (imager-03 design rule).
- Size alone proves nothing: the firmware can apply `framebuffer_width/height`, ignore `hdmi_timings` and scale. `fbtest.py info` also checks `vcgencmd measure_clock pixel` against the line, and the 1 px checkerboard under magnification is the real test.

## T-LCD-2 steps

As planned for L2.2. L2.2 rewrites this section as run.

1. **Card.** Raspberry Pi OS Lite (32-bit), Bullseye: the newest `*-raspios-bullseye-armhf-lite.img.xz` under `https://downloads.raspberrypi.com/raspios_oldstable_lite_armhf/images/`. Record the file name and its SHA-256. Flash with Raspberry Pi Imager (Use custom) and set hostname, user, Wi-Fi and SSH in its OS customisation. If Imager won't customise a custom image, put these on the boot partition instead: an empty `ssh`; `userconf.txt` holding `USER:HASH` (HASH from `openssl passwd -6`); `wpa_supplicant.conf` with `country=US` and a `network={ ssid="..." psk="..." }` block.
2. **Stock boot** (KMS still on), driver board powered and on the Pi's HDMI. SSH in, then:
   ```
   sudo apt update && sudo apt install -y git python3-pil python3-numpy
   git clone https://github.com/Dirkmeister/Msla-imager.git && cd Msla-imager
   sudo bash lcd/capture.sh stock
   ```
   `records/L2.2/stock/edid.txt` holds the board's own timing line.
3. **Timing ladder**, one line per boot; stop at the first PASS.
   1. The old 2022 card's line, if that card turned up.
   2. The board's EDID line: `sudo bash lcd/setup_display.sh custom "$(python3 lcd/edid_timing.py lcd/records/L2.2/stock/edid.bin --line)"`
   3. `sudo bash lcd/setup_display.sh 206`
   4. `sudo bash lcd/setup_display.sh 180` (43.69 Hz; the board is listed as 50 Hz only)

   After each: `sudo reboot`, then `sudo python3 lcd/fbtest.py info` and `sudo bash lcd/capture.sh LABEL`. No picture, or FAIL: run the same line again with `--ws` before moving to the next line. If nothing passes, a PC's HDMI at the EDID mode shows whether the board and panel take 50 Hz at all; D-03's fallback is a Pi 4 (KMS allows 600 MHz) or a PC.
4. **Patterns**, on the line that passed:
   ```
   sudo python3 lcd/show_png.py software/out/patterns/flat/tlcd2_grating.png
   sudo python3 lcd/show_png.py software/out/patterns/flat/tlcd2_checker.png --writes 20 --hold 900
   sudo bash lcd/capture.sh LABEL-soak
   ```
   Grating: all 4 one-pixel edge lines visible, 1-on-1-off patches resolved at the center and 4 corners. Checker: every pixel alternates at the center and 4 corners under magnification, no beat or blur, stable for the 15 min hold (900 s).
5. **Undo:** `sudo bash lcd/setup_display.sh kms && sudo reboot`.

## Result (L2.2)

Not run yet.
