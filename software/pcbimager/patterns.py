"""Pattern generator (REQ-026). Every pattern carries the copper "CU" polarity mark.

Content is authored as it should read on the copper face. Single-sided patterns are top-side jobs
(copper view = KiCad top view of the top face) and go to the screen through orient.render_topview,
the converter's own side path, so every pattern's F and CU marks also check the mirror logic.
Pixel-defined content (checkerboard, gratings, rulers) is laid down in screen pixels first.
tlcd5_screen is deliberately in screen view.
"""
import math
from dataclasses import dataclass, field

import numpy as np

from .geom import Layer, Track, Flash, Region, Affine, transform, rect_ring, bbox
from .units import inch, mil, mm_to_in
from .font import text, text_width_mm
from .marks import id_block, label
from .orient import render_topview, face_to_top_view, topview_to_screen_affine, flip_pixels
from .raster import Canvas
from . import coupons as cp

TAG = "V0.1"


@dataclass
class Pattern:
    name: str
    test: str                      # imager-06 test ID(s)
    kind: str                      # 'display' (no UV) or 'exposure'
    frames: list                   # [(t_s, bool image-frame array)]
    end_s: float = None            # exposure end (fixed-time jobs)
    time_mode: str = None          # 'fixed', 'nominal', or None for display
    side: str = "top"              # face the content is authored for
    zones: list = field(default_factory=list)
    notes: str = ""
    params: dict = field(default_factory=dict)


def _render_top(m, layer, base=None):
    """Single-sided patterns are top-side jobs: copper view = KiCad top view of the top face.
    Same code path as converted boards. `base` = screen-view pixels laid down first; the layer
    (including its clear primitives) is then rendered over it."""
    if base is None:
        return render_topview(m, layer, "top")
    mir = m.mirrored_side == "top"
    c = Canvas(m)
    c.img[:] = flip_pixels(base, m) if mir else base
    c.render(layer)
    return flip_pixels(c.img, m) if mir else c.img


def _screen_bbox_px(m, rect_mm, side="top"):
    """Top-view rect (u0, v0, u1, v1) mm -> screen pixel bbox [x0, y0, x1, y1)."""
    A = topview_to_screen_affine(m, side)
    c = Canvas(m)
    pts = [c.T(A(p)) for p in [(rect_mm[0], rect_mm[1]), (rect_mm[2], rect_mm[3])]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [int(round(min(xs))), int(round(min(ys))), int(round(max(xs))), int(round(max(ys)))]


# ------------------------------------------------------------------------- T-LCD-2

def tlcd2_checker(m):
    c = Canvas(m)
    H, W = c.img.shape
    jj, ii = np.indices((H, W))
    c.img[:] = (ii + jj) % 2 == 0
    lay, _ = id_block(f"TLCD2 CHECKER 1PX {TAG}", x=inch(-1.55), y=0)
    img = _render_top(m, lay, base=c.img)
    return Pattern("tlcd2_checker", "T-LCD-2", "display", [(0.0, img)],
                   notes="Full-field 1 px checkerboard, pixel (i, j) lit when i + j is even. "
                         "ID block at mid-left (u = -1.55 in) clears a patch.")


def tlcd2_grating(m):
    c = Canvas(m)
    H, W = c.img.shape
    c.img[0, :] = c.img[-1, :] = True
    c.img[:, 0] = c.img[:, -1] = True
    P = 64
    sites = {"C": (W // 2 - P, H // 2 - P // 2), "TL": (24, 24), "TR": (W - 24 - 2 * P, 24),
             "BL": (24, H - 24 - P), "BR": (W - 24 - 2 * P, H - 24 - P)}
    for x0, y0 in sites.values():
        blk = c.img[y0:y0 + P, x0:x0 + P]
        blk[:, ::2] = True                       # vertical 1-on 1-off
        blk2 = c.img[y0:y0 + P, x0 + P:x0 + 2 * P]
        blk2[::2, :] = True                      # horizontal 1-on 1-off
    lay, _ = id_block(f"TLCD2 GRATING 1PX {TAG}", x=0, y=inch(0.75))
    img = _render_top(m, lay, base=c.img)
    return Pattern("tlcd2_grating", "T-LCD-2", "display", [(0.0, img)],
                   notes="1 px frame on the outermost pixels (a missing edge = cropping or overscan). "
                         "64 x 64 px patches at centre and corners: left vertical 1-on-1-off, right "
                         "horizontal 1-on-1-off.",
                   params={"sites_px": sites, "patch_px": P})


# ------------------------------------------------------------------------- T-LCD-3

RULER_U_COLS = (80, 2480)   # 1 px lines, centres 2400 px apart (4.4646 in, 113.40 mm)
RULER_V_ROWS = (120, 1320)  # 1 px lines, centres 1200 px apart (2.2323 in, 56.70 mm)


def _ruler(m, half):
    c = Canvas(m)
    for x in RULER_U_COLS:
        c.img[:, x - half:x + half + 1] = True
    for y in RULER_V_ROWS:
        c.img[y - half:y + half + 1, :] = True
    return c


def tlcd3_ruler(m, width_px=1):
    half = (width_px - 1) // 2
    c = _ruler(m, half)
    du = (RULER_U_COLS[1] - RULER_U_COLS[0])
    dv = (RULER_V_ROWS[1] - RULER_V_ROWS[0])
    p = m.pitch_mm
    lay = Layer()
    b, _ = id_block(f"TLCD3 RULER {width_px}PX {TAG}", x=inch(-1.1), y=inch(0.25))
    lay.add(b)
    lay.add(label(f"U {du} PX = {du * p / 25.4:.4f} IN ({du * p:.2f} MM)", inch(0.6), inch(0.35)))
    lay.add(label(f"V {dv} PX = {dv * p / 25.4:.4f} IN ({dv * p:.2f} MM)", inch(0.6), inch(0.10)))
    if width_px > 1:
        lay.add(label(f"LINES {width_px} PX: AVERAGE OUTSIDE AND INSIDE", inch(0.6), inch(-0.15)))
    img = _render_top(m, lay, base=c.img)
    name = "tlcd3_ruler_1px" if width_px == 1 else f"tlcd3_ruler_{width_px}px"
    kind = "display" if width_px == 1 else "exposure"
    return Pattern(name, "T-LCD-3", kind, [(0.0, img)],
                   time_mode=None if width_px == 1 else "nominal",
                   notes=f"Lines {width_px} px wide centred on columns {RULER_U_COLS} and rows "
                         f"{RULER_V_ROWS}. Centre to centre: {du} px = {du * p / 25.4:.4f} in "
                         f"({du * p:.2f} mm) along u; {dv} px = {dv * p / 25.4:.4f} in ({dv * p:.2f} mm) "
                         "along v. On copper, measure outside-to-outside and inside-to-inside and "
                         "average them: line growth cancels.",
                   params={"cols": RULER_U_COLS, "rows": RULER_V_ROWS, "width_px": width_px})


# ------------------------------------------------------------------------- T-LCD-5

def _arrow(x0, y0, x1, y1, w, head):
    ang = math.atan2(y1 - y0, x1 - x0)
    lay = Layer([Track((x0, y0), (x1, y1), w, snap=False)])
    for da in (math.radians(150), math.radians(-150)):
        lay.append(Track((x1, y1), (x1 + head * math.cos(ang + da), y1 + head * math.sin(ang + da)),
                         w, snap=False))
    return lay


def tlcd5_screen(m):
    """Deliberately in SCREEN view: no stamp mirror. Checks native rotation and scan direction."""
    lay = Layer()
    lay.add(text("F", inch(-0.9), inch(0.05), inch(0.60), inch(0.06)))
    lay.add(text("CU", inch(0.2), inch(0.05), inch(0.40), inch(0.04)))
    lay.add(label("SCREEN VIEW: READS UPRIGHT FROM THE FRONT", 0, inch(-0.65)))
    lay.add(label("FAR SIDE", 0, inch(1.15)))
    lay.add(label("FRONT (OPERATOR)", 0, inch(-1.15)))
    lay.add(_arrow(inch(1.3), 0, inch(2.1), 0, mil(15), inch(0.12)))
    lay.add(label("+U", inch(1.7), inch(0.15)))
    lay.add(label(f"TLCD5 SCREEN {TAG}", 0, inch(-0.90)))
    c = Canvas(m)
    c.render(lay)          # no face transform on purpose
    return Pattern("tlcd5_screen", "T-LCD-5", "display", [(0.0, c.img)], side="screen",
                   notes="Seen from the operator position, looking down at the LCD: the F reads "
                         "normally and upright, FAR SIDE is at the far edge, the arrow points right. "
                         "Rotated 180 deg: set native_rot_ccw 270 (or 90). Mirrored: set native_mirror. "
                         "This is the only pattern whose text reads correctly on screen.")


def _cross(x, y, arm, w):
    return Layer([Track((x - arm, y), (x + arm, y), w), Track((x, y - arm), (x, y + arm), w)])


CROSSES_TOP_VIEW_IN = ((1.6, 0.7), (-1.6, -0.7), (1.6, -0.7))


def tlcd5_side(m, side):
    """Face content (reads correctly on `side`) + crosses at fixed top-view positions."""
    face = Layer()
    face.add(text("F", inch(-1.1), inch(0.1), inch(0.50), inch(0.05)))
    face.add(text("CU", inch(-0.2), inch(0.1), inch(0.30), inch(0.035)))
    face.add(text("TOP" if side == "top" else "BOT", inch(0.75), inch(0.1), inch(0.20), inch(0.025)))
    b, _ = id_block(f"TLCD5 {side.upper()} {TAG}", x=0, y=inch(-0.75), clear_bg=False)
    face.add(b)
    tv = transform(face, face_to_top_view(m, side))     # as KiCad holds it on F.Cu / B.Cu
    for (u, v) in CROSSES_TOP_VIEW_IN:
        tv.add(_cross(inch(u), inch(v), inch(0.15), mil(10)))
    img = render_topview(m, tv, side)
    return Pattern(f"tlcd5_{side}", "T-LCD-5, S-5 precursor", "exposure", [(0.0, img)],
                   time_mode="nominal", side=side,
                   notes=f"On screen the text reads mirrored (stamp rule). Expose the {side} face "
                         f"face-down; after develop or etch, 'F CU {'TOP' if side == 'top' else 'BOT'}' "
                         "reads correctly from that face. Crosses at top-view (u, v) in = "
                         f"{CROSSES_TOP_VIEW_IN} sit at the same panel spot on both faces after the "
                         "flip, so top and bottom crosses overlap through the board.")


# ------------------------------------------------------------------------- S-4

def s4_white(m):
    base = np.ones((m.image_h, m.image_w), dtype=bool)
    lay, _ = id_block(f"S4 WHITE {TAG}", x=inch(-1.55), y=0)
    img = _render_top(m, lay, base=base)
    return Pattern("s4_white", "S-4", "exposure", [(0.0, img)], time_mode="fixed",
                   notes="All pixels lit except the ID block keep-out. Exposure time set per run.")


def s4_black(m):
    lay, _ = id_block(f"S4 BLACK {TAG}", x=inch(-1.55), y=0)
    img = _render_top(m, lay)
    return Pattern("s4_black", "S-4", "exposure", [(0.0, img)], time_mode="fixed",
                   notes="All dark except the ID block, whose lit text is the positive control: it "
                         "must hold, and nothing else may. Run at 3x nominal (REQ-010).")


# ------------------------------------------------------------------------- wedges (S-1)

ZONE = inch(0.32)
ZONE_GAP_U = inch(0.06)
ZONE_LABEL = inch(0.10)
ZONE_GAP_V = inch(0.06)


def wedge_zone(cx, cy, Z=ZONE):
    """10/10 comb along u (top-left), along v (top-right), solid (bottom-left),
    solid with a 10 mil cross slot (bottom-right)."""
    q = Z / 2
    L = q * 0.8
    lay = Layer()
    for k in range(5):
        d = (k - 2) * mil(20)
        lay.append(Track((cx - q / 2 - L / 2, cy + q / 2 + d), (cx - q / 2 + L / 2, cy + q / 2 + d), mil(10)))
        lay.append(Track((cx + q / 2 + d, cy + q / 2 - L / 2), (cx + q / 2 + d, cy + q / 2 + L / 2), mil(10)))
    lay.append(Flash((cx - q / 2, cy - q / 2), "rect", L, L))
    lay.append(Flash((cx + q / 2, cy - q / 2), "rect", L, L))
    s = L * 0.75
    lay.append(Track((cx + q / 2 - s / 2, cy - q / 2), (cx + q / 2 + s / 2, cy - q / 2), mil(10), dark=False))
    lay.append(Track((cx + q / 2, cy - q / 2 - s / 2), (cx + q / 2, cy - q / 2 + s / 2), mil(10), dark=False))
    return lay


def _fmt_s(t):
    return f"{t:.0f}s" if abs(t - round(t)) < 0.05 else f"{t:.1f}s"


def wedge(m, name, test, times, cols, notes, params):
    """Progressive masking: every zone starts at UV on; zone k goes dark at times[k].
    Frame f (shown from times[f-1]) holds zones f..n-1. Labels and the ID block stay lit."""
    n = len(times)
    rows = math.ceil(n / cols)
    pitch_u = ZONE + ZONE_GAP_U
    pitch_v = ZONE_LABEL + ZONE + ZONE_GAP_V
    grid_h = rows * (ZONE_LABEL + ZONE) + (rows - 1) * ZONE_GAP_V
    top = grid_h / 2
    zones, zone_layers = [], []
    static = Layer()
    for k, t in enumerate(times):
        r, cidx = divmod(k, cols)
        cx = (cidx - (cols - 1) / 2) * pitch_u
        ytop = top - r * pitch_v
        cy = ytop - ZONE_LABEL - ZONE / 2
        static.add(label(_fmt_s(t), cx, ytop - ZONE_LABEL / 2))
        zone_layers.append(wedge_zone(cx, cy))
        rect = (cx - ZONE / 2, cy - ZONE / 2, cx + ZONE / 2, cy + ZONE / 2)
        zones.append({"id": f"Z{k:02d}", "t_s": round(t, 1),
                      "centre_in": [round(mm_to_in(cx), 4), round(mm_to_in(cy), 4)],
                      "screen_bbox_px": _screen_bbox_px(m, rect)})
    blk, (bw, bh) = id_block(f"{name.upper().replace('_', ' ')} {TAG}", x=0,
                             y=-top - inch(0.08) - inch(0.17), clear_bg=False)
    static.add(blk)
    frames = []
    prev = 0.0
    for f in range(n):
        lay = Layer(static)
        for k in range(f, n):
            lay.extend(zone_layers[k])
        frames.append((round(prev, 1), _render_top(m, lay)))
        prev = times[f]
    frames.append((round(times[-1], 1), np.zeros_like(frames[0][1])))   # blank at end
    return Pattern(name, test, "exposure", frames, end_s=round(times[-1], 1), time_mode="fixed",
                   zones=zones, notes=notes, params=params)


def s1_coarse(m):
    times = [round(15 * 2 ** (k / 2)) for k in range(12)]     # 15 ... 679 s, sqrt(2) steps
    return wedge(m, "s1_coarse", "S-1", times, 4,
                 "12 zones at sqrt(2) steps, 15 to 679 s, whole seconds (rounding error under 1.2%). "
                 "Each zone: 10/10 mil comb along u and along v, a solid square, a solid square with "
                 "a 10 mil cross slot. Read the first zone that holds and the window of zones that "
                 "pass.", {"t0_s": 15, "ratio": "2^(1/2)", "n": 12})


def s1_fine(m, start_s):
    times = [round(start_s * 2 ** (k / 4), 1) for k in range(8)]
    return wedge(m, "s1_fine", "S-1", times, 4,
                 f"8 zones at 2^(1/4) (+18.9%/step) from {start_s} s, one coarse step below the "
                 "first good coarse zone. Regenerate with that start time.",
                 {"start_s": start_s, "ratio": "2^(1/4)", "n": 8})


# ------------------------------------------------------------------------- map (S-2)

MAP_ROWS, MAP_COLS, MAP_SUB = 4, 7, 8


def s2_map(m, centre_s):
    """4 x 7 cells, 8 solid sub-zones each, times centre x 2^((j - 3.5)/4).
    Cells are A1 (top-left as read on copper) to D7. Sub-zones row-major, shortest first."""
    times = [round(centre_s * 2 ** ((j - 3.5) / 4), 1) for j in range(MAP_SUB)]
    W, H, p = m.image_w, m.image_h, m.pitch_mm
    cols_px = [round(k * W / MAP_COLS) for k in range(MAP_COLS + 1)]
    rows_px = [round(k * H / MAP_ROWS) for k in range(MAP_ROWS + 1)]
    # cell edges in copper view: column k spans u from px cols_px[k]..cols_px[k+1];
    # row r (A at top) spans v from (H/2 - rows_px[r]) down to (H/2 - rows_px[r+1]).
    margin, lab_h, gap = 8 * p, 44 * p, 10 * p
    static = Layer()
    subs = [Layer() for _ in range(MAP_SUB)]
    zones = []
    for r in range(MAP_ROWS):
        for k in range(MAP_COLS):
            u0, u1 = (cols_px[k] - W / 2) * p, (cols_px[k + 1] - W / 2) * p
            v1, v0 = (H / 2 - rows_px[r]) * p, (H / 2 - rows_px[r + 1]) * p
            cid = f"{'ABCD'[r]}{k + 1}"
            txt = cid
            if r == 0 and k == 0:
                txt = f"{cid}  F CU"
            if r == MAP_ROWS - 1 and k == MAP_COLS - 1:
                txt = f"{cid} {TAG}"
            static.add(label(txt, (u0 + u1) / 2, v1 - margin - lab_h / 2, h=inch(0.05)))
            ia, ib = u0 + margin, u1 - margin
            ja, jb = v0 + margin, v1 - margin - lab_h
            sw, sh = (ib - ia) / 4, (jb - ja) / 2
            for j in range(MAP_SUB):
                rr, cc = divmod(j, 4)
                x = ia + (cc + 0.5) * sw
                y = jb - (rr + 0.5) * sh
                subs[j].append(Flash((x, y), "rect", sw - gap, sh - gap))
            zones.append({"id": cid, "centre_in": [round(mm_to_in((u0 + u1) / 2), 4),
                                                    round(mm_to_in((v0 + v1) / 2), 4)],
                          "screen_bbox_px": _screen_bbox_px(m, (u0, v0, u1, v1))})
    # pattern name in cell D1's label strip area is taken by the ID; add a small name label in D4
    frames, prev = [], 0.0
    for f in range(MAP_SUB):
        lay = Layer(static)
        for j in range(f, MAP_SUB):
            lay.extend(subs[j])
        frames.append((round(prev, 1), _render_top(m, lay)))
        prev = times[f]
    frames.append((round(times[-1], 1), np.zeros_like(frames[0][1])))
    return Pattern("s2_map", "S-2", "exposure", frames, end_s=round(times[-1], 1), time_mode="fixed",
                   zones=zones,
                   notes=f"Cells A1..D7 tile the image (pixel edges cols {cols_px}, rows {rows_px}). "
                         f"Sub-zone j (row-major, shortest first) gets {times} s. Read the first "
                         "sub-zone that holds in each cell: one sub-zone = 2^(1/4) in irradiance.",
                   params={"centre_s": centre_s, "sub_times_s": times})


# ------------------------------------------------------------------------- S-3 coupons

def s3_coupon_layer(m):
    """Copper-view geometry of the S-3 coupon panel. Returns (layer, nets_meta, labels layer)."""
    gu, gv = m.board_area_mm
    sites = {}
    allnets = []
    lay = Layer()
    labels = Layer()
    for nm in ("C", "TL", "TR", "BL", "BR"):
        nets, lab, (w, h) = cp.site(nm)
        sites[nm] = (nets, lab, w, h)
    w, h = sites["C"][2], sites["C"][3]
    pos = {"C": (0.0, 0.0),
           "TL": (-gu / 2 + w / 2, gv / 2 - h / 2), "TR": (gu / 2 - w / 2, gv / 2 - h / 2),
           "BL": (-gu / 2 + w / 2, -gv / 2 + h / 2), "BR": (gu / 2 - w / 2, -gv / 2 + h / 2)}
    boxes = {}
    for nm, (nets, lab, w_, h_) in sites.items():
        T = Affine.translate(*pos[nm])
        boxes[nm] = (pos[nm][0] - w_ / 2, pos[nm][1] - h_ / 2, pos[nm][0] + w_ / 2, pos[nm][1] + h_ / 2)
        for nd, meta in nets:
            nd2 = {k: transform(v, T) for k, v in nd.items()}
            meta2 = {**meta, "centre_mm": T(meta["centre_mm"]),
                     "pads": {k: T(q) for k, q in meta["pads"].items()}}
            allnets.append((nd2, meta2))
            for v in nd2.values():
                lay.extend(v)
        labels.add(transform(lab, T))
    # overlap check
    names = list(boxes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = boxes[names[i]], boxes[names[j]]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                raise ValueError(f"coupon sites overlap: {names[i]} {names[j]}")
    # ruler marks, 10 mil, centres 2400 px apart (stable snap: on pixel centres)
    p = m.pitch_mm
    ru = ((RULER_U_COLS[0] + 0.5 - m.image_w / 2) * p, (RULER_U_COLS[1] + 0.5 - m.image_w / 2) * p)
    for u in ru:
        lay.append(Track((u, inch(-0.30)), (u, inch(0.30)), mil(10)))
    labels.add(label("RULER 2400 PX = 4.4646 IN", 0, -gv / 2 + inch(0.10)))
    blk, _ = id_block(f"S3 COUPONS {TAG}", x=0, y=gv / 2 - inch(0.17), clear_bg=False)
    labels.add(blk)
    return lay, allnets, labels, {"sites": boxes, "ruler_u_mm": ru}


def s3_coupons(m):
    lay, nets, labels, info = s3_coupon_layer(m)
    full = Layer(lay)
    full.extend(labels)
    img = _render_top(m, full)
    meta = []
    for nd, mt in nets:
        meta.append({"site": mt["site"], "s_mil": mt["s_mil"], "orient": mt["orient"],
                     "path_len_in": mt["path_len_in"],
                     "centre_in": [round(mm_to_in(mt["centre_mm"][0]), 4),
                                   round(mm_to_in(mt["centre_mm"][1]), 4)]})
    return Pattern("s3_coupons", "S-3, T-SW-1", "exposure", [(0.0, img)], time_mode="nominal",
                   zones=meta,
                   notes="5 sites (C, TL, TR, BL, BR as read on copper), each with serpentine-comb "
                         "structures at 5/5, 10/10, 15/15, 20/20, 25/25 mil, runs along u (top row) "
                         "and along v (bottom row). Pads: S_A bottom-left, C_L top-left, S_B top-right, "
                         "C_R bottom-right (runs along u). Opens: S_A-S_B; shorts: S to C_L and C_R. "
                         "Ruler marks: 10 mil lines, centres 2400 px apart.",
                   params={k: (v if k != "sites" else {n: [round(mm_to_in(x), 4) for x in b]
                                                        for n, b in v.items()})
                           for k, v in info.items()})


def all_patterns(m, fine_start_s=60.0, map_centre_s=120.0):
    return [tlcd2_checker(m), tlcd2_grating(m), tlcd3_ruler(m, 1), tlcd3_ruler(m, 5),
            tlcd5_screen(m), tlcd5_side(m, "top"), tlcd5_side(m, "bottom"),
            s4_white(m), s4_black(m), s1_coarse(m), s1_fine(m, fine_start_s),
            s2_map(m, map_centre_s), s3_coupons(m)]
