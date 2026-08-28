# Copyright (c) 2026 Martial Systems LLC
"""Stage 0-C on a fixture or live window. Sibling HAND is read, not recomputed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from stageflood.claims import require_clean, require_paths_clean
from stageflood.compare import overlap_table
from stageflood.config import (
    GAGE_DATUM_FT_NAVD88,
    GAGE_ID,
    GAGE_NAME,
    HYDRO_NODATA,
    P_DEFINITION,
    P_HEADLINE_T,
    PRIMARY_STAGE_FT,
    PRIMARY_STAGE_LABEL,
)
from stageflood.errors import ChannelUnlockedError, GateError
from stageflood.figure import write_three_panel
from stageflood.fixture import drain_truth, write_fixture
from stageflood.physics import paint_wet, relative_height_m, stage_to_wse_m
from stageflood.rating import fixture_rating, require_stage_on_rating
from stageflood.reach import drain_to_reach
from stageflood.sibling import require_manifest_sha, require_sibling_sha, sibling_paths

from stageforge.gate import require_claims, require_h_channel, require_sibling, require_stage


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    require_clean(text, source=str(path))
    path.write_text(text, encoding="utf-8")
    return path


def run_stage0_fixture(out_dir: Path) -> dict[str, Any]:
    require_stage(
        current_stage="0",
        target_stage="0",
        sibling_sha_ok=False,
        h_channel_locked=False,
        thread_id="stage0.fixture",
    )
    meta = write_fixture(out_dir / "rasters")
    report = {
        "stage": "0",
        "kind": "fixture",
        "gage_id": GAGE_ID,
        "gage_name": GAGE_NAME,
        "p_definition": P_DEFINITION,
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
        **meta,
    }
    _write_json(out_dir / "stage0_report.json", report)
    return report


def run_stage_a_fixture(out_dir: Path) -> dict[str, Any]:
    s0 = json.loads((out_dir / "stage0_report.json").read_text(encoding="utf-8"))
    require_stage(
        current_stage="0",
        target_stage="A",
        sibling_sha_ok=True,
        h_channel_locked=False,
        thread_id="stagea.fixture",
    )
    rating = fixture_rating()
    placed = require_stage_on_rating(PRIMARY_STAGE_FT, rating)
    wse = stage_to_wse_m(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    h_channel = float(s0["h_channel_m"])
    delta = relative_height_m(wse_navd88_m=wse, h_channel_m=h_channel)
    require_h_channel(h_channel_locked=True, delta_finite=np.isfinite(delta), thread_id="stagea.h")
    report = {
        "stage": "A",
        "kind": "fixture",
        "gage_id": GAGE_ID,
        "stage_ft": PRIMARY_STAGE_FT,
        "stage_label": PRIMARY_STAGE_LABEL,
        "rating_point_stage_ft": placed[0],
        "rating_point_q_cfs": placed[1],
        "datum_ft_navd88": GAGE_DATUM_FT_NAVD88,
        "wse_m": wse,
        "h_channel_m": h_channel,
        "h_channel_locked": True,
        "delta_m": delta,
        "p_is_forecast": False,
    }
    _write_json(out_dir / "stage_a_report.json", report)
    return report


def run_stage_b_fixture(out_dir: Path) -> dict[str, Any]:
    a = json.loads((out_dir / "stage_a_report.json").read_text(encoding="utf-8"))
    if not a.get("h_channel_locked"):
        raise ChannelUnlockedError("stage A did not lock h_channel")
    require_stage(
        current_stage="A",
        target_stage="B",
        sibling_sha_ok=True,
        h_channel_locked=True,
        thread_id="stageb.fixture",
    )
    require_h_channel(
        h_channel_locked=True,
        delta_finite=np.isfinite(float(a["delta_m"])),
        thread_id="stageb.h",
    )
    import rasterio

    rasters = Path(out_dir / "rasters")
    with rasterio.open(rasters / "hand.tif") as src:
        hand = src.read(1).astype(np.float64)
        hand[hand == src.nodata] = np.nan
    with rasterio.open(rasters / "flowdir.tif") as src:
        flowdir = src.read(1)
    with rasterio.open(rasters / "reach_stream.tif") as src:
        reach = src.read(1) == 1
    valid = np.ones(hand.shape, dtype=bool)
    drain = drain_to_reach(flowdir, reach, valid)
    expected = drain_truth()
    if not np.array_equal(drain, expected):
        # Fixture D8 must reproduce the locked drain-to-reach truth.
        raise GateError("fixture drain-to-reach does not match truth mask")
    wet = paint_wet(
        hand,
        delta_m=float(a["delta_m"]),
        drain_to_reach=drain,
        h_channel_locked=True,
    )
    dest = rasters / "wet.tif"
    with rasterio.open(rasters / "hand.tif") as src:
        profile = src.profile
    profile.update(dtype="uint8", nodata=255, count=1)
    with rasterio.open(dest, "w", **profile) as dst:
        dst.write(wet, 1)
    trib_wet = int((wet[:, 0] == 1).sum())
    if trib_wet != 0:
        raise GateError("tributary column painted wet")
    report = {
        "stage": "B",
        "kind": "fixture",
        "wet_path": str(dest),
        "n_wet": int((wet == 1).sum()),
        "n_drain": int(drain.sum()),
        "n_huc_cells": int(wet.size),
        "huc_wide": bool(drain.all()),
        "tributary_wet": trib_wet,
        "delta_m": float(a["delta_m"]),
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
    }
    _write_json(out_dir / "stage_b_report.json", report)
    return report


def run_stage_c_fixture(out_dir: Path) -> dict[str, Any]:
    b = json.loads((out_dir / "stage_b_report.json").read_text(encoding="utf-8"))
    if b.get("huc_wide"):
        raise GateError("C refuses a HUC-wide wet mask")
    require_stage(
        current_stage="B",
        target_stage="C",
        sibling_sha_ok=True,
        h_channel_locked=True,
        stage_b_wet=True,
        huc_wide_wet=False,
        thread_id="stagec.fixture",
    )
    import rasterio

    require_claims(p_as_forecast=False, hand_as_firm=False, thread_id="stagec.claims")
    rasters = Path(out_dir / "rasters")
    with rasterio.open(rasters / "wet.tif") as src:
        wet = src.read(1)
    with rasterio.open(rasters / "zone_class.tif") as src:
        zone = src.read(1)
    with rasterio.open(rasters / "p_calibrated.tif") as src:
        p_cal = src.read(1)
    with rasterio.open(rasters / "flowdir.tif") as src:
        flowdir = src.read(1)
    with rasterio.open(rasters / "reach_stream.tif") as src:
        reach = src.read(1) == 1
    drain = drain_to_reach(flowdir, reach, np.ones(wet.shape, dtype=bool))
    table = overlap_table(wet=wet, zone=zone, p_cal=p_cal, drain_to_reach=drain)
    a = json.loads((out_dir / "stage_a_report.json").read_text(encoding="utf-8"))
    title = (
        f"{GAGE_ID} {PRIMARY_STAGE_LABEL} {PRIMARY_STAGE_FT} ft; "
        f"Δ={float(a['delta_m']):.2f} m; {P_DEFINITION} is a map layer"
    )
    fig = write_three_panel(
        out_dir / "three_wet.png",
        wet=wet,
        zone=zone,
        p_cal=p_cal,
        drain_to_reach=drain,
        title=title,
    )
    report = {
        "stage": "C",
        "kind": "fixture",
        "figure": str(fig),
        "p_definition": P_DEFINITION,
        "p_headline_t": P_HEADLINE_T,
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
        **table,
    }
    _write_json(out_dir / "stage_c_report.json", report)
    require_paths_clean(
        [
            out_dir / "stage0_report.json",
            out_dir / "stage_a_report.json",
            out_dir / "stage_b_report.json",
            out_dir / "stage_c_report.json",
        ]
    )
    return report


def run_fixture(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    run_stage0_fixture(out_dir)
    run_stage_a_fixture(out_dir)
    run_stage_b_fixture(out_dir)
    return run_stage_c_fixture(out_dir)


def check_live_sibling(root: Path | None = None) -> dict[str, str]:
    paths = sibling_paths(root)
    require_manifest_sha(paths["stack_manifest"])
    shas = {
        "hand": require_sibling_sha(paths["hand"]),
        "p_calibrated": require_sibling_sha(paths["p_calibrated"]),
        "zone_class": require_sibling_sha(paths["zone_class"]),
    }
    require_sibling(sibling_sha_ok=True, thread_id="live.sibling")
    return shas
