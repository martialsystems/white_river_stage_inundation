# Copyright (c) 2026 Martial Systems LLC
"""Three-panel interview figure: SFHA, calibrated P, stage wet."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from stageflood.claims import require_clean
from stageflood.config import (
    FT_TO_M,
    GAGE_ID,
    P_DEFINITION,
    P_HEADLINE_T,
    PRIMARY_STAGE_FT,
    PRIMARY_STAGE_LABEL,
    SFHA_CODES,
    WET_WET,
)
from stageflood.errors import GateError


def stage_txt(stage_ft: float) -> str:
    h = float(stage_ft)
    if abs(h - round(h)) < 1e-9:
        return f"{h:.0f}"
    return f"{h:.2f}"


def depth_note(
    *,
    delta_m: float,
    dem_minus_datum_m: float,
    stage_ft: float = PRIMARY_STAGE_FT,
    dem_source: str,
) -> str:
    """Caption Δ as water above the DEM, not stage-as-depth."""
    above_ft = float(delta_m) / FT_TO_M
    unresolved_ft = float(stage_ft) - above_ft
    st = stage_txt(stage_ft)
    return (
        f"Δ = {float(delta_m):.2f} m ({above_ft:.1f} ft of water above the DEM). "
        f"{dem_source} is {float(dem_minus_datum_m):.2f} m above gage zero. "
        f"{unresolved_ft:.1f} ft of the {st} ft stage is inside the unresolved channel."
    )


def reach_title(
    *,
    wse_ft: float,
    stage_ft: float = PRIMARY_STAGE_FT,
    stage_label: str = PRIMARY_STAGE_LABEL,
) -> str:
    return (
        f"{GAGE_ID} {stage_label} {stage_txt(stage_ft)} ft: "
        f"cells below {float(wse_ft):.2f} ft WSE on the reach"
    )


def reach_footer(*, iou_sfha_wet: float, stage_ft: float = PRIMARY_STAGE_FT) -> str:
    return (
        f"{P_DEFINITION} ≥ {P_HEADLINE_T} is sibling map-completion, "
        f"not water at {stage_txt(stage_ft)} ft. "
        f"IoU SFHA vs stage wet = {float(iou_sfha_wet):.2f} on drain-to-reach cells only."
    )


def write_three_panel(
    dest: Path,
    *,
    wet: np.ndarray,
    zone: np.ndarray,
    p_cal: np.ndarray,
    drain_to_reach: np.ndarray,
    title: str,
    delta_line: str,
    footer: str,
    huc_cell_count: int | None = None,
    stage_ft: float = PRIMARY_STAGE_FT,
    wet_caption: str = "Stage wet: HAND inundation\nat NWS flood stage",
) -> Path:
    require_clean(title, source="figure_title")
    require_clean(delta_line, source="figure_delta")
    require_clean(footer, source="figure_footer")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    drain = np.asarray(drain_to_reach, dtype=bool)
    if huc_cell_count is not None:
        if drain.size >= int(huc_cell_count):
            raise GateError("figure refuses a HUC-wide reach mask")
    elif drain.all():
        raise GateError("figure refuses a HUC-wide reach mask")
    sfha = np.isin(zone, list(SFHA_CODES)).astype(float)
    p = np.asarray(p_cal, dtype=np.float64)
    p_show = np.where(np.isfinite(p), p, np.nan)
    wet_b = (np.asarray(wet) == WET_WET).astype(float)
    for arr in (sfha, p_show, wet_b):
        arr[~drain] = np.nan
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 5.2))
    panels = (
        (axes[0], sfha, "SFHA: floodway ∪ SFHA on the window", "viridis", 0.0, 1.0),
        (
            axes[1],
            p_show,
            f"{P_DEFINITION} ≥ {P_HEADLINE_T}: map-completion,\nnot water at {stage_txt(stage_ft)} ft",
            "plasma",
            0.0,
            1.0,
        ),
        (axes[2], wet_b, wet_caption, "cividis", 0.0, 1.0),
    )
    for ax, data, lab, cmap, vmin, vmax in panels:
        require_clean(lab, source="figure_panel")
        ax.imshow(data, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_title(lab, fontsize=8)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(title, fontsize=11)
    fig.text(0.5, 0.88, delta_line, ha="center", fontsize=8, wrap=True)
    fig.subplots_adjust(bottom=0.14, top=0.80, wspace=0.12)
    fig.text(0.5, 0.04, footer, ha="center", fontsize=8)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=120)
    plt.close(fig)
    return dest
