# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

import pytest

pytest.importorskip("rasterio", reason="use .venv/bin/python: pip install -r requirements.txt")

from stageflood.config import FIXTURE_COLS, FIXTURE_DELTA_M, FIXTURE_ROWS, PRIMARY_STAGE_FT
from stageflood.fixture import GAGE_COL, REACH_C0, REACH_C1, STREAM_ROW
from stageflood.pipeline import run_fixture


def test_fixture_paints_reach_not_tributary(tmp_path: Path) -> None:
    report = run_fixture(tmp_path)
    assert report["stage"] == "C"
    assert report["p_is_forecast"] is False
    assert report["hand_mask_is_firm"] is False
    assert report["n_stage_wet"] == REACH_C1 - REACH_C0
    assert report["n_reach_comparable"] < FIXTURE_ROWS * FIXTURE_COLS
    assert (tmp_path / "three_wet.png").is_file()
    a = (tmp_path / "stage_a_report.json").read_text(encoding="utf-8")
    assert str(PRIMARY_STAGE_FT) in a
    assert '"h_channel_is_gage_datum": false' in a
    assert f"{FIXTURE_DELTA_M}" in a
    b = (tmp_path / "stage_b_report.json").read_text(encoding="utf-8")
    assert '"tributary_wet": 0' in b
    import rasterio

    with rasterio.open(tmp_path / "rasters" / "wet.tif") as src:
        wet = src.read(1)
    assert wet[STREAM_ROW, GAGE_COL] == 1
    assert wet[STREAM_ROW - 1, GAGE_COL] == 0
    assert wet[STREAM_ROW, 0] != 1
