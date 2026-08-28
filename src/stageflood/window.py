# Copyright (c) 2026 Martial Systems LLC
"""Albers window around USGS 03351000. Not a HUC-wide paint."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from stageflood.config import (
    GAGE_LAT,
    GAGE_LON,
    HYDRO_NODATA,
    TEMPLATE_CRS,
    TEMPLATE_RES_M,
    VECTOR_CRS,
    WINDOW_HALF_M,
)
from stageflood.errors import GateError


@dataclass(frozen=True)
class RasterWindow:
    row0: int
    col0: int
    height: int
    width: int
    parent_height: int
    parent_width: int
    gage_row: int
    gage_col: int
    gage_row_w: int
    gage_col_w: int
    west: float
    north: float
    res_m: float
    crs_epsg: int

    @property
    def parent_cells(self) -> int:
        return int(self.parent_height) * int(self.parent_width)

    @property
    def window_cells(self) -> int:
        return int(self.height) * int(self.width)


def window_slices(
    *,
    gage_row: int,
    gage_col: int,
    parent_height: int,
    parent_width: int,
    half_cells: int,
) -> tuple[int, int, int, int]:
    if half_cells < 1:
        raise GateError("window half_cells must be >= 1")
    row0 = max(0, int(gage_row) - half_cells)
    col0 = max(0, int(gage_col) - half_cells)
    row1 = min(int(parent_height), int(gage_row) + half_cells + 1)
    col1 = min(int(parent_width), int(gage_col) + half_cells + 1)
    height = row1 - row0
    width = col1 - col0
    if height < 3 or width < 3:
        raise GateError("window is too small")
    if height == parent_height and width == parent_width:
        raise GateError("window is HUC-wide")
    return row0, col0, height, width


def lonlat_to_rowcol(dataset, lon: float, lat: float) -> tuple[int, int]:
    from rasterio.warp import transform as rio_transform

    xs, ys = rio_transform(f"EPSG:{VECTOR_CRS}", dataset.crs, [float(lon)], [float(lat)])
    row, col = dataset.index(xs[0], ys[0])
    return int(row), int(col)


def window_from_dataset(
    dataset,
    *,
    lon: float = GAGE_LON,
    lat: float = GAGE_LAT,
    half_m: float = WINDOW_HALF_M,
    res_m: float = TEMPLATE_RES_M,
) -> RasterWindow:
    epsg = int(dataset.crs.to_epsg() or 0)
    if epsg != TEMPLATE_CRS:
        raise GateError(f"sibling CRS EPSG:{epsg} != EPSG:{TEMPLATE_CRS}")
    gage_row, gage_col = lonlat_to_rowcol(dataset, lon, lat)
    if not (0 <= gage_row < dataset.height and 0 <= gage_col < dataset.width):
        raise GateError("gage falls outside the sibling raster")
    half_cells = int(round(float(half_m) / float(res_m)))
    row0, col0, height, width = window_slices(
        gage_row=gage_row,
        gage_col=gage_col,
        parent_height=dataset.height,
        parent_width=dataset.width,
        half_cells=half_cells,
    )
    t = dataset.transform
    west = float(t.c) + col0 * float(t.a)
    north = float(t.f) + row0 * float(t.e)
    return RasterWindow(
        row0=row0,
        col0=col0,
        height=height,
        width=width,
        parent_height=int(dataset.height),
        parent_width=int(dataset.width),
        gage_row=gage_row,
        gage_col=gage_col,
        gage_row_w=gage_row - row0,
        gage_col_w=gage_col - col0,
        west=west,
        north=north,
        res_m=float(res_m),
        crs_epsg=TEMPLATE_CRS,
    )


def rio_window(spec: RasterWindow):
    from rasterio.windows import Window

    return Window(spec.col0, spec.row0, spec.width, spec.height)


def window_transform(spec: RasterWindow):
    from rasterio.transform import from_origin

    return from_origin(spec.west, spec.north, spec.res_m, spec.res_m)


def read_window(path, spec: RasterWindow) -> np.ndarray:
    import rasterio

    with rasterio.open(path) as src:
        if src.height == spec.height and src.width == spec.width:
            arr = src.read(1)
        else:
            arr = src.read(1, window=rio_window(spec))
        nodata = src.nodata
    if arr.shape != (spec.height, spec.width):
        raise GateError("window read shape mismatch")
    out = np.asarray(arr)
    if nodata is not None:
        out = out.astype(np.float64, copy=True)
        out[out == nodata] = np.nan
        out[out == HYDRO_NODATA] = np.nan
    return out


def write_window_band(path, arr: np.ndarray, spec: RasterWindow, *, dtype: str, nodata) -> None:
    import rasterio
    from rasterio.crs import CRS

    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": spec.height,
        "width": spec.width,
        "count": 1,
        "dtype": dtype,
        "crs": CRS.from_epsg(spec.crs_epsg),
        "transform": window_transform(spec),
        "nodata": nodata,
        "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.asarray(arr, dtype=dtype), 1)
