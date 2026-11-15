# Orientation: which layer is mirrored, about which axis (REQ-004)

## The stamp rule

The LCD faces up. The panel lies on it with the face being imaged down (p.23, p.39, imager-03 subsystem 5). The LCD is a rubber stamp: what the screen shows, seen from above, lands on the face as its mirror image when you read that face.

So copper text must read mirrored on screen for every face. In KiCad terms (Gerbers are top view for both copper layers):

| Layer | How it lies on the LCD | Seen from above, the face shows | Screen must show |
|---|---|---|---|
| F.Cu | top face down, after a flip about the flip axis | F.Cu mirrored about the flip axis | F.Cu mirrored |
| B.Cu | top face up, bottom face down | B.Cu as in the top view | B.Cu as-is |

**This is the reverse of REQ-004 and imager-03 subsystem 4 ("mirror the bottom side").** Following those as written mirrors the whole board: both layers would still register to each other, but every footprint comes out reversed, so no IC fits. The code takes the side from `mirrored_side` in the machine config (default "top") so a T-LCD-5 result can overrule this analysis without a code change.

The same rule is the phototool rule from the notebook era: print the top layer mirrored so the printed side touches the copper (p.5 toner transfer: "Print Top (Mirror) & Bottom").

## Flip axis (D-14, pending in L5)

`flip_axis = "long"`: the panel turns over about its long centerline (D-14 option B, holes on that line). v goes to -v; screen rows j go to 1439 - j.
`flip_axis = "short"`: about the short centerline. u goes to -u; columns i go to 2559 - i.

The mirror is about the pin axis, not the board's own center, so it must be the same axis the pins enforce.

KiCad mirrors back-side text left-right, which assumes an end-over-end flip. With a long-axis flip, KiCad's B.Cu text reads upside down when you turn the board over. Cosmetic only.

## How the mirror is done

The mirrored side is rendered unmirrored, with a mirrored calibration, then the pixel array is flipped about the image centerline (an exact operation on the pixel grid because 2560 and 1440 are even). Results:
- The top-side screen image is pixel-for-pixel the mirror of a render, so "mirror correct" in T-SW-1 is an exact test.
- A feature whose center sits exactly on a snap tie lands at the same board position on both faces (T-SW-1: through-hole pad centers agree to 0.000 px front to back).

Mirrored calibration, from requiring C(F(P)) = flip(C'(P)) with C the panel-to-pixel map (offset dx, dy, rotation θ):
- long axis: C' = (dx, -dy, -θ)
- short axis: C' = (-dx, dy, -θ)

## Native orientation (pending L2)

`native_rot_ccw` (90 or 270) and `native_mirror` map the landscape image frame to the portrait framebuffer. Set them with the `tlcd5_screen` pattern: from the operator position, looking down at the LCD, the F must read normally and upright, FAR SIDE at the far edge, the arrow pointing right.
- Rotated 180°: swap 90 and 270.
- Mirrored: set `native_mirror` true (the panel scans mirrored).

## T-LCD-5 with these files

1. `tlcd5_screen`: settles the two native parameters above. It is the only pattern whose text reads correctly on screen.
2. `tlcd5_top` and `tlcd5_bottom`: expose a double-sided panel, top then bottom (flip about the flip axis between). On screen both show mirrored text. After develop, "F CU TOP" reads correctly from the top face and "F CU BOT" from the bottom face, and the three crosses on each face overlap through the board. If either face reads mirrored, `mirrored_side` is wrong; tell L4.
