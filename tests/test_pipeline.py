# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

from stageflood.config import PRIMARY_STAGE_FT
from stageflood.pipeline import run_fixture


def test_fixture_paints_reach_not_tributary(tmp_path: Path) -> None:
    report = run_fixture(tmp_path)
    assert report["stage"] == "C"
    assert report["p_is_forecast"] is False
    assert report["hand_mask_is_firm"] is False
    assert report["n_stage_wet"] > 0
    assert report["n_reach_comparable"] < 12 * 16
    assert (tmp_path / "three_wet.png").is_file()
    a = (tmp_path / "stage_a_report.json").read_text(encoding="utf-8")
    assert str(PRIMARY_STAGE_FT) in a
    b = (tmp_path / "stage_b_report.json").read_text(encoding="utf-8")
    assert '"tributary_wet": 0' in b
