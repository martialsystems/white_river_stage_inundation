# Copyright (c) 2026 Martial Systems LLC
"""HAND bathtub: wet iff HAND < (WSE - h_channel) on drain-to-reach cells."""

from __future__ import annotations

import numpy as np

from stageflood.config import FT_TO_M, HYDRO_NODATA, WET_DRY, WET_NODATA, WET_WET
from stageflood.errors import ChannelUnlockedError, GateError


def wse_ft_navd88(*, stage_ft: float, datum_ft_navd88: float) -> float:
    """NAVD88 water-surface elevation in feet: gage zero plus stage."""
    if not np.isfinite(stage_ft) or not np.isfinite(datum_ft_navd88):
        raise GateError("stage and datum must be finite")
    return float(datum_ft_navd88) + float(stage_ft)


def stage_to_wse_m(*, stage_ft: float, datum_ft_navd88: float) -> float:
    return wse_ft_navd88(stage_ft=stage_ft, datum_ft_navd88=datum_ft_navd88) * FT_TO_M


def relative_height_m(*, wse_navd88_m: float, h_channel_m: float) -> float:
    if not np.isfinite(wse_navd88_m) or not np.isfinite(h_channel_m):
        raise GateError("WSE and h_channel must be finite")
    return float(wse_navd88_m) - float(h_channel_m)


def paint_wet(
    hand: np.ndarray,
    *,
    delta_m: float,
    drain_to_reach: np.ndarray,
    h_channel_locked: bool,
) -> np.ndarray:
    """uint8 mask: 1 wet, 0 dry on the reach, 255 HAND-nodata or off-reach."""
    if not h_channel_locked:
        raise ChannelUnlockedError("lock h_channel before painting the wet mask")
    if not np.isfinite(delta_m):
        raise GateError("delta_m is not finite")
    hand_a = np.asarray(hand, dtype=np.float64)
    drain = np.asarray(drain_to_reach, dtype=bool)
    if hand_a.shape != drain.shape:
        raise GateError("HAND and drain-to-reach shapes differ")
    finite = np.isfinite(hand_a) & (hand_a != HYDRO_NODATA)
    out = np.full(hand_a.shape, WET_NODATA, dtype=np.uint8)
    on_reach = drain & finite
    out[on_reach] = np.where(hand_a[on_reach] < float(delta_m), WET_WET, WET_DRY)
    return out
