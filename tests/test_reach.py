# Copyright (c) 2026 Martial Systems LLC

import numpy as np
import pytest

from stageflood.errors import GateError
from stageflood.fixture import drain_truth, flowdir_south_then_east, reach_stream_mask
from stageflood.reach import drain_to_reach


def test_tributary_not_in_drain_to_reach() -> None:
    fd = flowdir_south_then_east()
    reach = reach_stream_mask()
    valid = np.ones(fd.shape, dtype=bool)
    drain = drain_to_reach(fd, reach, valid)
    assert np.array_equal(drain, drain_truth())
    assert not drain[:, 0].any()
    assert drain[:, 8].all()


def test_empty_reach_refused() -> None:
    fd = np.zeros((3, 3), dtype=np.int8)
    with pytest.raises(GateError):
        drain_to_reach(fd, np.zeros((3, 3), dtype=bool), np.ones((3, 3), dtype=bool))
