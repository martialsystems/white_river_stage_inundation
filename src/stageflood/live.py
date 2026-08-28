# Copyright (c) 2026 Martial Systems LLC
"""Live Nora Stage 0-C. Sibling HAND is read, not recomputed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from stageflood.claims import require_clean, require_paths_clean
from stageflood.compare import overlap_table, pair_fill_sentence
from stageflood.config import (
    CREST_DATE,
    CREST_LABEL,
    CREST_SOURCE,
    CREST_STAGE_FT,
    CREST_WSE_FT_NAVD88,
    FT_TO_M,
    GAGE_DATUM_FT_NAVD88,
    GAGE_ID,
    GAGE_NAME,
    GAGE_NWS_ID,
    GAGE_SNAP_MAX_M,
    HYDRO_BURN_M,
    HYDRO_NODATA,
    NWS_FLOOD_WSE_FT_NAVD88,
    P_DEFINITION,
    P_HEADLINE_T,
    PRIMARY_STAGE_FT,
    PRIMARY_STAGE_LABEL,
    REACH_ALONG_M,
    TEMPLATE_RES_M,
    WET_NODATA,
)
from stageflood.d8 import flowdir_from_dem
from stageflood.errors import ChannelUnlockedError, GateError, SiblingShaError
from stageflood.figure import depth_note, reach_footer, reach_title, stage_txt, write_three_panel
from stageflood.http import GetBytes, GetJson
from stageflood.nhd import fetch_white_river_flowlines, ftype_counts, rasterize_white_river
from stageflood.nwis import fetch_exsa_rating
from stageflood.physics import paint_wet, relative_height_m, stage_to_wse_m, wse_ft_navd88
from stageflood.pipeline import check_live_sibling
from stageflood.rating import RatingPoint, require_stage_on_rating
from stageflood.reach import along_stream_mask, drain_to_reach, nearest_cell
from stageflood.sibling import sibling_paths
from stageflood.window import (
    RasterWindow,
    read_window,
    window_from_dataset,
    write_window_band,
)
from stageforge.gate import require_claims, require_h_channel, require_sibling, require_stage


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    require_clean(text, source=str(path))
    path.write_text(text, encoding="utf-8")
    return path


def _finite_valid(dem: np.ndarray, hand: np.ndarray) -> np.ndarray:
    return np.isfinite(dem) & np.isfinite(hand) & (dem != HYDRO_NODATA) & (hand != HYDRO_NODATA)


def run_stage0_live(out_dir: Path, *, sibling_root: Path | None = None) -> dict[str, Any]:
    require_stage(
        current_stage="0",
        target_stage="0",
        sibling_sha_ok=False,
        h_channel_locked=False,
        thread_id="stage0.live",
    )
    shas = check_live_sibling(sibling_root)
    paths = sibling_paths(sibling_root)
    import rasterio

    with rasterio.open(paths["hand"]) as src:
        spec = window_from_dataset(src)
    rasters = Path(out_dir) / "rasters"
    hand = read_window(paths["hand"], spec)
    dem = read_window(paths["dem"], spec)
    zone = read_window(paths["zone_class"], spec)
    p_cal = read_window(paths["p_calibrated"], spec)
    write_window_band(rasters / "hand.tif", np.nan_to_num(hand, nan=HYDRO_NODATA), spec, dtype="float32", nodata=HYDRO_NODATA)
    write_window_band(rasters / "dem.tif", np.nan_to_num(dem, nan=HYDRO_NODATA), spec, dtype="float32", nodata=HYDRO_NODATA)
    write_window_band(rasters / "zone_class.tif", np.nan_to_num(zone, nan=255), spec, dtype="uint8", nodata=255)
    write_window_band(rasters / "p_calibrated.tif", np.nan_to_num(p_cal, nan=-1), spec, dtype="float32", nodata=-1)
    require_sibling(sibling_sha_ok=True, thread_id="stage0.live.sha")
    report = {
        "stage": "0",
        "kind": "live",
        "gage_id": GAGE_ID,
        "gage_nws_id": GAGE_NWS_ID,
        "gage_name": GAGE_NAME,
        "p_definition": P_DEFINITION,
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
        "hand_recomputed": False,
        "window": {
            "row0": spec.row0,
            "col0": spec.col0,
            "height": spec.height,
            "width": spec.width,
            "gage_row_w": spec.gage_row_w,
            "gage_col_w": spec.gage_col_w,
            "parent_cells": spec.parent_cells,
            "window_cells": spec.window_cells,
            "west": spec.west,
            "north": spec.north,
        },
        "sibling_sha": shas,
    }
    _write_json(Path(out_dir) / "stage0_report.json", report)
    return report


def run_stage_a_live(
    out_dir: Path,
    *,
    sibling_root: Path | None = None,
    get_bytes: GetBytes | None = None,
    get_json: GetJson | None = None,
) -> dict[str, Any]:
    s0 = json.loads((Path(out_dir) / "stage0_report.json").read_text(encoding="utf-8"))
    require_stage(
        current_stage="0",
        target_stage="A",
        sibling_sha_ok=True,
        h_channel_locked=False,
        thread_id="stagea.live",
    )
    rating = fetch_exsa_rating(get_bytes=get_bytes)
    placed = require_stage_on_rating(PRIMARY_STAGE_FT, rating)
    (Path(out_dir) / "rating.exsa.txt").write_text(
        f"site={GAGE_ID}\nn_points={len(rating)}\nplaced={placed[0]} ft, {placed[1]} cfs\n",
        encoding="utf-8",
    )
    paths = sibling_paths(sibling_root)
    import rasterio

    with rasterio.open(paths["hand"]) as src:
        spec = window_from_dataset(src)
    w = s0["window"]
    spec = RasterWindow(
        row0=int(w["row0"]),
        col0=int(w["col0"]),
        height=int(w["height"]),
        width=int(w["width"]),
        parent_height=spec.parent_height,
        parent_width=spec.parent_width,
        gage_row=spec.gage_row,
        gage_col=spec.gage_col,
        gage_row_w=int(w["gage_row_w"]),
        gage_col_w=int(w["gage_col_w"]),
        west=float(w["west"]),
        north=float(w["north"]),
        res_m=TEMPLATE_RES_M,
        crs_epsg=spec.crs_epsg,
    )
    rasters = Path(out_dir) / "rasters"
    hand = read_window(rasters / "hand.tif", spec)
    dem = read_window(rasters / "dem.tif", spec)
    valid = _finite_valid(dem, hand)
    features = fetch_white_river_flowlines(get_json=get_json)
    (Path(out_dir) / "nhd_white_river.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )
    white = rasterize_white_river(features, spec)
    snap_r, snap_c, snap_cells = nearest_cell(white, spec.gage_row_w, spec.gage_col_w)
    snap_m = snap_cells * TEMPLATE_RES_M
    if snap_m > GAGE_SNAP_MAX_M:
        raise GateError(f"gage is {snap_m:.1f} m from White River raster (max {GAGE_SNAP_MAX_M})")
    reach = along_stream_mask(
        white,
        start=(snap_r, snap_c),
        max_m=REACH_ALONG_M,
        cellsize=TEMPLATE_RES_M,
    )
    write_window_band(rasters / "reach_stream.tif", reach.astype(np.uint8), spec, dtype="uint8", nodata=0)
    stream_paint = np.isfinite(hand) & (hand == 0)
    burn = stream_paint | white
    flowdir = flowdir_from_dem(dem, burn, valid, burn_m=HYDRO_BURN_M)
    write_window_band(rasters / "flowdir.tif", flowdir, spec, dtype="int8", nodata=-1)
    h_channel = float(dem[snap_r, snap_c])
    if not np.isfinite(h_channel):
        raise GateError("h_channel is not finite at the snapped White River cell")
    wse_ft = wse_ft_navd88(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    if abs(wse_ft - NWS_FLOOD_WSE_FT_NAVD88) > 1e-9:
        raise GateError("WSE ft is not gage zero plus flood stage")
    wse = stage_to_wse_m(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    delta = relative_height_m(wse_navd88_m=wse, h_channel_m=h_channel)
    require_h_channel(h_channel_locked=True, delta_finite=np.isfinite(delta), thread_id="stagea.live.h")
    hand_at = float(hand[snap_r, snap_c]) if np.isfinite(hand[snap_r, snap_c]) else None
    datum_m = GAGE_DATUM_FT_NAVD88 * FT_TO_M
    report = {
        "stage": "A",
        "kind": "live",
        "gage_id": GAGE_ID,
        "gage_nws_id": GAGE_NWS_ID,
        "stage_ft": PRIMARY_STAGE_FT,
        "stage_label": PRIMARY_STAGE_LABEL,
        "rating_n_points": len(rating),
        "rating_min_ft": float(min(p[0] for p in rating)),
        "rating_max_ft": float(max(p[0] for p in rating)),
        "rating_point_stage_ft": placed[0],
        "rating_point_q_cfs": placed[1],
        "datum_ft_navd88": GAGE_DATUM_FT_NAVD88,
        "wse_ft_navd88": wse_ft,
        "datum_m": datum_m,
        "wse_m": wse,
        "h_channel_m": h_channel,
        "h_channel_locked": True,
        "h_channel_is_gage_datum": bool(abs(h_channel - datum_m) < 0.01),
        "h_channel_source": "sibling DEM at nearest White River cell",
        "delta_m": delta,
        "stage_height_m": PRIMARY_STAGE_FT * FT_TO_M,
        "dem_minus_datum_m": h_channel - datum_m,
        "hand_at_channel_m": hand_at,
        "snap_row": snap_r,
        "snap_col": snap_c,
        "snap_m": snap_m,
        "reach_along_m": REACH_ALONG_M,
        "river_km": (2.0 * REACH_ALONG_M) / 1000.0,
        "n_white_river_cells": int(white.sum()),
        "n_reach_stream": int(reach.sum()),
        "n_stream_paint": int(stream_paint.sum()),
        "tributary_rule": "D8 drain to the White River window, not Euclidean near the gage",
        "nhd_n_features": len(features),
        "nhd_ftype_counts": ftype_counts(features),
        "d8_byte_identical_to_sibling_stage_b": False,
        "d8_note": (
            "Window D8 rebuilt from DEM + HAND=0 stream paint + White River. "
            "Sibling has no flowdir.tif. Paths are not byte-identical to sibling Stage B. "
            "HAND not recomputed."
        ),
        "hand_recomputed": False,
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
    }
    _write_json(Path(out_dir) / "stage_a_report.json", report)
    return report


def run_stage_b_live(out_dir: Path) -> dict[str, Any]:
    a = json.loads((Path(out_dir) / "stage_a_report.json").read_text(encoding="utf-8"))
    s0 = json.loads((Path(out_dir) / "stage0_report.json").read_text(encoding="utf-8"))
    if not a.get("h_channel_locked"):
        raise ChannelUnlockedError("stage A did not lock h_channel")
    require_stage(
        current_stage="A",
        target_stage="B",
        sibling_sha_ok=True,
        h_channel_locked=True,
        thread_id="stageb.live",
    )
    require_h_channel(
        h_channel_locked=True,
        delta_finite=np.isfinite(float(a["delta_m"])),
        thread_id="stageb.live.h",
    )
    import rasterio

    rasters = Path(out_dir) / "rasters"
    with rasterio.open(rasters / "hand.tif") as src:
        hand = src.read(1).astype(np.float64)
        if src.nodata is not None:
            hand[hand == src.nodata] = np.nan
        profile = src.profile
    with rasterio.open(rasters / "flowdir.tif") as src:
        flowdir = src.read(1)
    with rasterio.open(rasters / "reach_stream.tif") as src:
        reach = src.read(1) == 1
    valid = np.isfinite(hand)
    drain = drain_to_reach(flowdir, reach, valid)
    wet = paint_wet(
        hand,
        delta_m=float(a["delta_m"]),
        drain_to_reach=drain,
        h_channel_locked=True,
    )
    dest = rasters / "wet.tif"
    profile.update(dtype="uint8", nodata=WET_NODATA, count=1, compress="deflate")
    with rasterio.open(dest, "w", **profile) as dst:
        dst.write(wet, 1)
    parent_cells = int(s0["window"]["parent_cells"])
    huc_wide = drain.size >= parent_cells
    if huc_wide:
        raise GateError("B painted a HUC-wide mask")
    report = {
        "stage": "B",
        "kind": "live",
        "wet_path": str(dest),
        "n_wet": int((wet == 1).sum()),
        "n_drain": int(drain.sum()),
        "n_window_cells": int(wet.size),
        "n_huc_cells": parent_cells,
        "huc_wide": huc_wide,
        "delta_m": float(a["delta_m"]),
        "wet_rule": "D8 drain-to-reach and finite HAND and HAND < Δ; not Euclidean to the gage",
        "d8_byte_identical_to_sibling_stage_b": False,
        "hand_recomputed": False,
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
    }
    _write_json(Path(out_dir) / "stage_b_report.json", report)
    return report


def run_stage_c_live(out_dir: Path) -> dict[str, Any]:
    b = json.loads((Path(out_dir) / "stage_b_report.json").read_text(encoding="utf-8"))
    if b.get("huc_wide"):
        raise GateError("C refuses a HUC-wide wet mask")
    require_stage(
        current_stage="B",
        target_stage="C",
        sibling_sha_ok=True,
        h_channel_locked=True,
        stage_b_wet=True,
        huc_wide_wet=False,
        thread_id="stagec.live",
    )
    require_claims(p_as_forecast=False, hand_as_firm=False, thread_id="stagec.live.claims")
    import rasterio

    rasters = Path(out_dir) / "rasters"
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
    with rasterio.open(rasters / "hand.tif") as src:
        hand = src.read(1).astype(np.float64)
        if src.nodata is not None:
            hand[hand == src.nodata] = np.nan
    drain = drain_to_reach(flowdir, reach, np.isfinite(hand))
    huc_cells = int(b["n_huc_cells"])
    table = overlap_table(
        wet=wet,
        zone=zone,
        p_cal=p_cal,
        drain_to_reach=drain,
        huc_cell_count=huc_cells,
    )
    a = json.loads((Path(out_dir) / "stage_a_report.json").read_text(encoding="utf-8"))
    wse_ft = float(a["wse_ft_navd88"])
    title = reach_title(wse_ft=wse_ft)
    delta_line = depth_note(
        delta_m=float(a["delta_m"]),
        dem_minus_datum_m=float(a["dem_minus_datum_m"]),
        dem_source="3DEP at the channel",
    )
    footer = reach_footer(iou_sfha_wet=float(table["iou_sfha_wet"]))
    fig = write_three_panel(
        Path(out_dir) / "three_wet.png",
        wet=wet,
        zone=zone,
        p_cal=p_cal,
        drain_to_reach=drain,
        title=title,
        delta_line=delta_line,
        footer=footer,
        huc_cell_count=huc_cells,
    )
    report = {
        "stage": "C",
        "kind": "live",
        "figure": str(fig),
        "figure_title": title,
        "figure_delta_line": delta_line,
        "figure_footer": footer,
        "wet_meaning": (
            f"cells below {wse_ft:.2f} ft WSE among cells that drain to this "
            f"{float(a['reach_along_m']) / 1000.0:.0f} km reach"
        ),
        "p_definition": P_DEFINITION,
        "p_headline_t": P_HEADLINE_T,
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
        "hand_recomputed": False,
        "d8_byte_identical_to_sibling_stage_b": False,
        **table,
    }
    _write_json(Path(out_dir) / "stage_c_report.json", report)
    require_paths_clean(
        [
            Path(out_dir) / "stage0_report.json",
            Path(out_dir) / "stage_a_report.json",
            Path(out_dir) / "stage_b_report.json",
            Path(out_dir) / "stage_c_report.json",
        ]
    )
    return report


def run_live(
    out_dir: Path,
    *,
    sibling_root: Path | None = None,
    get_bytes: GetBytes | None = None,
    get_json: GetJson | None = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Stage 0: sibling sha and Nora window", flush=True)
    run_stage0_live(out_dir, sibling_root=sibling_root)
    print("Stage A: EXSA rating, White River, h_channel", flush=True)
    run_stage_a_live(
        out_dir,
        sibling_root=sibling_root,
        get_bytes=get_bytes,
        get_json=get_json,
    )
    print("Stage B: drain-to-reach wet mask", flush=True)
    run_stage_b_live(out_dir)
    print("Stage C: three-layer compare", flush=True)
    return run_stage_c_live(out_dir)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_crest_figure(
    out_dir: Path,
    *,
    sibling_root: Path | None = None,
    get_bytes: GetBytes | None = None,
    rating: tuple[RatingPoint, ...] | None = None,
    check_sibling: bool = True,
    stage_ft: float = CREST_STAGE_FT,
    crest_date: str = CREST_DATE,
    stage_label: str = CREST_LABEL,
) -> dict[str, Any]:
    """Second PNG: same window and h_channel, new Δ. Does not rewrite v1 three_wet.png."""
    out_dir = Path(out_dir)
    v1_fig = out_dir / "three_wet.png"
    dest_fig = out_dir / f"three_wet_crest_{crest_date}.png"
    if dest_fig.resolve() == v1_fig.resolve():
        raise GateError("crest figure must not replace v1 three_wet.png")
    if not (out_dir / "stage_a_report.json").is_file():
        raise ChannelUnlockedError("run v1 live (stage A) before the crest figure")
    a = json.loads((out_dir / "stage_a_report.json").read_text(encoding="utf-8"))
    if not a.get("h_channel_locked"):
        raise ChannelUnlockedError("v1 stage A did not lock h_channel")
    b_path = out_dir / "stage_b_report.json"
    if not b_path.is_file():
        raise GateError("run v1 live (stage B) before the crest figure")
    b = json.loads(b_path.read_text(encoding="utf-8"))
    if b.get("huc_wide"):
        raise GateError("crest refuses a HUC-wide wet mask")
    c_path = out_dir / "stage_c_report.json"
    if not c_path.is_file():
        raise GateError("run v1 live (stage C) before the crest figure")
    c = json.loads(c_path.read_text(encoding="utf-8"))
    if check_sibling:
        shas = check_live_sibling(sibling_root)
        locked = json.loads((out_dir / "stage0_report.json").read_text(encoding="utf-8")).get(
            "sibling_sha"
        ) or {}
        if locked and shas != locked:
            raise SiblingShaError("sibling hashes moved since v1")
    v1_sha = _sha256_file(v1_fig) if v1_fig.is_file() else None
    curve = rating if rating is not None else fetch_exsa_rating(get_bytes=get_bytes)
    placed = require_stage_on_rating(stage_ft, curve)
    h_channel = float(a["h_channel_m"])
    wse_ft = wse_ft_navd88(stage_ft=stage_ft, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    if abs(wse_ft - (GAGE_DATUM_FT_NAVD88 + float(stage_ft))) > 1e-9:
        raise GateError("crest WSE ft is not gage zero plus crest stage")
    wse = stage_to_wse_m(stage_ft=stage_ft, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    delta = relative_height_m(wse_navd88_m=wse, h_channel_m=h_channel)
    require_h_channel(
        h_channel_locked=True,
        delta_finite=np.isfinite(delta),
        thread_id="crest.h",
    )
    require_claims(p_as_forecast=False, hand_as_firm=False, thread_id="crest.claims")
    import rasterio

    rasters = out_dir / "rasters"
    with rasterio.open(rasters / "hand.tif") as src:
        hand = src.read(1).astype(np.float64)
        if src.nodata is not None:
            hand[hand == src.nodata] = np.nan
        profile = src.profile
    with rasterio.open(rasters / "flowdir.tif") as src:
        flowdir = src.read(1)
    with rasterio.open(rasters / "reach_stream.tif") as src:
        reach = src.read(1) == 1
    with rasterio.open(rasters / "zone_class.tif") as src:
        zone = src.read(1)
    with rasterio.open(rasters / "p_calibrated.tif") as src:
        p_cal = src.read(1)
    drain = drain_to_reach(flowdir, reach, np.isfinite(hand))
    wet = paint_wet(
        hand,
        delta_m=delta,
        drain_to_reach=drain,
        h_channel_locked=True,
    )
    wet_path = rasters / f"wet_crest_{crest_date}.tif"
    profile.update(dtype="uint8", nodata=WET_NODATA, count=1, compress="deflate")
    with rasterio.open(wet_path, "w", **profile) as dst:
        dst.write(wet, 1)
    huc_cells = int(b["n_huc_cells"])
    table = overlap_table(
        wet=wet,
        zone=zone,
        p_cal=p_cal,
        drain_to_reach=drain,
        huc_cell_count=huc_cells,
    )
    dem_minus_datum_m = float(a["dem_minus_datum_m"])
    title = (
        f"{GAGE_ID} {stage_label} {stage_txt(stage_ft)} ft ({crest_date}, NWS provisional): "
        f"cells below {wse_ft:.2f} ft WSE on the reach"
    )
    dem_source = "3DEP at the channel" if a.get("kind") == "live" else "Channel DEM"
    delta_line = depth_note(
        delta_m=delta,
        dem_minus_datum_m=dem_minus_datum_m,
        stage_ft=stage_ft,
        dem_source=dem_source,
    )
    pair = pair_fill_sentence(baseline=c, later=table)
    footer = (
        reach_footer(iou_sfha_wet=float(table["iou_sfha_wet"]), stage_ft=stage_ft)
        + "\n"
        + pair
    )
    fig = write_three_panel(
        dest_fig,
        wet=wet,
        zone=zone,
        p_cal=p_cal,
        drain_to_reach=drain,
        title=title,
        delta_line=delta_line,
        footer=footer,
        huc_cell_count=huc_cells,
        stage_ft=stage_ft,
        wet_caption=f"Stage wet: HAND inundation\nat {stage_label}",
    )
    if v1_fig.is_file() and v1_sha is not None and _sha256_file(v1_fig) != v1_sha:
        raise GateError("crest run mutated v1 three_wet.png")
    n_v1_wet = int(b.get("n_wet") or 0)
    report = {
        "kind": "crest",
        "v1_frozen": True,
        "gage_id": GAGE_ID,
        "gage_nws_id": GAGE_NWS_ID,
        "stage_ft": float(stage_ft),
        "stage_label": stage_label,
        "crest_date": crest_date,
        "crest_source": CREST_SOURCE,
        "crest_wse_ft_navd88": round(
            CREST_WSE_FT_NAVD88 if abs(stage_ft - CREST_STAGE_FT) < 1e-9 else wse_ft, 2
        ),
        "rating_point_stage_ft": placed[0],
        "rating_point_q_cfs": placed[1],
        "wse_ft_navd88": round(wse_ft, 2),
        "wse_m": wse,
        "h_channel_m": h_channel,
        "h_channel_locked": True,
        "h_channel_is_gage_datum": bool(a.get("h_channel_is_gage_datum") is True),
        "delta_m": delta,
        "dem_minus_datum_m": dem_minus_datum_m,
        "wet_path": str(wet_path),
        "figure": str(fig),
        "v1_figure": str(v1_fig),
        "v1_figure_sha256": v1_sha,
        "n_wet": int((wet == 1).sum()),
        "n_v1_wet": n_v1_wet,
        "hand_recomputed": False,
        "window_recomputed": False,
        "d8_recomputed": False,
        "d8_byte_identical_to_sibling_stage_b": False,
        "p_is_forecast": False,
        "hand_mask_is_firm": False,
        "figure_title": title,
        "figure_delta_line": delta_line,
        "figure_footer": footer,
        "pair_fill": pair,
        "wet_meaning": (
            f"cells below {wse_ft:.2f} ft WSE among cells that drain to this "
            f"{float(a.get('reach_along_m') or REACH_ALONG_M) / 1000.0:.0f} km reach"
        ),
        **table,
    }
    dest_json = out_dir / f"crest_{crest_date}_report.json"
    _write_json(dest_json, report)
    require_paths_clean([dest_json])
    return report


def run_window_stages(
    out_dir: Path,
    *,
    hand: np.ndarray,
    dem: np.ndarray,
    zone: np.ndarray,
    p_cal: np.ndarray,
    reach_stream: np.ndarray,
    flowdir: np.ndarray,
    rating: tuple[RatingPoint, ...],
    gage_row: int,
    gage_col: int,
    huc_cell_count: int,
    spec: RasterWindow,
) -> dict[str, Any]:
    """Array-in live A-C for tests. Caller supplies window D8 and rating."""
    out_dir = Path(out_dir)
    rasters = out_dir / "rasters"
    require_stage(
        current_stage="0",
        target_stage="0",
        sibling_sha_ok=False,
        h_channel_locked=False,
        thread_id="stage0.window",
    )
    write_window_band(rasters / "hand.tif", np.nan_to_num(hand, nan=HYDRO_NODATA), spec, dtype="float32", nodata=HYDRO_NODATA)
    write_window_band(rasters / "dem.tif", np.nan_to_num(dem, nan=HYDRO_NODATA), spec, dtype="float32", nodata=HYDRO_NODATA)
    write_window_band(rasters / "zone_class.tif", zone, spec, dtype="uint8", nodata=255)
    write_window_band(rasters / "p_calibrated.tif", p_cal, spec, dtype="float32", nodata=-1)
    write_window_band(rasters / "reach_stream.tif", np.asarray(reach_stream, dtype=np.uint8), spec, dtype="uint8", nodata=0)
    write_window_band(rasters / "flowdir.tif", flowdir, spec, dtype="int8", nodata=-1)
    _write_json(
        out_dir / "stage0_report.json",
        {
            "stage": "0",
            "kind": "live_window",
            "gage_id": GAGE_ID,
            "p_is_forecast": False,
            "hand_mask_is_firm": False,
            "hand_recomputed": False,
            "window": {
                "row0": spec.row0,
                "col0": spec.col0,
                "height": spec.height,
                "width": spec.width,
                "gage_row_w": gage_row,
                "gage_col_w": gage_col,
                "parent_cells": huc_cell_count,
                "window_cells": spec.window_cells,
                "west": spec.west,
                "north": spec.north,
            },
        },
    )
    require_stage(
        current_stage="0",
        target_stage="A",
        sibling_sha_ok=True,
        h_channel_locked=False,
        thread_id="stagea.window",
    )
    placed = require_stage_on_rating(PRIMARY_STAGE_FT, rating)
    snap_r, snap_c, _ = nearest_cell(reach_stream, gage_row, gage_col)
    h_channel = float(dem[snap_r, snap_c])
    wse = stage_to_wse_m(stage_ft=PRIMARY_STAGE_FT, datum_ft_navd88=GAGE_DATUM_FT_NAVD88)
    delta = relative_height_m(wse_navd88_m=wse, h_channel_m=h_channel)
    require_h_channel(h_channel_locked=True, delta_finite=np.isfinite(delta), thread_id="stagea.window.h")
    _write_json(
        out_dir / "stage_a_report.json",
        {
            "stage": "A",
            "kind": "live_window",
            "gage_id": GAGE_ID,
            "stage_ft": PRIMARY_STAGE_FT,
            "stage_label": PRIMARY_STAGE_LABEL,
            "rating_point_stage_ft": placed[0],
            "rating_point_q_cfs": placed[1],
            "wse_ft_navd88": NWS_FLOOD_WSE_FT_NAVD88,
            "wse_m": wse,
            "h_channel_m": h_channel,
            "h_channel_locked": True,
            "delta_m": delta,
            "dem_minus_datum_m": h_channel - GAGE_DATUM_FT_NAVD88 * FT_TO_M,
            "reach_along_m": REACH_ALONG_M,
            "p_is_forecast": False,
            "hand_mask_is_firm": False,
        },
    )
    run_stage_b_live(out_dir)
    return run_stage_c_live(out_dir)
