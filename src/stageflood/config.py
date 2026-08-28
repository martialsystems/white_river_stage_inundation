# Copyright (c) 2026 Martial Systems LLC
"""Locked Nora reach constants. Do not expand to a second HUC."""

from __future__ import annotations

from pathlib import Path

HUC8 = "05120201"
GAGE_ID = "03351000"
GAGE_NAME = "White River near Nora, IN"
GAGE_LAT = 39.9106
GAGE_LON = -86.1056
GAGE_NWS_ID = "NORI3"
GAGE_DATUM_FT_NAVD88 = 710.51
# NWS flood stage at Nora. Stage A must place this on the rating.
PRIMARY_STAGE_FT = 11.0
PRIMARY_STAGE_LABEL = "NWS flood stage"
# Identity: NWS minor flooding WSE = gage zero + 11.0 ft, both NAVD88.
NWS_FLOOD_WSE_FT_NAVD88 = GAGE_DATUM_FT_NAVD88 + PRIMARY_STAGE_FT
# Second figure only. v1 stays 11 ft. NWS NORI3 recent crest, provisional.
CREST_STAGE_FT = 21.18
CREST_DATE = "2026-08-15"
CREST_LABEL = "August 2026 crest"
CREST_SOURCE = "NWS NORI3 recent crest, provisional"
CREST_WSE_FT_NAVD88 = round(GAGE_DATUM_FT_NAVD88 + CREST_STAGE_FT, 2)
FT_TO_M = 0.3048
# 5 km of White River mainstem, inside the 2 to 5 km flat-WSE window.
REACH_ALONG_M = 5000.0
WINDOW_MARGIN_M = 1000.0
WINDOW_HALF_M = REACH_ALONG_M + WINDOW_MARGIN_M
# Fixture model: HAND 0 on channel, 2 on the bank, Δ = 1 m.
FIXTURE_DELTA_M = 1.0
FIXTURE_BANK_HAND_M = 2.0
TEMPLATE_CRS = 5070
VECTOR_CRS = 4269
TEMPLATE_RES_M = 30.0
HYDRO_NODATA = -9999.0
HYDRO_BURN_M = 50.0
HYDRO_FILL_EPSILON_M = 1e-3
WET_NODATA = 255
WET_DRY = 0
WET_WET = 1
P_HEADLINE_T = 0.75
P_DEFINITION = "P(sfha | hydro)"
# Same live NLCD 2021 template as indiana_flood_completion Stage B.
LOCKED_TRANSFORM_SHA256 = (
    "479ac37628bfd7e5d409f6108ae6ba1805acfd37ecdc7093785db06ac9ebec22"
)
# v1 flood-stage three-panel. Interview note and crest refuse a rewrite.
LOCKED_V1_PNG_SHA256 = (
    "cab5c15439bb322b5116ae158f58c7777acd5634db7e351bdd47dd6f68d720ab"
)
# Band tobytes() sha256. Sibling has no flowdir.tif; dist_stream / dist_flowline are the stream paint.
LOCKED_BAND_SHA256 = {
    "hand": "3fdf3694c5662da0198440cc46d6ede4e97a8497cc2782e3f6d76c9553488b7f",
    "dem": "fd14a77318bec7952500c7de6092cfdc3be3411f836ef34237a9375abf9cf731",
    "dist_stream": "1a16f292cfd2a210429636c14c99aedae405812ade6e33b01dec801745bce5ac",
    "dist_flowline": "6634b0bbfb6164eb1d60cab28e608541a956745fb173f39b9682d3ce93d7e85d",
    "p_calibrated": "8e1cc7b2178192d6859b3ff6d01014019cf9c5588fbadc3d8b7e228a41ca42c3",
    "zone_class": "1d6c6e39f8f861e71eb4da1b781a12b09a747ab01491e38d641039e75921a0f6",
}
SIBLING_DEFAULT = Path.home() / "indiana_flood_completion"
ZONE_UNMAPPED = 0
ZONE_SFHA = 1
ZONE_FLOODWAY = 2
ZONE_SHADED_X = 3
ZONE_UNSHADED_X = 4
SFHA_CODES = frozenset({ZONE_SFHA, ZONE_FLOODWAY})
USER_AGENT = "MartialSystemsResearch/white_river_stage_inundation"
NHD_FLOWLINE_URL = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6"
NHD_GNIS_WHITE_RIVER = "White River"
NHD_PAGE_SIZE = 2000
NWIS_RATING_URL = (
    "https://waterdata.usgs.gov/nwisweb/get_ratings?site_no={site_no}&file_type=exsa"
)
# Live HUC is ~20e6 cells. A Nora window is ~3e5. Fixture is 192.
GAGE_SNAP_MAX_M = 600.0

# Tiny Albers window for the fixture (not the live HUC).
FIXTURE_WEST = 687_000.0
FIXTURE_NORTH = 1_965_000.0
FIXTURE_ROWS = 32
FIXTURE_COLS = 32
