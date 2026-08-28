# Copyright (c) 2026 Martial Systems LLC
"""Locked Nora reach constants. Do not expand to a second HUC."""

from __future__ import annotations

from pathlib import Path

HUC8 = "05120201"
GAGE_ID = "03351000"
GAGE_NAME = "White River near Nora, IN"
GAGE_LAT = 39.9106
GAGE_LON = -86.1055
GAGE_DATUM_FT_NAVD88 = 710.51
# NWS flood stage at Nora. Stage A must place this on the rating.
PRIMARY_STAGE_FT = 11.0
PRIMARY_STAGE_LABEL = "NWS flood stage"
FT_TO_M = 0.3048
REACH_ALONG_M = 5000.0
TEMPLATE_CRS = 5070
TEMPLATE_RES_M = 30.0
HYDRO_NODATA = -9999.0
WET_NODATA = 255
WET_DRY = 0
WET_WET = 1
P_HEADLINE_T = 0.75
P_DEFINITION = "P(sfha | hydro)"
# Same live NLCD 2021 template as indiana_flood_completion Stage B.
LOCKED_TRANSFORM_SHA256 = (
    "479ac37628bfd7e5d409f6108ae6ba1805acfd37ecdc7093785db06ac9ebec22"
)
SIBLING_DEFAULT = Path.home() / "indiana_flood_completion"
ZONE_UNMAPPED = 0
ZONE_SFHA = 1
ZONE_FLOODWAY = 2
ZONE_SHADED_X = 3
ZONE_UNSHADED_X = 4
SFHA_CODES = frozenset({ZONE_SFHA, ZONE_FLOODWAY})
USER_AGENT = "MartialSystemsResearch/white_river_stage_inundation"

# Tiny Albers window for the fixture (not the live HUC).
FIXTURE_WEST = 687_000.0
FIXTURE_NORTH = 1_965_000.0
FIXTURE_ROWS = 12
FIXTURE_COLS = 16
