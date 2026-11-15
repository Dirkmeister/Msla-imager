"""Rounding rule (REQ-023): sizes hold wherever a feature lands."""
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbimager.machine import Machine          # noqa: E402
from pcbimager.raster import Canvas            # noqa: E402
from pcbimager.geom import Track, Flash        # noqa: E402
from pcbimager.units import mil, px_count      # noqa: E402


def test_px_table():
    assert [px_count(mil(s)) for s in (5, 8, 10, 15, 20, 25)] == [3, 4, 5, 8, 11, 13]


def test_track_width_position_independent():
    m = Machine()
    rnd = random.Random(7)
    for _ in range(200):
        c = Canvas(m)
        x, y = rnd.uniform(-40, 40), rnd.uniform(-20, 20)
        c.render([Track((x, y), (x + 5, y), mil(10))])
        col = c.img[:, np.flatnonzero(c.img.any(axis=0))[10]]
        assert col.sum() == 5


def test_rect_pad_size_position_independent():
    m = Machine()
    rnd = random.Random(3)
    for _ in range(200):
        c = Canvas(m)
        c.render([Flash((rnd.uniform(-40, 40), rnd.uniform(-20, 20)), "rect", mil(60), mil(30))])
        ys, xs = np.nonzero(c.img)
        assert (np.ptp(xs) + 1, np.ptp(ys) + 1) == (32, 16)
