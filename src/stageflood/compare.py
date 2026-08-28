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
    huc_cell_count: int | None = None,
) -> dict[str, object]:
    drain = np.asarray(drain_to_reach, dtype=bool)
    if not drain.any():
        raise GateError("drain-to-reach is empty")
    if huc_cell_count is not None:
        if drain.size >= int(huc_cell_count):
            raise GateError("C refuses a HUC-wide wet/reach mask")
    elif int(drain.sum()) == drain.size:
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
        "iou_universe": "drain-to-reach",
        "iou_sfha_wet": _iou(a, c),
        "iou_p_wet": _iou(b, c),
        "iou_sfha_p": _iou(a, b),
    }


def pair_fill_sentence(*, baseline: dict, later: dict) -> str:
    """One sentence: leftover SFHA fill vs unshaded X, IoU on drain-to-reach."""
    extra = int(later["n_stage_wet"]) - int(baseline["n_stage_wet"])
    dry0 = int(baseline["n_sfha_dry_at_stage"])
    dry1 = int(later["n_sfha_dry_at_stage"])
    x0 = int(baseline["n_wet_unshaded_x"])
    x1 = int(later["n_wet_unshaded_x"])
    iou0 = float(baseline["iou_sfha_wet"])
    iou1 = float(later["iou_sfha_wet"])
    return (
        f"Extra {extra} wet cells filled leftover SFHA (dry {dry0} to {dry1}); "
        f"unshaded X wet {x0} to {x1}. "
        f"IoU {iou0:.2f} to {iou1:.2f} on drain-to-reach."
    )
