"""Converter v0 (REQ-022): Gerber + Excellon or SVG in; panelize; side mirror; invert;
1-bit PNG per layer out, as an IF-13 job.

Placement: the board outline (Edge.Cuts) bounding box is centred on the panel centre, then the
optional rotation (90-degree steps) and offset are applied. Both sides use the same placement,
so front-to-back registration depends only on the flip and the calibration.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .geom import Layer, Affine, transform, bbox
from .machine import Machine, Calibration
from .units import inch, mil, mm_to_in
from .font import text
from .orient import render_topview, face_to_top_view
from .job import write_job
from . import gerber_in, svg_in


@dataclass
class LayerSpec:
    path: str
    side: str                  # 'top' or 'bottom'
    fmt: str = "gerber"        # 'gerber' or 'svg'
    kind: str = "copper"       # 'copper' or 'mask' (label only for now)
    invert: bool = False


@dataclass
class Result:
    job_dir: Path
    images: dict = field(default_factory=dict)       # side -> image-frame bool array
    placement: Affine = None
    report: dict = field(default_factory=dict)


def template_mark(machine, side, job_id, kind="copper"):
    """One line in the guard band along the near edge, as read on `side`'s face, converted to
    top view. 'CU' for copper layers is the polarity mark: it must etch as copper."""
    g = machine.guard_in
    v = -(mm_to_in(machine.image_v_mm) / 2 - g / 2)
    u0 = -mm_to_in(machine.image_u_mm) / 2 + g + 0.05
    tag = "CU" if kind == "copper" else "SM"
    face = Layer()
    face.add(text(f"F {tag} {'TOP' if side == 'top' else 'BOT'} {job_id.upper()}",
                  inch(u0), inch(v), inch(0.050), mil(10), anchor="l"))
    return transform(face, face_to_top_view(machine, side))


def load(spec, stats):
    if spec.fmt == "gerber":
        return gerber_in.read_gerber(spec.path, stats), None
    lay, outline, vb, st = svg_in.read_svg(spec.path)
    stats.update(st)
    return lay, (outline or vb)


def convert(job_id, layers, outdir, outline=None, drill=None, rotate_deg=0, offset_in=(0.0, 0.0),
            machine=None, calibration=None, template=True, time_scale=1.0, write=True, label=None):
    m = machine or Machine()
    cal = calibration or Calibration()
    rep = {"layers": [], "warnings": []}
    loaded = []
    ref = None
    for spec in layers:
        st = {}
        lay, svg_ref = load(spec, st)
        loaded.append((spec, lay))
        rep["layers"].append({"path": str(spec.path), "side": spec.side, "fmt": spec.fmt,
                              "invert": spec.invert, "objects": st})
        if svg_ref and ref is None:
            ref = svg_ref
    if outline:
        ref = gerber_in.read_outline_bbox(outline)
        rep["reference"] = "Edge.Cuts outline"
    elif ref is not None:
        rep["reference"] = "SVG outline colour or viewBox"
    else:
        allp = Layer()
        for _, lay in loaded:
            allp.extend(lay)
        ref = bbox(allp)
        rep["reference"] = "copper bounding box (no outline given)"
        rep["warnings"].append("no outline: sides are centred on their combined copper bbox")
    cx, cy = (ref[0] + ref[2]) / 2, (ref[1] + ref[3]) / 2
    T = (Affine.translate(inch(offset_in[0]), inch(offset_in[1])) @ Affine.rotate_deg(rotate_deg)
         @ Affine.translate(-cx, -cy))
    w, h = ref[2] - ref[0], ref[3] - ref[1]
    if rotate_deg % 180:
        w, h = h, w
    bw, bh = m.board_area_mm
    rep["board_in"] = [round(mm_to_in(w), 4), round(mm_to_in(h), 4)]
    rep["board_area_in"] = [round(mm_to_in(bw), 4), round(mm_to_in(bh), 4)]
    tol = inch(0.001)
    if w > bw + tol or h > bh + tol:
        rep["warnings"].append(f"board {rep['board_in']} in exceeds the v1 board area "
                               f"{rep['board_area_in']} in (REQ-020)")
    res = Result(job_dir=None, placement=T, report=rep)
    exposures = []
    for spec, lay in loaded:
        L = transform(lay, T)
        if template:
            L.extend(template_mark(m, spec.side, label or job_id, spec.kind))
        log = {}
        img = render_topview(m, L, spec.side, cal, canvas_log=log)
        if spec.invert:
            img = ~img
        res.images[(spec.side, spec.kind)] = img
        exposures.append({"id": f"{spec.side}-{spec.kind}", "side": spec.side, "kind": "exposure",
                          "layer": spec.kind, "source": Path(spec.path).name, "invert": spec.invert,
                          "time": {"mode": "nominal", "scale": time_scale},
                          "_frames": [(0.0, img)],
                          "prompt": f"Panel {spec.side} face down on the pins, press plate on, lid "
                                    "closed, then start."})
        rep["layers"][len(exposures) - 1]["render"] = log
    holes = []
    if drill:
        for x, y, d in gerber_in.read_drills(drill):
            u, v = T((x, y))
            holes.append([round(mm_to_in(u), 5), round(mm_to_in(v), 5), round(mm_to_in(d), 5)])
        rep["holes"] = len(holes)
    if write:
        extra = {"placement": {"reference_bbox_mm": [round(x, 6) for x in ref],
                               "rotate_deg": rotate_deg, "offset_in": list(offset_in)},
                 "converter_report": rep}
        if holes:
            extra["drills_panel_in"] = {"origin": "panel centre, top view, u right, v up",
                                        "holes": holes}
        res.job_dir = write_job(outdir, job_id, exposures, m, cal,
                                purpose={"test": "board", "notes": "converted by pcbimager.convert"},
                                extra=extra)
    return res
