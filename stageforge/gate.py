# Copyright (c) 2026 Martial Systems LLC
"""Call sites for the three refuse laws."""

from __future__ import annotations

from typing import Any

from stageforge._bootstrap import ensure_paths

ensure_paths()

from graphforge.product_law import require_law

from stageforge.graphs.claim_bans import build_graph as build_claim_bans
from stageforge.graphs.h_channel import build_graph as build_h_channel
from stageforge.graphs.sibling_sha import build_graph as build_sibling_sha
from stageforge.graphs.stage_gate import build_graph as build_stage_gate


def require_stage(
    *,
    current_stage: str = "0",
    target_stage: str = "0",
    sibling_sha_ok: bool = False,
    h_channel_locked: bool = False,
    stage_b_wet: bool = False,
    huc_wide_wet: bool = False,
    thread_id: str = "stage_stage",
) -> None:
    require_law(
        build_stage_gate(),
        {
            "current_stage": current_stage,
            "target_stage": target_stage,
            "sibling_sha_ok": sibling_sha_ok,
            "h_channel_locked": h_channel_locked,
            "stage_b_wet": stage_b_wet,
            "huc_wide_wet": huc_wide_wet,
        },
        allow_decisions=["allow"],
        law_id="stage.stage_gate",
        thread_id=thread_id,
        raise_error=True,
    )


def require_sibling(*, sibling_sha_ok: bool, thread_id: str = "stage_sha") -> None:
    require_law(
        build_sibling_sha(),
        {"sibling_sha_ok": sibling_sha_ok},
        allow_decisions=["allow"],
        law_id="stage.sibling_sha",
        thread_id=thread_id,
        raise_error=True,
    )


def require_h_channel(
    *,
    h_channel_locked: bool,
    delta_finite: bool,
    thread_id: str = "stage_h",
) -> None:
    require_law(
        build_h_channel(),
        {"h_channel_locked": h_channel_locked, "delta_finite": delta_finite},
        allow_decisions=["allow"],
        law_id="stage.h_channel",
        thread_id=thread_id,
        raise_error=True,
    )


def require_claims(**flags: Any) -> None:
    thread_id = str(flags.pop("thread_id", "stage_claims"))
    state = {
        "p_as_forecast": False,
        "hand_as_firm": False,
        "p_as_100yr": False,
        "site_level_flood_risk": False,
    }
    state.update(flags)
    require_law(
        build_claim_bans(),
        state,
        allow_decisions=["allow"],
        law_id="stage.claim_bans",
        thread_id=thread_id,
        raise_error=True,
    )
