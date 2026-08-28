# Copyright (c) 2026 Martial Systems LLC
"""Three refuse laws: sha, h_channel, claims. Verify-before-done is the finish gate."""

from __future__ import annotations

from typing import Any


def laws() -> list[dict[str, Any]]:
    from stageforge.graphs.claim_bans import build_graph as claim_bans
    from stageforge.graphs.h_channel import build_graph as h_channel
    from stageforge.graphs.sibling_sha import build_graph as sibling_sha
    from stageforge.graphs.stage_gate import build_graph as stage_gate

    return [
        {
            "id": "stage.stage_gate",
            "build": stage_gate,
            "state": {
                "current_stage": "0",
                "target_stage": "0",
                "sibling_sha_ok": True,
                "h_channel_locked": False,
                "stage_b_wet": False,
                "huc_wide_wet": False,
            },
            "allow_decisions": ["allow"],
        },
        {
            "id": "stage.sibling_sha",
            "build": sibling_sha,
            "state": {"sibling_sha_ok": True},
            "allow_decisions": ["allow"],
        },
        {
            "id": "stage.h_channel",
            "build": h_channel,
            "state": {"h_channel_locked": True, "delta_finite": True},
            "allow_decisions": ["allow"],
        },
        {
            "id": "stage.claim_bans",
            "build": claim_bans,
            "state": {
                "p_as_forecast": False,
                "hand_as_firm": False,
                "p_as_100yr": False,
                "site_level_flood_risk": False,
            },
            "allow_decisions": ["allow"],
        },
    ]
