# Copyright (c) 2026 Martial Systems LLC
"""Tiny reach: main channel east, one tributary that must stay dry."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from stageflood.config import (
    FIXTURE_COLS,
    FIXTURE_NORTH,
    FIXTURE_ROWS,
    FIXTURE_WEST,
    FT_TO_M,
    GAGE_DATUM_FT_NAVD88,
    HYDRO_NODATA,
    PRIMARY_STAGE_FT,
    TEMPLATE_CRS,
    TEMPLATE_RES_M,
    ZONE_SFHA,
    ZONE_UNSHADED_X,
)
from stageflood.physics import relative_height_m, stage_to_wse_m
from stageflood.rating import fixture_rating, require_stage_on_rating

# Stream along the south row. Reach is columns 4..14. Tributary column 0 is off-reach.
STREAM_ROW = FIXTURE_ROWS - 1
REACH_C0, REACH_C1 = 4, FIXTURE_COLS
GAGE_COL = 8
TRIB_COL = 0
# HAND increases north of the channel, 1 m per row.
HAND_STEP_M = 1.0


def _transform():
    from rasterio.transform import from_origin

    return from_origin(FIXTURE_WEST, FIXTURE_NORTH, TEMPLATE_RES_M, TEMPLATE_RES_M)


def write_band(path: Path, arr: np.ndarray, *, dtype: str, nodata) -> None:
    import rasterio
    from rasterio.crs import CRS

    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": dtype,
        "crs": CRS.from_epsg(TEMPLATE_CRS),
        "transform": _transform(),
        "nodata": nodata,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.asarray(arr, dtype=dtype), 1)


def stream_mask() -> np.ndarray:
    m = np.zeros((FIXTURE_ROWS, FIXTURE_COLS), dtype=bool)
    m[STREAM_ROW, :] = True
    return m


def reach_stream_mask() -> np.ndarray:
    m = np.zeros((FIXTURE_ROWS, FIXTURE_COLS), dtype=bool)
    m[STREAM_ROW, REACH_C0:REACH_C1] = True
    return m


def flowdir_south_then_east() -> np.ndarray:
    """Hillslope drains south. Reach stream drains east. West of the reach drains west."""
    fd = np.full((FIXTURE_ROWS, FIXTURE_COLS), 4, dtype=np.int8)
    fd[STREAM_ROW, :] = 2
    fd[STREAM_ROW, :REACH_C0] = 6
    fd[STREAM_ROW, 0] = -1
    fd[STREAM_ROW, -1] = -1
    return fd


def hand_grid() -> np.ndarray:
    hand = np.zeros((FIXTURE_ROWS, FIXTURE_COLS), dtype=np.float64)
    for r in range(FIXTURE_ROWS):
        hand[r, :] = (STREAM_ROW - r) * HAND_STEP_M
    hand[STREAM_ROW, TRIB_COL] = 0.0
    return hand


def dem_grid(*, stream_z_m: float) -> np.ndarray:
    hand = hand_grid()
    return stream_z_m + hand


def drain_truth() -> np.ndarray:
    """Cells that D8-drain to the reach window (west of col 4 outlets the other way)."""
    m = np.zeros((FIXTURE_ROWS, FIXTURE_COLS), dtype=bool)
    m[:, REACH_C0:] = True
    return m


def zone_grid() -> np.ndarray:
    z = np.full((FIXTURE_ROWS, FIXTURE_COLS), ZONE_UNSHADED_X, dtype=np.uint8)
    z[STREAM_ROW, REACH_C0:REACH_C1] = ZONE_SFHA
    z[STREAM_ROW - 1, REACH_C0:REACH_C1] = ZONE_SFHA
    return z


def p_grid() -> np.ndarray:
    p = np.full((FIXTURE_ROWS, FIXTURE_COLS), 0.10, dtype=np.float32)
    p[STREAM_ROW, REACH_C0:REACH_C1] = 0.90
    p[STREAM_ROW - 1, REACH_C0:REACH_C1] = 0.82
    p[0, :] = 0.05
    return p


def write_fixture(out_dir: Path) -> dict[str, object]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stream_z_m = GAGE_DATUM_FT_NAVD88 * FT_TO_M
    write_band(out_dir / "hand.tif", hand_grid(), dtype="float32", nodata=HYDRO_NODATA)
    write_band(out_dir / "dem.tif", dem_grid(stream_z_m=stream_z_m), dtype="float32", nodata=HYDRO_NODATA)
    write_band(out_dir / "zone_class.tif", zone_grid(), dtype="uint8", nodata=255)
    write_band(out_dir / "p_calibrated.tif", p_grid(), dtype="float32", nodata=-1)
    write_band(out_dir / "flowdir.tif", flowdir_south_then_east(), dtype="int8", nodata=-1)
    write_band(out_dir / "reach_stream.tif", reach_stream_mask().astype(np.uint8), dtype="uint8", nodata=0)
    rating = fixture_rating()
    require_stage_on_rating(PRIMARY_STAGE_FT, rating)
    wse = stage_to_wse_m(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    h_channel = float(dem_grid(stream_z_m=stream_z_m)[STREAM_ROW, GAGE_COL])
    delta = relative_height_m(wse_navd88_m=wse, h_channel_m=h_channel)
    return {
        "kind": "fixture",
        "gage_id": "03351000",
        "stage_ft": PRIMARY_STAGE_FT,
        "h_channel_m": h_channel,
        "wse_m": wse,
        "delta_m": delta,
        "stream_z_m": stream_z_m,
        "gage_row": STREAM_ROW,
        "gage_col": GAGE_COL,
        "rating": [list(p) for p in rating],
        "out_dir": str(out_dir),
    }
