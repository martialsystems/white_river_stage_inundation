# Copyright (c) 2026 Martial Systems LLC

import pytest

from stageflood.errors import RatingError
from stageflood.rating import fixture_rating, require_stage_on_rating


def test_flood_stage_on_fixture_rating() -> None:
    pt = require_stage_on_rating(11.0, fixture_rating())
    assert pt[0] == 11.0
    assert pt[1] == 12000.0


def test_off_curve_refused() -> None:
    with pytest.raises(RatingError):
        require_stage_on_rating(40.0, fixture_rating())
    with pytest.raises(RatingError):
        require_stage_on_rating(11.0, [])
