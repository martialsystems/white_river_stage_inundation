# Copyright (c) 2026 Martial Systems LLC

import numpy as np
import pytest

from stageflood.errors import GateError
from stageflood.fixture import drain_truth, flowdir_south_then_east, reach_stream_mask
from stageflood.reach import along_stream_mask, drain_to_reach, nearest_cell


def test_tributary_not_in_drain_to_reach() -> None:
    fd = flowdir_south_then_east()
    reach = reach_stream_mask()
    valid = np.ones(fd.shape, dtype=bool)
    drain = drain_to_reach(fd, reach, valid)
    assert np.array_equal(drain, drain_truth())
    assert not drain[:, 0].any()
    assert drain[:, 16].all()


def test_along_stream_clips_distance() -> None:
    stream = np.zeros((3, 21), dtype=bool)
    stream[1, :] = True
    mask = along_stream_mask(stream, start=(1, 10), max_m=90.0, cellsize=30.0)
    assert mask[1, 10]
    assert mask[1, 13]
    assert not mask[1, 14]
    assert not mask[1, 0]
    r, c, d = nearest_cell(stream, 0, 10)
    assert (r, c) == (1, 10)


def test_empty_reach_refused() -> None:
    fd = np.zeros((3, 3), dtype=np.int8)
    with pytest.raises(GateError):
        drain_to_reach(fd, np.zeros((3, 3), dtype=bool), np.ones((3, 3), dtype=bool))
