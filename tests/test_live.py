# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rasterio", reason="use .venv/bin/python: pip install -r requirements.txt")

from stageflood.config import (
    FIXTURE_COLS,
    FIXTURE_ROWS,
    NWS_FLOOD_WSE_FT_NAVD88,
    PRIMARY_STAGE_FT,
    TEMPLATE_CRS,
    TEMPLATE_RES_M,
)
from stageflood.fixture import (
    GAGE_COL,
    STREAM_ROW,
    channel_z_m,
    dem_grid,
    flowdir_south_then_east,
    hand_grid,
    p_grid,
    reach_stream_mask,
    zone_grid,
)
from stageflood.live import run_window_stages
from stageflood.rating import fixture_rating
from stageflood.window import RasterWindow


def _spec() -> RasterWindow:
    return RasterWindow(
        row0=0,
        col0=0,
        height=FIXTURE_ROWS,
        width=FIXTURE_COLS,
        parent_height=4252,
        parent_width=4826,
        gage_row=STREAM_ROW,
        gage_col=GAGE_COL,
        gage_row_w=STREAM_ROW,
        gage_col_w=GAGE_COL,
        west=687_000.0,
        north=1_965_000.0,
        res_m=TEMPLATE_RES_M,
        crs_epsg=TEMPLATE_CRS,
    )


def test_window_stages_channel_wet_bank_dry(tmp_path: Path) -> None:
    report = run_window_stages(
        tmp_path,
        hand=hand_grid(),
        dem=dem_grid(),
        zone=zone_grid(),
        p_cal=p_grid(),
        reach_stream=reach_stream_mask(),
        flowdir=flowdir_south_then_east(),
        rating=fixture_rating(),
        gage_row=STREAM_ROW,
        gage_col=GAGE_COL,
        huc_cell_count=4252 * 4826,
        spec=_spec(),
    )
    assert report["n_stage_wet"] > 0
    a = (tmp_path / "stage_a_report.json").read_text(encoding="utf-8")
    assert str(PRIMARY_STAGE_FT) in a
    import rasterio

    with rasterio.open(tmp_path / "rasters" / "wet.tif") as src:
        wet = src.read(1)
    assert wet[STREAM_ROW, GAGE_COL] == 1
    assert wet[STREAM_ROW - 1, GAGE_COL] == 0
    assert abs(channel_z_m() - (NWS_FLOOD_WSE_FT_NAVD88 * 0.3048 - 1.0)) < 1e-9
    assert not np.all(wet == 1)
