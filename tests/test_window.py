# Copyright (c) 2026 Martial Systems LLC

import pytest

from stageflood.errors import GateError
from stageflood.window import window_slices


def test_window_is_not_huc_wide() -> None:
    row0, col0, h, w = window_slices(
        gage_row=1895,
        gage_col=1460,
        parent_height=4252,
        parent_width=4826,
        half_cells=200,
    )
    assert h < 4252 and w < 4826
    assert h == 401 and w == 401
    assert row0 == 1895 - 200
    assert col0 == 1460 - 200


def test_read_window_accepts_already_cropped(tmp_path) -> None:
    pytest.importorskip("rasterio")
    import numpy as np
    from rasterio.transform import from_origin
    from stageflood.window import RasterWindow, read_window, write_window_band

    spec = RasterWindow(
        row0=100,
        col0=80,
        height=5,
        width=6,
        parent_height=4252,
        parent_width=4826,
        gage_row=102,
        gage_col=83,
        gage_row_w=2,
        gage_col_w=3,
        west=0.0,
        north=100.0,
        res_m=30.0,
        crs_epsg=5070,
    )
    path = tmp_path / "hand.tif"
    write_window_band(path, np.ones((5, 6), dtype=np.float32), spec, dtype="float32", nodata=-9999)
    arr = read_window(path, spec)
    assert arr.shape == (5, 6)


def test_full_parent_window_refused() -> None:
    with pytest.raises(GateError, match="HUC-wide"):
        window_slices(
            gage_row=10,
            gage_col=10,
            parent_height=20,
            parent_width=20,
            half_cells=100,
        )
