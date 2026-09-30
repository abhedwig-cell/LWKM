"""Python post-processing core for LHM/LWKM raster products.

This module is intentionally smaller than the historical batch/Fortran stack.
It replaces orchestration and simple raster aggregation, not MODFLOW/MetaSWAP.

Compatibility principles:
- fail on geometry changes instead of silently resampling;
- keep flux and state aggregation explicit;
- split positive/negative fluxes before temporal summation;
- preserve historical 62,500 m2 MODFLOW-cell support by default;
- write plain ESRI ASCII grids that can be consumed by the existing LWKM chain.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import math
from typing import Iterable, Sequence

import numpy as np

from tools.idf_reader import IDF, read_idf


DEFAULT_NODATA = -9999.0
DEFAULT_MODFLOW_CELL_AREA_M2 = 62500.0


@dataclass(frozen=True)
class AsciiGrid:
    values: np.ndarray
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata: float = DEFAULT_NODATA


def _valid_idf_values(grid: IDF) -> np.ndarray:
    values = np.asarray(grid.values, dtype=np.float64)
    invalid = ~np.isfinite(values) | np.isclose(values, float(grid.nodata))
    if invalid.any():
        raise ValueError(
            "IDF contains NODATA/non-finite cells; explicit masking semantics are required "
            "before historical-exact admission"
        )
    return values


def _same_idf_geometry(a: IDF, b: IDF) -> bool:
    return (
        a.ncol == b.ncol
        and a.nrow == b.nrow
        and math.isclose(a.xmin, b.xmin)
        and math.isclose(a.xmax, b.xmax)
        and math.isclose(a.ymin, b.ymin)
        and math.isclose(a.ymax, b.ymax)
        and math.isclose(a.dx, b.dx)
        and math.isclose(a.dy, b.dy)
    )


def _ascii_from_idf(idf: IDF, values: np.ndarray, nodata: float = DEFAULT_NODATA) -> AsciiGrid:
    if not math.isclose(idf.dx, idf.dy):
        raise ValueError(f"non-square IDF cells are not supported: dx={idf.dx}, dy={idf.dy}")
    return AsciiGrid(
        values=np.asarray(values, dtype=np.float64),
        ncols=idf.ncol,
        nrows=idf.nrow,
        xllcorner=idf.xmin,
        yllcorner=idf.ymin,
        cellsize=idf.dx,
        nodata=nodata,
    )


def read_ascii_grid(path: str | Path) -> AsciiGrid:
    path = Path(path)
    header: dict[str, float] = {}
    with path.open("r", encoding="utf-8") as handle:
        for _ in range(6):
            line = handle.readline()
            if not line:
                raise ValueError(f"{path}: incomplete ESRI ASCII header")
            key, value = line.split()
            header[key.lower()] = float(value)
        values = np.loadtxt(handle, dtype=np.float64)

    required = {"ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata_value"}
    missing = required.difference(header)
    if missing:
        raise ValueError(f"{path}: missing header keys {sorted(missing)}")

    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    if values.shape != (nrows, ncols):
        raise ValueError(f"{path}: expected {(nrows, ncols)}, got {values.shape}")

    return AsciiGrid(
        values=values,
        ncols=ncols,
        nrows=nrows,
        xllcorner=header["xllcorner"],
        yllcorner=header["yllcorner"],
        cellsize=header["cellsize"],
        nodata=header["nodata_value"],
    )


def write_ascii_grid(path: str | Path, grid: AsciiGrid, *, decimals: int = 6) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = f"%.{int(decimals)}f"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"ncols {grid.ncols}\n")
        handle.write(f"nrows {grid.nrows}\n")
        handle.write(f"xllcorner {grid.xllcorner:g}\n")
        handle.write(f"yllcorner {grid.yllcorner:g}\n")
        handle.write(f"cellsize {grid.cellsize:g}\n")
        handle.write(f"NODATA_value {grid.nodata:g}\n")
        np.savetxt(handle, grid.values, fmt=fmt)


def aggregate_idf_series(
    paths: Sequence[str | Path],
    *,
    kind: str,
    cell_area_m2: float = DEFAULT_MODFLOW_CELL_AREA_M2,
    output: str = "period",
) -> AsciiGrid:
    """Aggregate one IDF time series.

    kind='flux_m3_day':
        IDF values are cell fluxes [m3/day]. Historical full-cell conversion is
        sum(value) / cell_area * 1000 -> mm over the period. output='mean_day'
        divides the period total by the number of files.

    kind='state':
        arithmetic time mean per cell. This is the full-grid equivalent of the
        historical state-item handling for equal-size MODFLOW cells.
    """
    if not paths:
        raise ValueError("no IDF files supplied")
    if kind not in {"flux_m3_day", "state"}:
        raise ValueError(f"unsupported kind: {kind}")
    if output not in {"period", "mean_day"}:
        raise ValueError(f"unsupported output: {output}")

    first = read_idf(Path(paths[0]))
    accumulator = np.zeros((first.nrow, first.ncol), dtype=np.float64)

    for raw_path in paths:
        current = read_idf(Path(raw_path))
        if not _same_idf_geometry(first, current):
            raise ValueError(f"IDF geometry mismatch: {raw_path}")
        accumulator += _valid_idf_values(current)

    n = len(paths)
    if kind == "flux_m3_day":
        values = accumulator / float(cell_area_m2) * 1000.0
        if output == "mean_day":
            values /= n
    else:
        values = accumulator / n

    return _ascii_from_idf(first, values)


def aggregate_idf_sign_split(
    paths: Sequence[str | Path],
    *,
    cell_area_m2: float = DEFAULT_MODFLOW_CELL_AREA_M2,
    output: str = "period",
) -> tuple[AsciiGrid, AsciiGrid]:
    """Aggregate positive and negative daily flux contributions separately.

    This matches the historical modflowidf2asc sign classification: values < 0
    go to the negative bucket, zero and positive values to the positive bucket.
    """
    if not paths:
        raise ValueError("no IDF files supplied")
    first = read_idf(Path(paths[0]))
    positive = np.zeros((first.nrow, first.ncol), dtype=np.float64)
    negative = np.zeros((first.nrow, first.ncol), dtype=np.float64)

    for raw_path in paths:
        current = read_idf(Path(raw_path))
        if not _same_idf_geometry(first, current):
            raise ValueError(f"IDF geometry mismatch: {raw_path}")
        values = _valid_idf_values(current)
        positive += np.where(values >= 0.0, values, 0.0)
        negative += np.where(values < 0.0, values, 0.0)

    factor = 1000.0 / float(cell_area_m2)
    positive *= factor
    negative *= factor
    if output == "mean_day":
        positive /= len(paths)
        negative /= len(paths)
    elif output != "period":
        raise ValueError(f"unsupported output: {output}")

    return _ascii_from_idf(first, positive), _ascii_from_idf(first, negative)


def _same_ascii_geometry(a: AsciiGrid, b: AsciiGrid) -> bool:
    return (
        a.ncols == b.ncols
        and a.nrows == b.nrows
        and math.isclose(a.xllcorner, b.xllcorner)
        and math.isclose(a.yllcorner, b.yllcorner)
        and math.isclose(a.cellsize, b.cellsize)
    )


def combine_ascii_grids(
    paths: Sequence[str | Path],
    *,
    weights: Sequence[float] | None = None,
    mean: bool = False,
) -> AsciiGrid:
    """Linear grid algebra for the common GridCalc sum/mean use cases."""
    if not paths:
        raise ValueError("no ASCII grids supplied")
    grids = [read_ascii_grid(p) for p in paths]
    first = grids[0]
    for path, grid in zip(paths[1:], grids[1:]):
        if not _same_ascii_geometry(first, grid):
            raise ValueError(f"ASCII geometry mismatch: {path}")

    if weights is None:
        weights = [1.0] * len(grids)
    if len(weights) != len(grids):
        raise ValueError("weights length must equal number of grids")

    result = np.zeros_like(first.values, dtype=np.float64)
    valid_all = np.ones_like(first.values, dtype=bool)
    for grid, weight in zip(grids, weights):
        valid = np.isfinite(grid.values) & ~np.isclose(grid.values, grid.nodata)
        valid_all &= valid
        result += np.where(valid, grid.values * float(weight), 0.0)

    if mean:
        result /= float(sum(weights))

    result = np.where(valid_all, result, first.nodata)
    return AsciiGrid(
        result,
        first.ncols,
        first.nrows,
        first.xllcorner,
        first.yllcorner,
        first.cellsize,
        first.nodata,
    )


def _expand_inputs(patterns: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw in patterns:
        path = Path(raw)
        if any(ch in raw for ch in "*?[]"):
            matches = sorted(path.parent.glob(path.name))
            files.extend(matches)
        else:
            files.append(path)
    missing = [str(p) for p in files if not p.exists()]
    if missing:
        raise FileNotFoundError(missing[0])
    if not files:
        raise ValueError("input pattern matched no files")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    agg = sub.add_parser("idf-aggregate", help="aggregate an IDF time series to ESRI ASCII")
    agg.add_argument("--input", action="append", required=True, help="file or glob; repeatable")
    agg.add_argument("--output", required=True)
    agg.add_argument("--kind", choices=["flux_m3_day", "state"], required=True)
    agg.add_argument("--stat", choices=["period", "mean_day"], default="period")
    agg.add_argument("--cell-area", type=float, default=DEFAULT_MODFLOW_CELL_AREA_M2)

    split = sub.add_parser("idf-sign-split", help="aggregate positive/negative flux separately")
    split.add_argument("--input", action="append", required=True)
    split.add_argument("--positive-output", required=True)
    split.add_argument("--negative-output", required=True)
    split.add_argument("--stat", choices=["period", "mean_day"], default="period")
    split.add_argument("--cell-area", type=float, default=DEFAULT_MODFLOW_CELL_AREA_M2)

    comb = sub.add_parser("ascii-combine", help="sum or average already-produced ASCII grids")
    comb.add_argument("--input", action="append", required=True)
    comb.add_argument("--output", required=True)
    comb.add_argument("--mean", action="store_true")

    args = parser.parse_args()

    if args.command == "idf-aggregate":
        paths = _expand_inputs(args.input)
        grid = aggregate_idf_series(paths, kind=args.kind, cell_area_m2=args.cell_area, output=args.stat)
        write_ascii_grid(args.output, grid)
        print(f"wrote {args.output} from {len(paths)} IDFs")
        return 0

    if args.command == "idf-sign-split":
        paths = _expand_inputs(args.input)
        pos, neg = aggregate_idf_sign_split(paths, cell_area_m2=args.cell_area, output=args.stat)
        write_ascii_grid(args.positive_output, pos)
        write_ascii_grid(args.negative_output, neg)
        print(f"wrote sign-split outputs from {len(paths)} IDFs")
        return 0

    paths = _expand_inputs(args.input)
    grid = combine_ascii_grids(paths, mean=args.mean)
    write_ascii_grid(args.output, grid)
    print(f"wrote {args.output} from {len(paths)} ASCII grids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
