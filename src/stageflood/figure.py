# Copyright (c) 2026 Martial Systems LLC
"""Three-panel interview figure: SFHA, calibrated P, stage wet."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from stageflood.claims import require_clean
from stageflood.config import P_DEFINITION, P_HEADLINE_T, SFHA_CODES, WET_WET
from stageflood.errors import GateError


def write_three_panel(
    dest: Path,
    *,
    wet: np.ndarray,
    zone: np.ndarray,
    p_cal: np.ndarray,
    drain_to_reach: np.ndarray,
    title: str,
    huc_cell_count: int | None = None,
) -> Path:
    require_clean(title, source="figure_title")
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
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.3))
    panels = (
        (axes[0], sfha, "SFHA: floodway ∪ SFHA on the window", "viridis", 0.0, 1.0),
        (
            axes[1],
            p_show,
            f"{P_DEFINITION} ≥ {P_HEADLINE_T}: map-completion,\nnot water at 11 ft",
            "plasma",
            0.0,
            1.0,
        ),
        (axes[2], wet_b, "Stage wet: HAND inundation\nat NWS flood stage", "cividis", 0.0, 1.0),
    )
    footer = f"{P_DEFINITION} ≥ {P_HEADLINE_T} is sibling map-completion, not water at 11 ft."
    require_clean(footer, source="figure_footer")
    for ax, data, lab, cmap, vmin, vmax in panels:
        require_clean(lab, source="figure_panel")
        ax.imshow(data, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_title(lab, fontsize=8)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(title)
    fig.subplots_adjust(bottom=0.14, top=0.82, wspace=0.12)
    fig.text(0.5, 0.04, footer, ha="center", fontsize=8)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=120)
    plt.close(fig)
    return dest
