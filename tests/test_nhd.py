# Copyright (c) 2026 Martial Systems LLC

from stageflood.nhd import select_white_river, white_river_query_url


def test_keeps_artificial_path_558() -> None:
    feats = [
        {"properties": {"gnis_name": "White River", "ftype": 558}},
        {"properties": {"gnis_name": "Fall Creek", "ftype": 460}},
        {"properties": {"gnis_name": "White River", "ftype": 460}},
    ]
    kept = select_white_river(feats)
    ftypes = {f["properties"]["ftype"] for f in kept}
    assert 558 in ftypes
    only_460 = [f for f in kept if f["properties"]["ftype"] == 460]
    assert len(kept) == 2
    assert len(only_460) == 1


def test_query_does_not_filter_ftype_460() -> None:
    url = white_river_query_url(xmin=-86.2, ymin=39.8, xmax=-86.0, ymax=40.0)
    assert "gnis_name='White River'" in url or "gnis_name%3D%27White%20River%27" in url
    assert "ftype=460" not in url
    assert "ftype%3D460" not in url
