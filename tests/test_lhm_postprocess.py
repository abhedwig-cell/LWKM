from __future__ import annotations

from pathlib import Path
import struct

import numpy as np

from tools.lhm_postprocess import (
    aggregate_idf_series,
    aggregate_idf_sign_split,
    combine_ascii_grids,
    read_ascii_grid,
    write_ascii_grid,
    AsciiGrid,
)


def write_test_idf(path: Path, values: np.ndarray, *, nodata: float = -9999.0) -> None:
    values = np.asarray(values, dtype="<f4")
    nrow, ncol = values.shape
    xmin = 0.0
    xmax = ncol * 250.0
    ymin = 0.0
    ymax = nrow * 250.0
    header = struct.pack(
        "<3i10f",
        1271,
        ncol,
        nrow,
        xmin,
        xmax,
        ymin,
        ymax,
        float(np.min(values)),
        float(np.max(values)),
        nodata,
        0.0,
        250.0,
        250.0,
    )
    path.write_bytes(header + values.tobytes(order="C"))


def test_flux_aggregation_uses_full_modflow_cell_support(tmp_path: Path):
    a = tmp_path / "a.idf"
    b = tmp_path / "b.idf"
    write_test_idf(a, np.array([[62.5, -62.5], [125.0, 0.0]]))
    write_test_idf(b, np.array([[62.5, -62.5], [0.0, 62.5]]))

    grid = aggregate_idf_series([a, b], kind="flux_m3_day")

    # 62.5 m3 over a 62,500 m2 cell = 1 mm.
    np.testing.assert_allclose(grid.values, [[2.0, -2.0], [2.0, 1.0]])


def test_flux_sign_split_matches_historical_daily_sign_buckets(tmp_path: Path):
    a = tmp_path / "a.idf"
    b = tmp_path / "b.idf"
    write_test_idf(a, np.array([[62.5, -62.5]]))
    write_test_idf(b, np.array([[-125.0, 125.0]]))

    positive, negative = aggregate_idf_sign_split([a, b])

    np.testing.assert_allclose(positive.values, [[1.0, 2.0]])
    np.testing.assert_allclose(negative.values, [[-2.0, -1.0]])


def test_state_aggregation_is_time_mean(tmp_path: Path):
    a = tmp_path / "a.idf"
    b = tmp_path / "b.idf"
    write_test_idf(a, np.array([[1.0, 3.0]]))
    write_test_idf(b, np.array([[3.0, 5.0]]))

    grid = aggregate_idf_series([a, b], kind="state")

    np.testing.assert_allclose(grid.values, [[2.0, 4.0]])


def test_ascii_roundtrip_and_combine(tmp_path: Path):
    meta = dict(ncols=2, nrows=1, xllcorner=0.0, yllcorner=0.0, cellsize=250.0, nodata=-9999.0)
    a = AsciiGrid(np.array([[1.0, 2.0]]), **meta)
    b = AsciiGrid(np.array([[3.0, 4.0]]), **meta)
    pa = tmp_path / "a.asc"
    pb = tmp_path / "b.asc"
    write_ascii_grid(pa, a)
    write_ascii_grid(pb, b)

    combined = combine_ascii_grids([pa, pb], mean=True)
    np.testing.assert_allclose(combined.values, [[2.0, 3.0]])

    out = tmp_path / "out.asc"
    write_ascii_grid(out, combined)
    reread = read_ascii_grid(out)
    np.testing.assert_allclose(reread.values, combined.values)


def test_nodata_is_not_silently_aggregated(tmp_path: Path):
    a = tmp_path / "a.idf"
    write_test_idf(a, np.array([[1.0, -9999.0]]))
    try:
        aggregate_idf_series([a], kind="state")
    except ValueError as exc:
        assert "NODATA" in str(exc)
    else:
        raise AssertionError("expected explicit NODATA failure")
