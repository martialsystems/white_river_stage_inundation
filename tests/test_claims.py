# Copyright (c) 2026 Martial Systems LLC

import pytest

from stageflood.claims import require_clean, scan_text
from stageflood.errors import ClaimBanError


def test_allows_map_layer_caption() -> None:
    text = (
        "USGS 03351000 NWS flood stage 11 ft. "
        "P(sfha | hydro) is a map layer. Stage wet is HAND < Δ."
    )
    assert scan_text(text) == []
    require_clean(text, source="t")


def test_bans_forecast_firm_100yr() -> None:
    assert "p_as_forecast" in scan_text("calibrated P predicts inundation")
    assert "p_as_forecast" in scan_text("train a flood model on FEMA")
    assert "hand_as_firm" in scan_text("HAND bathtub is a FIRM")
    assert "p_as_100yr" in scan_text("100-year exceedance from HAND")
    assert "site_level_flood_risk" in scan_text("this is site-level flood risk")
    with pytest.raises(ClaimBanError):
        require_clean("P(sfha | hydro) is a flood forecast", source="t")
