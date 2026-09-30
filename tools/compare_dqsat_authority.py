"""Compare legacy and representative-SVAT dqsat semantics for P12 STATIC04."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AsciiGrid:
    values: np.ndarray
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata: float


def read_ascii_grid(path: str | Path) -> AsciiGrid:
    path = Path(path)
    header: dict[str, float] = {}
    with path.open("r", encoding="utf-8") as handle:
        for _ in range(6):
            parts = handle.readline().split()
            if len(parts) != 2:
                raise ValueError(f"{path}: invalid ESRI ASCII header")
            header[parts[0].lower()] = float(parts[1])
        values = np.loadtxt(handle, dtype=float)

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


def sample_centres(grid: AsciiGrid, x: pd.Series, y: pd.Series) -> np.ndarray:
    xf = pd.to_numeric(x, errors="raise").to_numpy(float)
    yf = pd.to_numeric(y, errors="raise").to_numpy(float)
    col_f = (xf - grid.xllcorner) / grid.cellsize - 0.5
    row_f = grid.nrows - (yf - grid.yllcorner) / grid.cellsize - 0.5

    col = np.rint(col_f).astype(int)
    row = np.rint(row_f).astype(int)
    if not np.allclose(col_f, col, atol=1e-8) or not np.allclose(row_f, row, atol=1e-8):
        raise ValueError("SVAT coordinates are not exact raster-cell centres")
    if np.any(col < 0) or np.any(col >= grid.ncols) or np.any(row < 0) or np.any(row >= grid.nrows):
        raise ValueError("SVAT coordinate falls outside dqsat raster")
    return grid.values[row, col]


def lower_tie_mode(values: pd.Series):
    """Match Alterratools MAJORITY/MAJORITYR4: sorted values, lowest value wins ties."""
    counts = values.value_counts(dropna=False)
    if counts.empty:
        raise ValueError("cannot take majority of empty series")
    max_count = counts.max()
    return min(counts[counts == max_count].index.tolist())


def compare_dqsat_authority(
    schema: pd.DataFrame,
    relation: pd.DataFrame,
    dqsat_grid: AsciiGrid,
) -> pd.DataFrame:
    schema_required = {"HRU", "svat_repr"}
    relation_required = {"svat_orig", "HRU", "x", "y", "bodem370_orig"}
    if not schema_required.issubset(schema):
        raise ValueError(f"schema missing {sorted(schema_required.difference(schema.columns))}")
    if not relation_required.issubset(relation):
        raise ValueError(f"relation missing {sorted(relation_required.difference(relation.columns))}")

    s = schema.loc[:, ["HRU", "svat_repr"]].copy()
    r = relation.loc[:, ["svat_orig", "HRU", "x", "y", "bodem370_orig"]].copy()
    for col in ("HRU", "svat_repr"):
        s[col] = pd.to_numeric(s[col], errors="raise").astype(int)
    for col in ("svat_orig", "HRU", "bodem370_orig"):
        r[col] = pd.to_numeric(r[col], errors="raise").astype(int)

    if s["HRU"].duplicated().any():
        raise ValueError("schema HRU is not unique")
    if s["svat_repr"].duplicated().any():
        raise ValueError("schema representative SVAT is not unique")
    if r["svat_orig"].duplicated().any():
        raise ValueError("relation SVAT is not unique")

    r["dqsat_source"] = sample_centres(dqsat_grid, r["x"], r["y"])
    if np.any(r["dqsat_source"].to_numpy(float) == dqsat_grid.nodata):
        raise ValueError("member SVAT samples a dqsat NODATA cell")

    # HRUlist2SWAP v0.38 changes BFE 204 to 205 immediately after reading bodem.asc.
    r["legacy_bfe"] = r["bodem370_orig"].replace({204: 205})

    legacy_bfe = r.groupby("HRU", sort=True)["legacy_bfe"].agg(lower_tie_mode)
    r["legacy_bfe_majority"] = r["HRU"].map(legacy_bfe)
    selected = r[r["legacy_bfe"] == r["legacy_bfe_majority"]]
    legacy_dqsat = selected.groupby("HRU", sort=True)["dqsat_source"].agg(lower_tie_mode)

    representatives = s.merge(
        r.rename(columns={"svat_orig": "svat_repr"}),
        on="svat_repr",
        how="left",
        validate="one_to_one",
        indicator=True,
        suffixes=("_schema", "_member"),
    )
    if not (representatives["_merge"] == "both").all():
        missing = representatives.loc[representatives["_merge"] != "both", "svat_repr"].tolist()
        raise ValueError(f"representative SVAT missing from relation: {missing[:10]}")
    bad_hru = representatives["HRU_schema"] != representatives["HRU_member"]
    if bad_hru.any():
        bad = representatives.loc[bad_hru, ["HRU_schema", "svat_repr", "HRU_member"]]
        raise ValueError(f"representative SVAT belongs to another HRU: {bad.head().to_dict('records')}")

    out = pd.DataFrame(
        {
            "hru": representatives["HRU_schema"].to_numpy(int),
            "representative_svat": representatives["svat_repr"].to_numpy(int),
            "representative_x": representatives["x"].to_numpy(float),
            "representative_y": representatives["y"].to_numpy(float),
            "legacy_bfe_majority": representatives["HRU_schema"].map(legacy_bfe).to_numpy(),
            "legacy_dqsat": representatives["HRU_schema"].map(legacy_dqsat).to_numpy(float),
            "representative_dqsat": representatives["dqsat_source"].to_numpy(float),
        }
    )
    if out[["legacy_dqsat", "representative_dqsat"]].isna().any().any():
        raise ValueError("incomplete dqsat comparison")
    out["delta_representative_minus_legacy"] = out["representative_dqsat"] - out["legacy_dqsat"]
    out["discriminating"] = out["delta_representative_minus_legacy"] != 0
    return out.sort_values("hru").reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, help="export_HRUschema_10242.csv")
    parser.add_argument("--relation", required=True, help="export_svat_HRU_NRU_10242.csv")
    parser.add_argument("--dqsat-grid", required=True, help="grensvlak_NHIWQ_v2_fill.asc")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = compare_dqsat_authority(
        pd.read_csv(args.schema, low_memory=False),
        pd.read_csv(args.relation, low_memory=False),
        read_ascii_grid(args.dqsat_grid),
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"HRUs: {len(result)}")
    print(f"equal: {(~result['discriminating']).sum()}")
    print(f"discriminating: {result['discriminating'].sum()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
