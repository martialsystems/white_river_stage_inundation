# Copyright (c) 2026 Martial Systems LLC
"""Refuse P-as-forecast and HAND-as-FIRM claims."""

from __future__ import annotations

from typing import Any

from stageforge._bootstrap import ensure_paths

ensure_paths()

from graphforge import END, START, StateGraph, last_value, operator_add
from graphforge.state import ChannelSpec, StateSchema


def _schema() -> StateSchema:
    return StateSchema.from_specs(
        [
            ChannelSpec("p_as_forecast", last_value, default=False),
            ChannelSpec("hand_as_firm", last_value, default=False),
            ChannelSpec("p_as_100yr", last_value, default=False),
            ChannelSpec("site_level_flood_risk", last_value, default=False),
            ChannelSpec("violations", last_value, default=[]),
            ChannelSpec("decision", last_value, default=None),
            ChannelSpec("events", operator_add, default=[]),
        ]
    )


def _evaluate(state: dict[str, Any]) -> dict[str, Any]:
    flags = (
        ("p_as_forecast", "p_as_forecast"),
        ("hand_as_firm", "hand_as_firm"),
        ("p_as_100yr", "p_as_100yr"),
        ("site_level_flood_risk", "site_level_flood_risk"),
    )
    violations = [code for key, code in flags if state.get(key)]
    return {
        "violations": violations,
        "events": [
            {"node": "evaluate", "ok": len(violations) == 0, "violations": list(violations)}
        ],
    }


def build_graph() -> StateGraph:
    g = StateGraph(_schema(), name="stage.claim_bans")

    def allow(state: dict[str, Any]) -> dict[str, Any]:
        del state
        return {"decision": "allow", "events": [{"node": "allow"}]}

    def block(state: dict[str, Any]) -> dict[str, Any]:
        return {
            "decision": "block",
            "events": [{"node": "block", "violations": state.get("violations") or []}],
        }

    def route(state: dict[str, Any]) -> str:
        return "ok" if not (state.get("violations") or []) else "bad"

    g.add_node("evaluate", _evaluate)
    g.add_node("allow", allow)
    g.add_node("block", block)
    g.add_edge(START, "evaluate")
    g.add_conditional_edges("evaluate", route, {"ok": "allow", "bad": "block"})
    g.add_edge("allow", END)
    g.add_edge("block", END)
    return g
