# Copyright (c) 2026 Martial Systems LLC
"""Three-layer counts on the reach. P is a map layer, not a score target."""

from __future__ import annotations

import numpy as np

from stageflood.config import (
    P_DEFINITION,
    P_HEADLINE_T,
    SFHA_CODES,
    WET_NODATA,
    WET_WET,
    ZONE_UNSHADED_X,
)
from stageflood.errors import GateError


def overlap_table(
    *,
    wet: np.ndarray,
    zone: np.ndarray,
    p_cal: np.ndarray,
    drain_to_reach: np.ndarray,
    p_t: float = P_HEADLINE_T,
) -> dict[str, object]:
    drain = np.asarray(drain_to_reach, dtype=bool)
    if not drain.any():
        raise GateError("drain-to-reach is empty")
    if drain.sum() == drain.size:
        raise GateError("C refuses a HUC-wide wet/reach mask")
    w = np.asarray(wet)
    z = np.asarray(zone)
    p = np.asarray(p_cal, dtype=np.float64)
    on = drain & (w != WET_NODATA)
    n = int(on.sum())
    if n == 0:
        raise GateError("no comparable cells on the reach")
    sfha = np.isin(z, list(SFHA_CODES))
    p_hi = np.isfinite(p) & (p >= float(p_t))
    wet_b = w == WET_WET
    a = sfha & on
    b = p_hi & on
    c = wet_b & on

    def _iou(x: np.ndarray, y: np.ndarray) -> float:
        inter = int((x & y).sum())
        union = int((x | y).sum())
        return float(inter / union) if union else 0.0

    return {
        "p_definition": P_DEFINITION,
        "p_is_forecast": False,
        "p_headline_t": float(p_t),
        "n_reach_comparable": n,
        "n_sfha": int(a.sum()),
        "n_p_ge_t": int(b.sum()),
        "n_stage_wet": int(c.sum()),
        "n_sfha_and_wet": int((a & c).sum()),
        "n_sfha_dry_at_stage": int((a & ~c).sum()),
        "n_wet_unshaded_x": int((c & (z == ZONE_UNSHADED_X)).sum()),
        "iou_sfha_wet": _iou(a, c),
        "iou_p_wet": _iou(b, c),
        "iou_sfha_p": _iou(a, b),
    }
