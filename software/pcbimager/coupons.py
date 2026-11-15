"""S-3 coupon geometry (p.45 Test Board 1), authored in copper view, mm.

Serpentine-comb structure, line s / space s:
  three serpentine runs (S0, S1, S2) of length Lr joined in a meander, with one comb finger
  between each pair of runs (C0 from the left, C1 from the right).
  Pads (square): S_A bottom-left, C_L top-left, S_B top-right, C_R bottom-right.
  Opens: S_A to S_B continuity (4-wire: two probe tips per pad gives R, so width = rho L / (R t)).
  Shorts: S to C_L and S to C_R must be open.
Every conductor is width s, so the serpentine path length is known (returned in the metadata).
"""
import math

from .geom import Layer, Track, Flash, Affine, transform, bbox
from .units import inch, mil
from .font import text

PAD = inch(0.045)
PAD_DY = inch(0.060)   # pad centre beyond the outermost run, along the run-normal
LR = inch(0.120)       # run length
SIZES_MIL = (5, 10, 15, 20, 25)


def serp_comb(s_mil, Lr=LR, pad=PAD):
    """One structure, runs along x, centred on the origin. Returns (nets, meta)."""
    s = mil(s_mil)
    off = max(inch(0.050), 3 * s)
    xL, xR = -Lr / 2 - off, Lr / 2 + off
    yT, yB = 4 * s + PAD_DY, -4 * s - PAD_DY
    S, CL, CR = Layer(), Layer(), Layer()
    # serpentine
    S.add(Track((-Lr / 2, -4 * s), (Lr / 2, -4 * s), s),      # S0
          Track((Lr / 2, -4 * s), (Lr / 2, 0), s),            # join R
          Track((-Lr / 2, 0), (Lr / 2, 0), s),                # S1
          Track((-Lr / 2, 0), (-Lr / 2, 4 * s), s),           # join L
          Track((-Lr / 2, 4 * s), (Lr / 2, 4 * s), s))        # S2
    # serpentine leads to pads
    S.add(Track((-Lr / 2, -4 * s), (xL, -4 * s), s), Track((xL, -4 * s), (xL, yB), s),
          Flash((xL, yB), "rect", pad, pad))
    S.add(Track((Lr / 2, 4 * s), (xR, 4 * s), s), Track((xR, 4 * s), (xR, yT), s),
          Flash((xR, yT), "rect", pad, pad))
    # comb fingers and leads
    CL.add(Track((Lr / 2 - 2 * s, -2 * s), (xL, -2 * s), s), Track((xL, -2 * s), (xL, yT), s),
           Flash((xL, yT), "rect", pad, pad))
    CR.add(Track((-Lr / 2 + 2 * s, 2 * s), (xR, 2 * s), s), Track((xR, 2 * s), (xR, yB), s),
           Flash((xR, yB), "rect", pad, pad))
    # serpentine path length pad edge to pad edge, along centre lines
    path = (3 * Lr + 8 * s + 2 * (off) + 2 * (PAD_DY - pad / 2))
    meta = {"s_mil": s_mil, "run_len_in": round(Lr / 25.4, 4), "path_len_in": round(path / 25.4, 4),
            "pads": {"S_A": (xL, yB), "C_L": (xL, yT), "S_B": (xR, yT), "C_R": (xR, yB)}}
    return {"S": S, "C_L": CL, "C_R": CR}, meta


def structure(s_mil, orient):
    """orient 'u': runs along u. 'v': runs along v (rotated 90 deg CCW)."""
    nets, meta = serp_comb(s_mil)
    lab = text(str(s_mil), 0, meta["pads"]["C_L"][1], inch(0.04), mil(8))
    if orient == "v":
        R = Affine.rotate_deg(90)
        nets = {k: transform(v, R) for k, v in nets.items()}
        lab = transform(text(str(s_mil), 0, 0, inch(0.04), mil(8)),
                        Affine.translate(-meta["pads"]["C_L"][1], 0))
        meta["pads"] = {k: R(p) for k, p in meta["pads"].items()}
    meta["orient"] = orient
    return nets, lab, meta


def site(name):
    """Row 1: runs along u, sizes left to right. Row 2: runs along v. Centred on the origin."""
    rows = []
    for orient in ("u", "v"):
        items = [structure(s, orient) for s in SIZES_MIL]
        rows.append(items)
    gap = inch(0.04)
    placed = []
    row_boxes = []
    for items in rows:
        boxes = []
        for nets, lab, meta in items:
            allp = Layer()
            for v in nets.values():
                allp.extend(v)
            boxes.append(bbox(allp))
        w = sum(b[2] - b[0] for b in boxes) + gap * (len(boxes) - 1)
        h = max(b[3] - b[1] for b in boxes)
        row_boxes.append((boxes, w, h))
    label_h = inch(0.08)
    total_h = label_h + row_boxes[0][2] + gap + row_boxes[1][2]
    total_w = max(rb[1] for rb in row_boxes)
    y_top = total_h / 2
    out_nets = []
    lay_labels = Layer()
    lay_labels.add(text(name, 0, y_top - label_h / 2, inch(0.06), mil(10)))
    y_cursor = y_top - label_h
    for (items, (boxes, w, h)) in zip(rows, row_boxes):
        x = -w / 2
        yc = y_cursor - h / 2
        for (nets, lab, meta), b in zip(items, boxes):
            bx = (b[0] + b[2]) / 2
            by = (b[1] + b[3]) / 2
            T = Affine.translate(x + (b[2] - b[0]) / 2 - bx, yc - by)
            out_nets.append(({k: transform(v, T) for k, v in nets.items()},
                             {**meta, "site": name, "centre_mm": T((0.0, 0.0)),
                              "pads": {k: T(p) for k, p in meta["pads"].items()}}))
            lay_labels.add(transform(lab, T))
            x += (b[2] - b[0]) + gap
        y_cursor -= h + gap
    return out_nets, lay_labels, (total_w, total_h)
