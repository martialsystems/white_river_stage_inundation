# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

import pytest

pytest.importorskip("rasterio", reason="use .venv/bin/python: pip install -r requirements.txt")

from stageflood.config import (
    CREST_DATE,
    CREST_STAGE_FT,
    CREST_WSE_FT_NAVD88,
    FIXTURE_COLS,
    FIXTURE_ROWS,
    NWS_FLOOD_WSE_FT_NAVD88,
    PRIMARY_STAGE_FT,
    TEMPLATE_CRS,
    TEMPLATE_RES_M,
)
from stageflood.errors import RatingError
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
from stageflood.live import run_crest_figure, run_window_stages
from stageflood.rating import fixture_rating, require_stage_on_rating
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


def test_crest_on_exsa_point_not_fixture_curve() -> None:
    with pytest.raises(RatingError):
        require_stage_on_rating(CREST_STAGE_FT, fixture_rating())
    placed = require_stage_on_rating(CREST_STAGE_FT, ((1.65, 95.0), (21.18, 34472.25), (21.59, 35715.87)))
    assert placed[0] == 21.18
    assert abs(CREST_WSE_FT_NAVD88 - 731.69) < 1e-9


def test_crest_png_leaves_v1_figure(tmp_path: Path) -> None:
    v1 = run_window_stages(
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
    v1_png = tmp_path / "three_wet.png"
    before = v1_png.read_bytes()
    crest = run_crest_figure(
        tmp_path,
        rating=((1.65, 95.0), (11.0, 12000.0), (21.18, 34472.25), (21.59, 35715.87)),
        check_sibling=False,
    )
    assert v1_png.read_bytes() == before
    dest = tmp_path / f"three_wet_crest_{CREST_DATE}.png"
    assert dest.is_file()
    assert dest != v1_png
    assert crest["n_wet"] > v1["n_stage_wet"]
    assert crest["v1_frozen"] is True
    assert crest["hand_recomputed"] is False
    assert crest["window_recomputed"] is False
    assert crest["d8_recomputed"] is False
    assert crest["iou_universe"] == "drain-to-reach"
    assert "21.18" in crest["figure_title"]
    assert "Δ = 4.10 m" in crest["figure_delta_line"]
    assert "not water at 21.18 ft" in crest["figure_footer"]
    import rasterio

    with rasterio.open(tmp_path / "rasters" / f"wet_crest_{CREST_DATE}.tif") as src:
        wet = src.read(1)
    assert wet[STREAM_ROW, GAGE_COL] == 1
    assert wet[STREAM_ROW, 0] != 1
    assert abs(crest["wse_ft_navd88"] - CREST_WSE_FT_NAVD88) < 1e-9
    assert abs(crest["wse_ft_navd88"] - NWS_FLOOD_WSE_FT_NAVD88) > 1.0
    assert crest["stage_ft"] != PRIMARY_STAGE_FT
    assert channel_z_m() == pytest.approx(crest["h_channel_m"])
