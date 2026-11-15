"""IF-13 job folders (PC -> Pi). Spec: docs/IF-13.md.

<job_id>/
  job.json      manifest
  e1_f00.png    frames: 1-bit grayscale PNG, native framebuffer size and orientation, lit = 1
  ...
"""
import datetime as _dt
import hashlib
import json
from pathlib import Path

import numpy as np

from . import __version__
from .machine import Machine, Calibration
from .raster import to_native, save_png_1bit, load_png_bool, png_header

IF13_VERSION = "0.1"


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _now():
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def exposure_from_pattern(pat, eid="E1", prompt=None):
    return {"id": eid, "side": pat.side, "kind": pat.kind,
            "time": ({"mode": "fixed", "end_s": pat.end_s} if pat.time_mode == "fixed" and pat.end_s
                     else {"mode": "nominal", "scale": 1.0} if pat.time_mode == "nominal"
                     else {"mode": "operator"} if pat.time_mode == "fixed"
                     else {"mode": "none"}),
            "_frames": pat.frames,
            "prompt": prompt or _default_prompt(pat.side, pat.kind)}


def _default_prompt(side, kind):
    if kind == "display":
        return "Display only. UV stays off."
    face = {"top": "top face", "bottom": "bottom face"}.get(side, "copper")
    return f"Panel {face} down on the pins, press plate on, lid closed, then start."


def write_job(outdir, job_id, exposures, machine, calibration=None, purpose=None, zones=None,
              extra=None):
    """exposures: list of dicts from exposure_from_pattern (or equivalent) with '_frames'
    = [(t_s, image-frame bool array)]. Writes frames in native orientation."""
    calibration = calibration or Calibration()
    d = Path(outdir) / job_id
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.png"):
        old.unlink()
    manifest = {
        "format": "IF-13", "version": IF13_VERSION, "job_id": job_id, "created": _now(),
        "generator": f"pcb-imager {__version__}",
        "purpose": purpose or {},
        "machine": machine.to_dict(),
        "calibration": calibration.to_dict(),
        "polarity": "lit = material stays (copper on negative dry film)",
        "frame_format": {"type": "png", "bit_depth": 1, "width": machine.native_w,
                         "height": machine.native_h, "lit": 1},
        "exposures": [],
    }
    for ei, ex in enumerate(exposures, 1):
        frames = []
        times = [t for t, _ in ex["_frames"]]
        if times[0] != 0.0 or any(b < a for a, b in zip(times, times[1:])):
            raise ValueError("frame times must start at 0 and not decrease")
        for k, (t, img) in enumerate(ex["_frames"]):
            fn = f"e{ei}_f{k:02d}.png"
            save_png_1bit(to_native(img, machine), d / fn)
            frames.append({"t_s": t, "file": fn, "sha256": _sha256(d / fn),
                           "lit_px": int(np.count_nonzero(img))})
        e = {k: v for k, v in ex.items() if not k.startswith("_")}
        e["frames"] = frames
        manifest["exposures"].append(e)
    if zones:
        manifest["zones"] = zones
    if extra:
        manifest.update(extra)
    (d / "job.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return d


def verify_job(jobdir):
    """Checks a job folder the way the Pi loader will. Returns a list of problems (empty = OK)."""
    d = Path(jobdir)
    probs = []
    man = json.loads((d / "job.json").read_text())
    if man.get("format") != "IF-13":
        probs.append("format is not IF-13")
    ff = man["frame_format"]
    for e in man["exposures"]:
        ts = [f["t_s"] for f in e["frames"]]
        if ts[0] != 0.0:
            probs.append(f"{e['id']}: first frame not at 0 s")
        if any(b < a for a, b in zip(ts, ts[1:])):
            probs.append(f"{e['id']}: frame times decrease")
        if e["time"]["mode"] == "fixed" and e["time"]["end_s"] < ts[-1]:
            probs.append(f"{e['id']}: end before last frame")
        for f in e["frames"]:
            p = d / f["file"]
            if not p.exists():
                probs.append(f"missing {f['file']}")
                continue
            if _sha256(p) != f["sha256"]:
                probs.append(f"checksum {f['file']}")
            w, h, bd, ct = png_header(p)
            if (w, h, bd, ct) != (ff["width"], ff["height"], 1, 0):
                probs.append(f"{f['file']}: {w}x{h} depth {bd} type {ct}")
    return probs
