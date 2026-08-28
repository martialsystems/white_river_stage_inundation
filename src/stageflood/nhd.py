# Copyright (c) 2026 Martial Systems LLC
"""NHD White River centerline. Nora is ftype 558 Artificial Path, not 460."""

from __future__ import annotations

import math
from typing import Any
from urllib.parse import quote

import numpy as np

from stageflood.config import (
    GAGE_LAT,
    GAGE_LON,
    NHD_FLOWLINE_URL,
    NHD_GNIS_WHITE_RIVER,
    NHD_PAGE_SIZE,
    TEMPLATE_CRS,
    VECTOR_CRS,
    WINDOW_HALF_M,
)
from stageflood.errors import FetchError, GateError
from stageflood.http import GetJson, get_json as default_get_json
from stageflood.window import RasterWindow, window_transform


def envelope_4269(
    *,
    lon: float = GAGE_LON,
    lat: float = GAGE_LAT,
    half_m: float = WINDOW_HALF_M,
) -> tuple[float, float, float, float]:
    dlat = float(half_m) / 111_000.0
    coslat = math.cos(math.radians(float(lat)))
    dlon = float(half_m) / (111_000.0 * max(coslat, 0.2))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def white_river_query_url(
    *,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    offset: int = 0,
    page_size: int = NHD_PAGE_SIZE,
) -> str:
    """Query by gnis_name. Do not filter ftype=460: Nora's stem is 558."""
    where = quote(f"gnis_name='{NHD_GNIS_WHITE_RIVER}'")
    geom = quote(f"{xmin},{ymin},{xmax},{ymax}")
    return (
        f"{NHD_FLOWLINE_URL}/query"
        f"?where={where}"
        f"&geometry={geom}"
        f"&geometryType=esriGeometryEnvelope"
        f"&inSR={VECTOR_CRS}&outSR={VECTOR_CRS}"
        f"&spatialRel=esriSpatialRelIntersects"
        f"&returnGeometry=true"
        f"&outFields=objectid,ftype,fcode,gnis_name"
        f"&resultOffset={int(offset)}"
        f"&resultRecordCount={int(page_size)}"
        f"&f=geojson"
    )


def _props(feat: dict[str, Any]) -> dict[str, Any]:
    props = feat.get("properties") or feat.get("attributes") or {}
    return props if isinstance(props, dict) else {}


def select_white_river(features: list) -> list:
    """Keep gnis_name White River. Ftype 558 stays; 460-only filters drop Nora."""
    out = []
    for feat in features:
        name = str(_props(feat).get("gnis_name") or _props(feat).get("GNIS_NAME") or "")
        if name.strip().casefold() == NHD_GNIS_WHITE_RIVER.casefold():
            out.append(feat)
    if not out:
        raise GateError("no NHD White River flowlines in the window")
    return out


def fetch_white_river_flowlines(
    *,
    get_json: GetJson | None = None,
    half_m: float = WINDOW_HALF_M,
) -> list:
    getter = get_json or default_get_json
    xmin, ymin, xmax, ymax = envelope_4269(half_m=half_m)
    features: list = []
    offset = 0
    for _ in range(20):
        url = white_river_query_url(
            xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, offset=offset
        )
        page = getter(url)
        if not isinstance(page, dict):
            raise FetchError("NHD query did not return an object")
        if page.get("error"):
            raise FetchError(f"NHD query error: {page['error']}")
        batch = page.get("features") or []
        if not batch:
            break
        features.extend(batch)
        exceeded = bool(
            (page.get("properties") or {}).get("exceededTransferLimit")
            or page.get("exceededTransferLimit")
        )
        if not exceeded:
            break
        offset += len(batch)
    else:
        raise GateError("NHD pagination exceeded 20 pages")
    return select_white_river(features)


def _geoms_5070(features: list) -> list:
    from rasterio.warp import transform_geom

    shapes = []
    for feat in features:
        geom = feat.get("geometry")
        if not geom:
            continue
        g5070 = transform_geom(f"EPSG:{VECTOR_CRS}", f"EPSG:{TEMPLATE_CRS}", geom)
        shapes.append((g5070, 1))
    if not shapes:
        raise GateError("no NHD geometries to rasterize")
    return shapes


def rasterize_white_river(features: list, spec: RasterWindow) -> np.ndarray:
    from rasterio.features import rasterize

    shapes = _geoms_5070(features)
    painted = rasterize(
        shapes,
        out_shape=(spec.height, spec.width),
        transform=window_transform(spec),
        fill=0,
        dtype="uint8",
        all_touched=True,
    )
    if not np.any(painted):
        raise GateError("White River raster is empty on the Nora window")
    return painted.astype(bool, copy=False)


def ftype_counts(features: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for feat in features:
        ftype = _props(feat).get("ftype")
        key = str(ftype) if ftype is not None else "none"
        counts[key] = counts.get(key, 0) + 1
    return counts
