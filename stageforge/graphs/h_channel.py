# Copyright (c) 2026 Martial Systems LLC
"""Refuse wet mask before h_channel is locked and Δ is finite."""

from __future__ import annotations

from typing import Any

from stageforge._bootstrap import ensure_paths

ensure_paths()

from graphforge import END, START, StateGraph, last_value, operator_add
from graphforge.state import ChannelSpec, StateSchema


def _schema() -> StateSchema:
    return StateSchema.from_specs(
        [
            ChannelSpec("h_channel_locked", last_value, default=False),
            ChannelSpec("delta_finite", last_value, default=False),
            ChannelSpec("violations", last_value, default=[]),
            ChannelSpec("decision", last_value, default=None),
            ChannelSpec("events", operator_add, default=[]),
        ]
    )


def _evaluate(state: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    if not bool(state.get("h_channel_locked")):
        violations.append("h_channel_unlocked")
    if not bool(state.get("delta_finite")):
        violations.append("delta_not_finite")
    return {
        "violations": violations,
        "events": [{"node": "evaluate", "ok": not violations, "violations": list(violations)}],
    }


def build_graph() -> StateGraph:
    g = StateGraph(_schema(), name="stage.h_channel")

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
