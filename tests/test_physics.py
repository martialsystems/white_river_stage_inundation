# Copyright (c) 2026 Martial Systems LLC

import numpy as np
import pytest

from stageflood.errors import ChannelUnlockedError, GateError
from stageflood.config import (
    FIXTURE_DELTA_M,
    GAGE_DATUM_FT_NAVD88,
    NWS_FLOOD_WSE_FT_NAVD88,
    PRIMARY_STAGE_FT,
)
from stageflood.figure import depth_note
from stageflood.physics import paint_wet, relative_height_m, stage_to_wse_m, wse_ft_navd88


def test_wse_is_datum_plus_stage_not_channel() -> None:
    wse_ft = wse_ft_navd88(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    assert abs(wse_ft - 721.51) < 1e-9
    assert abs(wse_ft - NWS_FLOOD_WSE_FT_NAVD88) < 1e-9
    wse_m = stage_to_wse_m(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    datum_m = GAGE_DATUM_FT_NAVD88 * 0.3048
    double_count = relative_height_m(wse_navd88_m=wse_m, h_channel_m=datum_m)
    h_channel = wse_m - FIXTURE_DELTA_M
    delta = relative_height_m(wse_navd88_m=wse_m, h_channel_m=h_channel)
    assert abs(double_count - PRIMARY_STAGE_FT * 0.3048) < 1e-9
    assert abs(delta - FIXTURE_DELTA_M) < 1e-9
    assert abs(h_channel - datum_m) > 1.0
    note = depth_note(
        delta_m=1.0919,
        dem_minus_datum_m=2.2609,
        dem_source="3DEP at the channel",
    )
    assert "Δ = 1.09 m" in note
    assert "2.26 m above gage zero" in note
    assert "3.6 ft of water above the DEM" in note


def test_relative_height_and_paint() -> None:
    wse = stage_to_wse_m(stage_ft=11.0, datum_ft_navd88=710.51)
    h_ch = stage_to_wse_m(stage_ft=0.0, datum_ft_navd88=710.51)
    delta = relative_height_m(wse_navd88_m=wse, h_channel_m=h_ch)
    assert abs(delta - 11.0 * 0.3048) < 1e-9
    hand = np.array([[0.0, 2.0, 4.0], [0.5, np.nan, 1.0]], dtype=np.float64)
    drain = np.array([[True, True, True], [True, True, False]])
    wet = paint_wet(hand, delta_m=delta, drain_to_reach=drain, h_channel_locked=True)
    assert wet[0, 0] == 1
    assert wet[0, 1] == 1
    assert wet[0, 2] == 0  # HAND 4 > 3.35
    assert wet[1, 1] == 255
    assert wet[1, 2] == 255  # off reach


def test_paint_refuses_unlocked_channel() -> None:
    hand = np.zeros((2, 2))
    drain = np.ones((2, 2), dtype=bool)
    with pytest.raises(ChannelUnlockedError):
        paint_wet(hand, delta_m=1.0, drain_to_reach=drain, h_channel_locked=False)


def test_nonfinite_delta_refused() -> None:
    with pytest.raises(GateError):
        relative_height_m(wse_navd88_m=float("nan"), h_channel_m=1.0)
