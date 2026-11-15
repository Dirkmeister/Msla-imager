"""SVG reader (KiCad 'Plot to SVG' / kicad-cli pcb export svg) -> Layer in top view (mm, y up).

Export each copper layer together with Edge.Cuts, colour mode (not black and white), page size
'board area only'. Elements are split by colour: the outline colour (KiCad default #D0D2CD) gives
the board reference; the copper colour (most common remaining colour) is the layer; black is
drill marks and is ignored. Invisible <text> (KiCad adds it for search) is ignored.

Mapping to the rounding rule:
  stroked straight segments -> Track (R1). Curves -> Tracks, not snapped (R4).
  filled <circle>           -> Flash circle (R1)
  filled paths (pads, polygons) -> Region (R2): pad sizes come out +/- 1 px. SVG carries no
  flash semantics, which is the main thing this path loses against Gerber. It also has no drills.
"""
from collections import Counter

from svgelements import SVG, Shape, Path, Circle, Text, Move, Line, Close, Color

from .geom import Layer, Track, Flash, Region

OUTLINE_COLOUR = "#d0d2cd"
DRILL_COLOUR = "#000000"


def _hex(c):
    if c is None or c.value is None:
        return None
    return Color(c).hex[:7].lower()


def _visible_fill(e):
    return e.fill is not None and e.fill.value is not None and e.fill.opacity > 0


def _subpaths(path):
    """(points, curved) for each subpath; curves approximated at 0.02 mm steps."""
    out, cur, curved = [], [], False
    for seg in path.segments():
        if isinstance(seg, Move):
            if len(cur) > 1:
                out.append((cur, curved))
            cur, curved = [(seg.end.x, seg.end.y)], False
        elif isinstance(seg, Line):
            cur.append((seg.end.x, seg.end.y))
        elif isinstance(seg, Close):
            if cur:
                cur.append(cur[0])
                out.append((cur, curved))
            cur, curved = [], False
        else:
            curved = True
            L = seg.length(error=1e-4)
            n = max(2, int(L / 0.02) + 1)
            for k in range(1, n + 1):
                q = seg.point(k / n)
                cur.append((q.x, q.y))
    if len(cur) > 1:
        out.append((cur, curved))
    return out


def read_svg(path, copper_colour=None):
    """Returns (layer, outline_bbox_or_None, viewbox, stats). Coordinates mm, y up
    (SVG y is negated), relative to the SVG origin."""
    svg = SVG.parse(str(path), ppi=25.4, reify=True)
    elems = [e for e in svg.elements() if isinstance(e, Shape) and not isinstance(e, Text)]
    colours = Counter()
    for e in elems:
        col = _hex(e.fill) if _visible_fill(e) else _hex(e.stroke)
        if col:
            colours[col] += 1
    if copper_colour is None:
        cand = [c for c, _ in colours.most_common() if c not in (OUTLINE_COLOUR, DRILL_COLOUR)]
        copper_colour = cand[0] if cand else DRILL_COLOUR
    lay = Layer()
    oxs, oys = [], []
    st = Counter()
    for e in elems:
        fill = _visible_fill(e)
        col = _hex(e.fill) if fill else _hex(e.stroke)
        sw = e.stroke_width if (e.stroke is not None and e.stroke.value is not None) else 0.0
        if col == OUTLINE_COLOUR:
            for pts, _ in _subpaths(Path(e)):
                oxs += [p[0] for p in pts]
                oys += [-p[1] for p in pts]
            continue
        if col != copper_colour:
            st["skipped_" + str(col)] += 1
            continue
        if isinstance(e, Circle) and fill:
            r = (e.rx + e.ry) / 2
            lay.append(Flash((e.cx, -e.cy), "circle", 2 * r))
            st["circle"] += 1
            continue
        sp = _subpaths(Path(e))
        if fill:
            rings = [[(x, -y) for x, y in pts] for pts, _ in sp if len(pts) >= 3]
            if rings:
                lay.append(Region(rings))
                st["fill"] += 1
        if sw and sw > 0:
            for pts, curved in sp:
                for a, b in zip(pts, pts[1:]):
                    lay.append(Track((a[0], -a[1]), (b[0], -b[1]), sw, snap=not curved))
                st["stroke"] += 1
    vb = svg.viewbox
    outline = (min(oxs), min(oys), max(oxs), max(oys)) if oxs else None
    return lay, outline, (vb.x, -vb.y - vb.height, vb.x + vb.width, -vb.y), dict(st)
