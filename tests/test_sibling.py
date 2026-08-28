# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rasterio", reason="use .venv/bin/python: pip install -r requirements.txt")

from rasterio.crs import CRS
from rasterio.transform import from_origin
import rasterio

from stageflood.config import LOCKED_BAND_SHA256, LOCKED_TRANSFORM_SHA256
from stageflood.errors import SiblingShaError
from stageflood.sibling import require_band_sha, require_sibling_sha, transform_sha256_from_raster


def _write(path: Path, *, width: int = 4, height: int = 3, crs: int = 5070) -> None:
    t = from_origin(0, 100, 30, 30)
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": CRS.from_epsg(crs),
        "transform": t,
        "nodata": -9999.0,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.zeros((height, width), dtype=np.float32), 1)


def test_sha_mismatch_refused(tmp_path: Path) -> None:
    p = tmp_path / "hand.tif"
    _write(p)
    got = transform_sha256_from_raster(p)
    assert got != LOCKED_TRANSFORM_SHA256
    with pytest.raises(SiblingShaError):
        require_sibling_sha(p)
    with pytest.raises(SiblingShaError):
        require_sibling_sha(tmp_path / "missing.tif")
    with pytest.raises(SiblingShaError):
        require_band_sha(p, expected="deadbeef")
    assert set(LOCKED_BAND_SHA256) == {
        "hand",
        "dem",
        "dist_stream",
        "dist_flowline",
        "p_calibrated",
        "zone_class",
    }
