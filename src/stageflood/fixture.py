# Copyright (c) 2026 Martial Systems LLC
"""32x32 toy: channel HAND=0, bank HAND=2, Δ=1 m. Channel wet, bank dry."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from stageflood.config import (
    FIXTURE_BANK_HAND_M,
    FIXTURE_COLS,
    FIXTURE_DELTA_M,
    FIXTURE_NORTH,
    FIXTURE_ROWS,
    FIXTURE_WEST,
    FT_TO_M,
    GAGE_DATUM_FT_NAVD88,
    HYDRO_NODATA,
    NWS_FLOOD_WSE_FT_NAVD88,
    PRIMARY_STAGE_FT,
    TEMPLATE_CRS,
    TEMPLATE_RES_M,
    ZONE_SFHA,
    ZONE_UNSHADED_X,
)
from stageflood.errors import GateError
from stageflood.physics import relative_height_m, stage_to_wse_m, wse_ft_navd88
from stageflood.rating import fixture_rating, require_stage_on_rating

# One channel row at the south edge. Reach is columns 8..31. Col 0 outlets west.
STREAM_ROW = FIXTURE_ROWS - 1
REACH_C0, REACH_C1 = 8, FIXTURE_COLS
GAGE_COL = 16
TRIB_COL = 0


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
    """HAND = 0 on the channel row, 2 m on the bank."""
    hand = np.full((FIXTURE_ROWS, FIXTURE_COLS), FIXTURE_BANK_HAND_M, dtype=np.float64)
    hand[STREAM_ROW, :] = 0.0
    return hand


def channel_z_m() -> float:
    """DEM at the gage cell. Not gage datum. Chosen so Δ = WSE − z = 1 m."""
    wse = stage_to_wse_m(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    return wse - FIXTURE_DELTA_M


def dem_grid(*, stream_z_m: float | None = None) -> np.ndarray:
    z = channel_z_m() if stream_z_m is None else float(stream_z_m)
    return z + hand_grid()


def drain_truth() -> np.ndarray:
    """Cells that D8-drain to the reach window (west of col 8 outlets the other way)."""
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
    wse_ft = wse_ft_navd88(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    if abs(wse_ft - NWS_FLOOD_WSE_FT_NAVD88) > 1e-9:
        raise GateError("WSE ft is not gage zero plus flood stage")
    wse = stage_to_wse_m(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    h_channel = channel_z_m()
    datum_m = GAGE_DATUM_FT_NAVD88 * FT_TO_M
    if abs(h_channel - datum_m) < 0.01:
        raise GateError("h_channel must be the DEM at the channel cell, not gage datum")
    delta = relative_height_m(wse_navd88_m=wse, h_channel_m=h_channel)
    if abs(delta - FIXTURE_DELTA_M) > 1e-9:
        raise GateError(f"fixture Δ is {delta}, expected {FIXTURE_DELTA_M}")
    write_band(out_dir / "hand.tif", hand_grid(), dtype="float32", nodata=HYDRO_NODATA)
    write_band(out_dir / "dem.tif", dem_grid(), dtype="float32", nodata=HYDRO_NODATA)
    write_band(out_dir / "zone_class.tif", zone_grid(), dtype="uint8", nodata=255)
    write_band(out_dir / "p_calibrated.tif", p_grid(), dtype="float32", nodata=-1)
    write_band(out_dir / "flowdir.tif", flowdir_south_then_east(), dtype="int8", nodata=-1)
    write_band(out_dir / "reach_stream.tif", reach_stream_mask().astype(np.uint8), dtype="uint8", nodata=0)
    rating = fixture_rating()
    require_stage_on_rating(PRIMARY_STAGE_FT, rating)
    return {
        "kind": "fixture",
        "gage_id": "03351000",
        "stage_ft": PRIMARY_STAGE_FT,
        "wse_ft_navd88": wse_ft,
        "h_channel_m": h_channel,
        "h_channel_is_gage_datum": False,
        "wse_m": wse,
        "delta_m": delta,
        "stream_z_m": h_channel,
        "gage_row": STREAM_ROW,
        "gage_col": GAGE_COL,
        "rating": [list(p) for p in rating],
        "out_dir": str(out_dir),
    }
