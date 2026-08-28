# Copyright (c) 2026 Martial Systems LLC

import numpy as np
import pytest

from stageflood.errors import ChannelUnlockedError, GateError
from stageflood.physics import paint_wet, relative_height_m, stage_to_wse_m


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
