# L1: L1.11 test-board panel generator (KiCad 7.0 pcbnew API): 3x3 C test board, control board, detector board; fills zones, writes DRC report, Gerbers and drill. Run: python3 light/l1_11/test_board/make_test_board.py (needs KiCad 7's pcbnew module and kicad-cli)
"""
Panel for one 2-sided 1.6 mm (0.063 in) 1 oz FR4 blank, isolation-milled on the top side only.
The bottom copper stays intact as a floating heat spreader (no holes touch a net on it).

Boards (all copper is large islands with 0.4 mm (15.7 mil) isolation cuts, straight wherever possible):
  A. Test board, 86 x 80 mm (3.386 x 3.150 in). 9 CUN0LF1B at C21's pitch, 20.00 x 22.68 mm (0.787 x 0.893 in),
     footprint LED_SMD:LED_PLCC_2835_Handsoldering (KiCad 7 stock = the V1 board @ 8208f05, pad for pad).
     3 strings = the 3 rows, anode on the left. Each row: VIN_Rr | LED c1 | Rr_N1 | LED c2 | Rr_N2 | LED c3 | Rr_OUT.
     The isolation cuts run through each LED's pad gap, so every LED's cathode pad (the large pad) sits in a
     20 x 22 mm island. NTC TH1 (1206) on two isolated islands 5 mm right of the center LED, beside its cathode pad.
     M3 holes: 4 on the ATS's 53.00 x 53.00 mm square, centred on the center LED; 4 corner holes for the holder and
     stand. Every hole has an isolated copper ring under the screw head. No ballasts on this board: their heat
     would bias L1.12's per-LED theta.
  B. Control board, 60 x 40 mm: brick +12 V to the three VIN wires; per string a link (solder or clip) where the
     meter reads the string current, then the ballast (12 ohm axial flat, or four 47 ohm 1206 in parallel) to GND;
     the detector's load resistor RL (1206 or axial) with meter pads; NTC meter pads. Sits outside the shroud.
  C. Detector board, 22 x 36 mm: the spare CUN0LF1B as the detector, two wire pads, two M3 holes.
Coordinates: mm, KiCad page; the center LED of board A at (100, 100).
"""
import os
import subprocess

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "l1_11_test_board.kicad_pcb")
GERB = os.path.join(HERE, "gerber")
KLIB = "/usr/share/kicad/footprints"
LOCAL = os.path.join(HERE, "l1_11.pretty")

ISO = 0.4          # isolation cut, mm
HALF = ISO / 2
EDGE = 0.5         # copper back from the board edge, mm
PX, PY = 20.00, 22.68
CX, CY = 100.0, 100.0
GAPC = -0.475      # LED pad-gap centre from the footprint origin, rotated 180 deg (anode left)

mm = pcbnew.FromMM
board = pcbnew.BOARD()
ds = board.GetDesignSettings()
ds.m_CopperEdgeClearance = mm(EDGE)
ds.m_HoleClearance = mm(0.4)
nc = ds.m_NetSettings.m_DefaultNetClass
nc.SetClearance(mm(ISO))
nc.SetTrackWidth(mm(1.0))
board.SetCopperLayerCount(2)

nets = {}


def net(name):
    if name not in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni
    return nets[name]


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def place(lib, name, ref, value, x, y, rot=0.0, padnets=None, local=False):
    fp = pcbnew.FootprintLoad(LOCAL if local else os.path.join(KLIB, lib + ".pretty"), name)
    fp.SetFPIDAsString(("l1_11" if local else lib) + ":" + name)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(V(x, y))
    fp.SetOrientationDegrees(rot)
    board.Add(fp)
    for num, nname in (padnets or {}).items():
        for p in fp.Pads():
            if p.GetNumber() == str(num):
                p.SetNet(net(nname))
    if name.startswith(("TestPoint", "MountingHole")):
        fp.Reference().SetVisible(False)              # labels come from board text instead
    return fp


def zone(nname, x0, y0, x1, y1, prio=0, poly=None):
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.F_Cu)
    z.SetNet(net(nname))
    z.SetZoneName(nname)
    z.SetLocalClearance(mm(ISO))
    z.SetMinThickness(mm(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetAssignedPriority(prio)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    ol = z.Outline()
    ol.NewOutline()
    pts = poly or [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for px, py in pts:
        ol.Append(mm(px), mm(py))
    board.Add(z)
    return z


def edge_rect(x0, y0, x1, y1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(V(x0, y0))
    s.SetEnd(V(x1, y1))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


def text(s, x, y, size=1.0, layer=pcbnew.F_SilkS, rot=0.0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(size * 0.15))
    t.SetTextAngleDegrees(rot)
    board.Add(t)


def hole(ref, x, y):
    # M3 clearance hole with a 6.4 mm top-only ring: an isolated copper ring under the screw head
    return place("MountingHole", "MountingHole_3.2mm_M3_Pad_TopOnly", ref, "M3", x, y)


# ---------------------------------------------------------------- A. test board
AX0, AX1, AY0, AY1 = 57.0, 143.0, 60.0, 140.0
edge_rect(AX0, AY0, AX1, AY1)
xs = [CX - PX, CX, CX + PX]
ys = [CY - PY, CY, CY + PY]
xcut = [x + GAPC for x in xs]                      # 79.525, 99.525, 119.525
ycut = [CY - PY / 2, CY + PY / 2]                  # 88.66, 111.34
row_y = [(AY0 + EDGE, ycut[0] - HALF), (ycut[0] + HALF, ycut[1] - HALF), (ycut[1] + HALF, AY1 - EDGE)]
col_x = [(AX0 + EDGE, xcut[0] - HALF), (xcut[0] + HALF, xcut[1] - HALF), (xcut[1] + HALF, xcut[2] - HALF),
         (xcut[2] + HALF, AX1 - EDGE)]
ref = 1
for r in range(3):
    names = [f"VIN_R{r+1}", f"R{r+1}_N1", f"R{r+1}_N2", f"R{r+1}_OUT"]
    for k, nm in enumerate(names):
        zone(nm, col_x[k][0], row_y[r][0], col_x[k][1], row_y[r][1])
    for c in range(3):
        place("LED_SMD", "LED_PLCC_2835_Handsoldering", f"D{ref}", "CUN0LF1B", xs[c], ys[r], 180,
              {2: names[c], 1: names[c + 1]})          # pad 2 = A (left), pad 1 = K (right)
        ref += 1
    place("TestPoint", "TestPoint_Pad_3.0x3.0mm", f"TP{r+1}", f"VIN_R{r+1}", 61.5, ys[r], 0, {1: names[0]})
    place("TestPoint", "TestPoint_Pad_3.0x3.0mm", f"TP{r+4}", f"OUT_R{r+1}", 138.5, ys[r], 0, {1: names[3]})
    text(f"VIN{r+1}", 61.5, ys[r] - 3.3, 1.0)
    text(f"OUT{r+1}", 138.5, ys[r] - 3.3, 1.0)

# NTC on two isolated islands, 5 mm right of the center LED (beside its cathode pad)
zone("NTC_A", 103.2, 96.0, 108.4, CY - HALF, prio=1)
zone("NTC_B", 103.2, CY + HALF, 108.4, 104.0, prio=1)
place("Resistor_SMD", "R_1206_3216Metric_Pad1.30x1.75mm_HandSolder", "TH1", "B57621C5103K062 10k NTC", 105.0, CY,
      90, {1: "NTC_B", 2: "NTC_A"})
place("TestPoint", "TestPoint_Pad_1.5x1.5mm", "TP7", "NTC_A wire", 107.4, 97.3, 0, {1: "NTC_A"})
place("TestPoint", "TestPoint_Pad_1.5x1.5mm", "TP8", "NTC_B wire", 107.4, 102.7, 0, {1: "NTC_B"})

for i, (hx, hy) in enumerate([(CX - 26.5, CY - 26.5), (CX + 26.5, CY - 26.5), (CX - 26.5, CY + 26.5),
                              (CX + 26.5, CY + 26.5)]):
    hole(f"H{i+1}", hx, hy)                         # ATS 4-corner pattern, 53.00 mm square
for i, (hx, hy) in enumerate([(62.0, 64.5), (138.0, 64.5), (62.0, 135.5), (138.0, 135.5)]):
    hole(f"H{i+5}", hx, hy)                         # holder and stand

text("L1.11 C TEST 3x3  20.00 x 22.68  -DK", CX, 62.4, 1.0)
text("NTC", 105.8, 94.6, 0.8)
text("A+ left, K right; strings = rows", CX, 138.0, 0.8)
text("Bottom: 1 oz copper left intact (floating spreader). Isolation cuts 0.4 mm, top only.", CX, 141.6, 0.8,
     pcbnew.F_Fab)

# ---------------------------------------------------------------- B. control board
BX0, BY0 = 57.0, 145.0
BX1, BY1 = BX0 + 60.0, BY0 + 40.0
edge_rect(BX0, BY0, BX1, BY1)


def u(x):
    return BX0 + x


def v(y):
    return BY0 + y


bands = [(0.5, 10.0 - HALF), (10.0 + HALF, 20.0 - HALF), (20.0 + HALF, 30.0 - HALF)]
zone("V12", u(0.5), v(0.5), u(12.0 - HALF), v(30.0 - HALF))
zone("GND", u(39.0 + HALF), v(0.5), u(59.5), v(30.0 - HALF))
place("TestPoint", "TestPoint_Pad_3.0x3.0mm", "TP11", "+12 IN", u(3.5), v(5.0), 0, {1: "V12"})
place("TestPoint", "TestPoint_Pad_3.0x3.0mm", "TP12", "GND IN", u(55.5), v(5.0), 0, {1: "GND"})
text("+12 IN", u(3.5), v(1.9), 0.8)
text("GND IN", u(55.5), v(1.9), 0.8)
for k in range(3):
    b0, b1 = bands[k]
    yc = (b0 + b1) / 2
    la, lb = f"LINK{k+1}_A", f"LINK{k+1}_B"
    zone(la, u(12.0 + HALF), v(b0), u(22.0 - HALF), v(b1))
    zone(lb, u(22.0 + HALF), v(b0), u(39.0 - HALF), v(b1))
    place("TestPoint", "TestPoint_Pad_3.0x3.0mm", f"TP{13+k}", f"VIN{k+1} out", u(8.5), v(yc), 0, {1: "V12"})
    place("TestPoint", "TestPoint_Pad_3.0x3.0mm", f"TP{16+k}", f"OUT{k+1} in", u(15.5), v(yc), 0, {1: la})
    place("", "Link_2Pad_Gap0.4mm", f"JP{k+1}", f"S{k+1} link / meter", u(22.0), v(yc), 0, {1: la, 2: lb},
          local=True)
    place("", "Ballast_Axial_P16_or_4x1206", f"R{k+1}", "12R axial >=0.61W | 4x47R 1206", u(39.0), v(yc), 0,
          {1: lb, 2: "GND"}, local=True)
    text(f"S{k+1}", u(18.6), v(yc - 3.4), 0.8)
# meter band: detector load resistor and NTC pads
zone("DET_P", u(0.5), v(30.0 + HALF), u(15.0 - HALF), v(39.5))
zone("DET_N", u(15.0 + HALF), v(30.0 + HALF), u(30.0 - HALF), v(39.5))
zone("NTC_A_CTL", u(30.0 + HALF), v(30.0 + HALF), u(45.0 - HALF), v(39.5))
zone("NTC_B_CTL", u(45.0 + HALF), v(30.0 + HALF), u(59.5), v(39.5))
place("", "R_1206_or_Axial_P12", "RL", "100k detector load (1206 or axial)", u(15.0), v(35.0), 0,
      {1: "DET_P", 2: "DET_N"}, local=True)
for ref_, val, x, y, nn in (("TP21", "DET A+ wire", 3.5, 33.6, "DET_P"), ("TP22", "DET K- wire", 26.5, 33.6, "DET_N"),
                            ("TP23", "NTC wire", 33.5, 33.6, "NTC_A_CTL"), ("TP24", "NTC wire", 56.0, 33.6, "NTC_B_CTL")):
    place("TestPoint", "TestPoint_Pad_3.0x3.0mm", ref_, val, u(x), v(y), 0, {1: nn})
for ref_, val, x, y, nn in (("TP25", "meter V+", 4.0, 37.6, "DET_P"), ("TP26", "meter COM", 26.0, 37.6, "DET_N"),
                            ("TP27", "meter", 38.0, 37.6, "NTC_A_CTL"), ("TP28", "meter", 52.0, 37.6, "NTC_B_CTL")):
    place("TestPoint", "TestPoint_Pad_2.0x2.0mm", ref_, val, u(x), v(y), 0, {1: nn})
text("DET", u(8.0), v(31.4), 0.8)
text("NTC", u(45.0), v(31.4), 0.8)
text("L1.11 CONTROL  -DK", u(30.0), v(1.8), 0.8)

# ---------------------------------------------------------------- C. detector board
CX0, CY0 = 121.0, 145.0
CX1, CY1 = CX0 + 22.0, CY0 + 36.0
edge_rect(CX0, CY0, CX1, CY1)
dx, dy = CX0 + 11.0, CY0 + 11.0
zone("DETB_A", CX0 + EDGE, CY0 + EDGE, dx + GAPC - HALF, CY1 - EDGE)
zone("DETB_K", dx + GAPC + HALF, CY0 + EDGE, CX1 - EDGE, CY1 - EDGE)
place("LED_SMD", "LED_PLCC_2835_Handsoldering", "D10", "CUN0LF1B (detector)", dx, dy, 180,
      {2: "DETB_A", 1: "DETB_K"})
place("TestPoint", "TestPoint_Pad_3.0x3.0mm", "TP31", "A+ wire", CX0 + 5.0, CY0 + 31.5, 0, {1: "DETB_A"})
place("TestPoint", "TestPoint_Pad_3.0x3.0mm", "TP32", "K- wire", CX0 + 17.0, CY0 + 31.5, 0, {1: "DETB_K"})
hole("H9", CX0 + 5.0, CY0 + 23.0)
hole("H10", CX0 + 17.0, CY0 + 23.0)
text("A+", CX0 + 5.0, CY0 + 28.2, 0.8)
text("K-", CX0 + 17.0, CY0 + 28.2, 0.8)
text("DET -DK", CX0 + 11.0, CY0 + 2.0, 0.8)

# ---------------------------------------------------------------- fill, DRC, save, export
board.Save(OUT)                                     # unfilled; reload so the board has a project, then fill
board = pcbnew.LoadBoard(OUT)
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
rep = os.path.join(HERE, "drc_report.txt")
ok = pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
print("DRC report written:", ok, rep)
os.makedirs(GERB, exist_ok=True)
subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", GERB + "/", "-l", "F.Cu,B.Cu,F.SilkS,F.Fab,Edge.Cuts",
                "--subtract-soldermask", OUT], check=True)
subprocess.run(["kicad-cli", "pcb", "export", "drill", "-o", GERB + "/", "--format", "excellon", "--drill-origin",
                "absolute", "--excellon-units", "mm", "--excellon-separate-th", OUT], check=True)
subprocess.run(["kicad-cli", "pcb", "export", "svg", "-o", os.path.join(HERE, "l1_11_test_board_top.svg"), "-l",
                "F.Cu,F.SilkS,Edge.Cuts", "--page-size-mode", "2", "--exclude-drawing-sheet", OUT], check=True)
print("done:", OUT)
