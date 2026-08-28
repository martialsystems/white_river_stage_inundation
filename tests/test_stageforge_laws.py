# Copyright (c) 2026 Martial Systems LLC

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from stageforge._bootstrap import ensure_paths

ensure_paths()

from graphforge.product_law import LawBlockedError

from stageforge.gate import require_claims, require_h_channel, require_sibling, require_stage
from stageforge.product_laws import laws


def test_stage_gate_allows_zero() -> None:
    require_stage(current_stage="0", target_stage="0", thread_id="t.s0")


def test_stage_gate_blocks_skip_and_paint_without_h() -> None:
    with pytest.raises(LawBlockedError):
        require_stage(
            current_stage="0",
            target_stage="B",
            sibling_sha_ok=True,
            h_channel_locked=True,
            thread_id="t.skip",
        )
    with pytest.raises(LawBlockedError):
        require_stage(
            current_stage="A",
            target_stage="B",
            sibling_sha_ok=True,
            h_channel_locked=False,
            thread_id="t.noh",
        )


def test_sibling_and_h_channel_laws() -> None:
    require_sibling(sibling_sha_ok=True, thread_id="t.sha.ok")
    with pytest.raises(LawBlockedError):
        require_sibling(sibling_sha_ok=False, thread_id="t.sha.bad")
    require_h_channel(h_channel_locked=True, delta_finite=True, thread_id="t.h.ok")
    with pytest.raises(LawBlockedError):
        require_h_channel(h_channel_locked=False, delta_finite=True, thread_id="t.h.bad")


def test_claim_bans() -> None:
    require_claims(thread_id="t.c.ok")
    with pytest.raises(LawBlockedError):
        require_claims(p_as_forecast=True, thread_id="t.c.p")
    with pytest.raises(LawBlockedError):
        require_claims(hand_as_firm=True, thread_id="t.c.f")


def test_laws_registry() -> None:
    ids = {row["id"] for row in laws()}
    assert ids == {
        "stage.stage_gate",
        "stage.sibling_sha",
        "stage.h_channel",
        "stage.claim_bans",
    }
