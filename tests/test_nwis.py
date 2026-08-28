# Copyright (c) 2026 Martial Systems LLC

import pytest

from stageflood.errors import RatingError
from stageflood.nwis import parse_exsa_rdb, rating_url
from stageflood.rating import require_stage_on_rating

EXSA = """# //STATION AGENCY="USGS " NUMBER="03351000       "
# //STATION NAME="WHITE RIVER NEAR NORA, IN"
INDEP	SHIFT	DEP	STOR
16N	16N	16N	1S
1.65	-0.06	95.03	
11.00	-0.03	10245.31	
21.59	0.00	35715.87	*
"""


def test_parse_exsa_places_flood_stage() -> None:
    rating = parse_exsa_rdb(EXSA)
    assert rating[0][0] == 1.65
    assert rating[-1][0] == 21.59
    pt = require_stage_on_rating(11.0, rating)
    assert pt[0] == 11.00
    assert pt[1] == 10245.31


def test_exsa_refuses_wrong_site_and_empty() -> None:
    with pytest.raises(RatingError):
        parse_exsa_rdb(EXSA.replace("03351000", "09999999"))
    with pytest.raises(RatingError):
        parse_exsa_rdb("# no header\n")
    with pytest.raises(RatingError):
        require_stage_on_rating(40.0, parse_exsa_rdb(EXSA))


def test_rating_url_is_exsa() -> None:
    url = rating_url("03351000")
    assert "site_no=03351000" in url
    assert "file_type=exsa" in url
