# Copyright (c) 2026 Martial Systems LLC
"""Read-only sibling rasters. Refuse if the 30 m template sha drifted."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from stageflood.config import LOCKED_BAND_SHA256, LOCKED_TRANSFORM_SHA256, SIBLING_DEFAULT
from stageflood.errors import SiblingShaError


def transform_sha256_from_raster(path: Path) -> str:
    import rasterio

    with rasterio.open(path) as src:
        t = src.transform
        payload = (
            f"{int(src.crs.to_epsg() or 0)}|{src.width}|{src.height}|"
            f"{t.a},{t.b},{t.c},{t.d},{t.e},{t.f}"
        )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def require_sibling_sha(path: Path, *, expected: str = LOCKED_TRANSFORM_SHA256) -> str:
    if not path.is_file():
        raise SiblingShaError(f"sibling raster missing: {path}")
    got = transform_sha256_from_raster(path)
    if got != expected:
        raise SiblingShaError(f"transform {got} != locked {expected} ({path})")
    return got


def band_sha256_from_raster(path: Path) -> str:
    import rasterio

    with rasterio.open(path) as src:
        return hashlib.sha256(src.read(1).tobytes()).hexdigest()


def require_band_sha(path: Path, *, expected: str) -> str:
    if not path.is_file():
        raise SiblingShaError(f"sibling raster missing: {path}")
    got = band_sha256_from_raster(path)
    if got != expected:
        raise SiblingShaError(f"band {got} != locked {expected} ({path})")
    return got


def sibling_paths(root: Path | None = None) -> dict[str, Path]:
    base = Path(root) if root is not None else SIBLING_DEFAULT
    interim = base / "data" / "interim"
    return {
        "hand": interim / "hand.tif",
        "dem": interim / "dem.tif",
        "dist_stream": interim / "dist_stream.tif",
        "dist_flowline": interim / "dist_flowline.tif",
        "zone_class": interim / "zone_class.tif",
        "sfha": interim / "sfha.tif",
        "p_calibrated": interim / "p_sfha_calibrated.tif",
        "stack_manifest": interim / "stack_manifest.json",
    }


def require_manifest_sha(manifest_path: Path, *, expected: str = LOCKED_TRANSFORM_SHA256) -> str:
    if not manifest_path.is_file():
        raise SiblingShaError(f"stack manifest missing: {manifest_path}")
    blob = json.loads(manifest_path.read_text(encoding="utf-8"))
    got = str(blob.get("template_transform_sha256") or "")
    if got != expected:
        raise SiblingShaError(f"manifest sha {got} != locked {expected}")
    return got
