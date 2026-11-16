# L2 LCD mask: L2.1 numbers for panel 1 (Sharp LS055R1SX04) from its datasheet LCY-1314302B and vendor cell data: outline, active-area borders, margins on the 4.5 x 6 in panel, stack t (EST) and alpha_max. No bench thickness readings (Dallas, 2026-11-15). Run: python3 calcs/l2_stack_t.py
import math

MM_PER_IN = 25.4


def inch(mm):
    return mm / MM_PER_IN


def show(label, mm, work=""):
    print(f"  {label}: {inch(mm):.4f} in ({mm:.3f} mm){'   ' + work if work else ''}")


# 1. Datasheet LCY-1314302B: Table 1 (p.5) and Fig. 13 (p.31). mm.
FRAME_W, FRAME_L = 70.94, 128.49          # metal frame, ±0.15
TFT_W, TFT_L = 70.04, 127.59              # bottom (TFT) glass, ±0.15
CF_W, CF_L = 70.04, 124.65                # top (CF) glass, ±0.15
POL_W, POL_L = 69.64, 123.06              # front polarizer, ±0.15
AA_W, AA_L = 68.04, 120.96                # active area
MODULE_T, MODULE_T_TOL = 1.35, 0.10       # with backlight
AA_TO_FRAME_SIDE, AA_TO_FRAME_FAR, AA_TO_FRAME_FPC = 1.45, 1.45, 6.08
FPC_PAST_FRAME, FPC_TAIL_W = 98.2, 9.0

print("1. Datasheet outline (LCY-1314302B Fig. 13)")
for name, w, l in (("Metal frame", FRAME_W, FRAME_L), ("TFT glass", TFT_W, TFT_L),
                   ("CF glass", CF_W, CF_L), ("Front polarizer", POL_W, POL_L), ("Active area", AA_W, AA_L)):
    print(f"  {name}: {inch(w):.4f} x {inch(l):.4f} in ({w:.2f} x {l:.2f} mm)")
show("Module thickness typ", MODULE_T, f"±{inch(MODULE_T_TOL):.4f} in (±{MODULE_T_TOL} mm); max {MODULE_T + MODULE_T_TOL:.2f} mm")
print(f"  Border check W: {AA_TO_FRAME_SIDE} + {AA_W} + {AA_TO_FRAME_SIDE} = {AA_TO_FRAME_SIDE + AA_W + AA_TO_FRAME_SIDE:.2f} mm (frame {FRAME_W})")
print(f"  Border check L: {AA_TO_FRAME_FAR} + {AA_L} + {AA_TO_FRAME_FPC} = {AA_TO_FRAME_FAR + AA_L + AA_TO_FRAME_FPC:.2f} mm (frame {FRAME_L})")
show("Active area to frame, long sides", AA_TO_FRAME_SIDE)
show("Active area to frame, far end", AA_TO_FRAME_FAR)
show("Active area to frame, FPC end", AA_TO_FRAME_FPC)
show("FPC past the frame, flat", FPC_PAST_FRAME)
show("FPC tail width", FPC_TAIL_W)
print(f"  p.78 71 x 128 mm vs frame: 71 - {FRAME_W} = {71 - FRAME_W:+.2f} mm, 128 - {FRAME_L} = {128 - FRAME_L:+.2f} mm")

print("\n2. Derived from Fig. 13 (EST: frame overhangs the glass equally at both ends; glasses flush at the far end)")
ledge = TFT_L - CF_L
show("Ledge depth", ledge, f"= {TFT_L} - {CF_L}")
pol_strip = (CF_W - POL_W) / 2
show("Glass beyond front polarizer, each long side", pol_strip, f"= ({CF_W} - {POL_W})/2")
ovh_w = (FRAME_W - TFT_W) / 2
ovh_l = (FRAME_L - TFT_L) / 2
show("Frame overhang per long side", ovh_w, f"= ({FRAME_W} - {TFT_W})/2")
show("Frame overhang per end", ovh_l, f"= ({FRAME_L} - {TFT_L})/2")
show("Glass edge to active area, long sides", (TFT_W - AA_W) / 2, f"= ({TFT_W} - {AA_W})/2")
show("Glass edge to active area, far end", AA_TO_FRAME_FAR - ovh_l, f"= {AA_TO_FRAME_FAR} - {ovh_l:.2f}")
show("TFT glass edge to active area, FPC end", AA_TO_FRAME_FPC - ovh_l, f"= {AA_TO_FRAME_FPC} - {ovh_l:.2f}")
show("CF glass edge to active area, FPC end", CF_L - AA_L - (AA_TO_FRAME_FAR - ovh_l),
     f"= {CF_L} - {AA_L} - {AA_TO_FRAME_FAR - ovh_l:.2f}")

print("\n3. Margins on the 4.5 x 6 in panel, image centered (D-09)")
PANEL_W, PANEL_L = 4.5 * MM_PER_IN, 6.0 * MM_PER_IN
m_l = (PANEL_L - AA_L) / 2
m_w = (PANEL_W - AA_W) / 2
show("Panel edge to image edge, long axis", m_l, f"= ({PANEL_L:.1f} - {AA_L})/2")
show("Panel edge to image edge, short axis", m_w, f"= ({PANEL_W:.2f} - {AA_W})/2")
show("Frame edge to panel edge, far end", m_l - AA_TO_FRAME_FAR, f"= {m_l:.2f} - {AA_TO_FRAME_FAR}")
show("Frame edge to panel edge, FPC end (FPC leaves here)", m_l - AA_TO_FRAME_FPC, f"= {m_l:.2f} - {AA_TO_FRAME_FPC}")
show("Frame edge to panel edge, long sides", m_w - AA_TO_FRAME_SIDE, f"= {m_w:.2f} - {AA_TO_FRAME_SIDE}")

print("\n4. Stack t, EST (not measured)")
TOP_GLASS = 0.15        # same-size Sharp 1440 x 2560 cell: 0.15 + 0.15 mm glass (imager-04 section 1, vendor)
CELL_BARE = 0.30        # same cell without polarizers (imager-04 section 1, vendor)
CELL_WITH_POL = 0.55    # LS055T3SX03 Sharp 5.5 in cell with polarizers, outline depth 0.55 mm typ (lcds-screen.com); same active area, other model
top_pol = (CELL_WITH_POL - CELL_BARE) / 2
t0 = TOP_GLASS + top_pol
show("Top polarizer", top_pol, f"= ({CELL_WITH_POL} - {CELL_BARE})/2, polarizers assumed equal")
show("t without the cover sheet", t0, f"= {TOP_GLASS} + {top_pol:.3f}")
print("  Excludes the factory protective film (comes off) and any added protector (none).")

B_MIL, N = 2.5, 1.5     # REQ-008 smear budget; n assumed (imager-04 section 1)
b_mm = B_MIL * 0.0254


def alpha_max(t_mm):
    th = math.degrees(math.atan(b_mm / t_mm))
    return th, math.degrees(math.asin(N * math.sin(math.radians(th))))


print("\n5. alpha_max = asin(1.5 sin(atan(2.5 mil / t)))")
cases = [("t, no cover sheet (EST)", t0)]
for c_in in (0.0005, 0.001, 0.002):
    cases.append((f"t + {c_in} in cover sheet", t0 + c_in * MM_PER_IN))
cases += [("old EST, half the listing's 1.45 mm module", 0.725),
          ("half the datasheet's 1.35 mm module", 0.675)]
for label, t in cases:
    th, a = alpha_max(t)
    print(f"  {label}: t = {inch(t):.4f} in ({t:.4f} mm); atan({b_mm:.4f}/{t:.4f}) = {th:.3f} deg; "
          f"1.5 x sin = {N * math.sin(math.radians(th)):.4f}; alpha_max = {a:.2f} deg")
