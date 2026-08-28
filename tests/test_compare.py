# Copyright (c) 2026 Martial Systems LLC

import numpy as np
import pytest

from stageflood.compare import overlap_table
from stageflood.config import ZONE_SFHA, ZONE_UNSHADED_X
from stageflood.errors import GateError


def test_overlap_counts_and_refuses_huc_wide() -> None:
    wet = np.array([[1, 1, 0], [1, 255, 0]], dtype=np.uint8)
    zone = np.array(
        [[ZONE_SFHA, ZONE_UNSHADED_X, ZONE_UNSHADED_X], [ZONE_SFHA, ZONE_UNSHADED_X, ZONE_SFHA]],
        dtype=np.uint8,
    )
    p = np.array([[0.9, 0.8, 0.1], [0.2, 0.9, 0.9]], dtype=np.float64)
    drain = np.array([[True, True, True], [True, True, False]])
    t = overlap_table(wet=wet, zone=zone, p_cal=p, drain_to_reach=drain)
    assert t["p_is_forecast"] is False
    assert t["n_stage_wet"] == 3
    assert t["n_wet_unshaded_x"] == 1
    assert t["n_sfha_dry_at_stage"] == 0
    assert t["iou_universe"] == "drain-to-reach"
    with pytest.raises(GateError):
        overlap_table(
            wet=wet,
            zone=zone,
            p_cal=p,
            drain_to_reach=np.ones(wet.shape, dtype=bool),
        )
