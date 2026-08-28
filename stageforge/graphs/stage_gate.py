# Copyright (c) 2026 Martial Systems LLC
"""Refuse stage skips and paint without sha / h_channel."""

from __future__ import annotations

from typing import Any

from stageforge._bootstrap import ensure_paths

ensure_paths()

from graphforge import END, START, StateGraph, last_value, operator_add
from graphforge.state import ChannelSpec, StateSchema

_ORDER = ("0", "A", "B", "C")


def _rank(stage: Any) -> int:
    try:
        return _ORDER.index(str(stage or "0"))
    except ValueError:
        return -1


def _schema() -> StateSchema:
    return StateSchema.from_specs(
        [
            ChannelSpec("current_stage", last_value, default="0"),
            ChannelSpec("target_stage", last_value, default="0"),
            ChannelSpec("sibling_sha_ok", last_value, default=False),
            ChannelSpec("h_channel_locked", last_value, default=False),
            ChannelSpec("stage_b_wet", last_value, default=False),
            ChannelSpec("huc_wide_wet", last_value, default=False),
            ChannelSpec("violations", last_value, default=[]),
            ChannelSpec("decision", last_value, default=None),
            ChannelSpec("events", operator_add, default=[]),
        ]
    )


def _evaluate(state: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    current = str(state.get("current_stage") or "0")
    target = str(state.get("target_stage") or "0")
    cr, tr = _rank(current), _rank(target)
    if cr < 0 or tr < 0:
        violations.append("unknown_stage")
    if tr > cr + 1:
        violations.append("stage_skip")
    if tr >= _rank("A") and not bool(state.get("sibling_sha_ok")):
        violations.append("advance_without_sibling_sha")
    if tr >= _rank("B") and not bool(state.get("h_channel_locked")):
        violations.append("paint_without_h_channel")
    if tr >= _rank("C"):
        if not bool(state.get("stage_b_wet")):
            violations.append("compare_without_wet")
        if bool(state.get("huc_wide_wet")):
            violations.append("huc_wide_wet")
    ok = len(violations) == 0
    return {
        "violations": violations,
        "events": [{"node": "evaluate", "ok": ok, "violations": list(violations)}],
    }


def build_graph() -> StateGraph:
    g = StateGraph(_schema(), name="stage.stage_gate")

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
