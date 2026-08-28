# Copyright (c) 2026 Martial Systems LLC

import numpy as np

from stageflood.d8 import d8_flowdir, flowdir_from_dem, priority_flood_fill
from stageflood.reach import drain_to_reach


def test_hillslope_drains_to_burned_channel() -> None:
    dem = np.array(
        [
            [5.0, 5.0, 5.0],
            [3.0, 3.0, 3.0],
            [2.0, 1.0, 2.0],
        ],
        dtype=np.float64,
    )
    stream = np.array(
        [
            [False, False, False],
            [False, False, False],
            [False, True, False],
        ]
    )
    valid = np.ones(dem.shape, dtype=bool)
    fd = flowdir_from_dem(dem, stream, valid, burn_m=50.0, cellsize=30.0)
    drain = drain_to_reach(fd, stream, valid)
    assert drain[0, 1]
    assert drain[2, 1]


def test_fill_raises_a_pit() -> None:
    dem = np.array([[3.0, 3.0, 3.0], [3.0, 0.0, 3.0], [3.0, 3.0, 3.0]])
    valid = np.ones(dem.shape, dtype=bool)
    filled = priority_flood_fill(dem, valid, seed_mask=None)
    assert filled[1, 1] >= filled[0, 1]
    fd = d8_flowdir(filled, valid, 30.0)
    assert fd.shape == dem.shape
