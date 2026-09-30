"""Compare legacy pre-override and representative-SVAT nature semantics."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def lower_tie_mode(values: pd.Series):
    """Match Alterratools MAJORITY: sorted values, lowest value wins ties."""
    counts = values.value_counts(dropna=False)
    if counts.empty:
        raise ValueError("cannot take majority of empty series")
    maximum = counts.max()
    return min(counts[counts == maximum].index.tolist())


def is_nature_lgn(value: int) -> bool:
    value = int(value)
    return value > 10 and value < 21 and value != 18


def compare_nature_authority(
    schema: pd.DataFrame,
    relation: pd.DataFrame,
    svat_attributes: pd.DataFrame,
) -> pd.DataFrame:
    if not {"HRU", "svat_repr"}.issubset(schema):
        raise ValueError("schema requires HRU and svat_repr")
    if not {"HRU", "svat_orig"}.issubset(relation):
        raise ValueError("relation requires HRU and svat_orig")
    if not {"svat", "landgebruik22"}.issubset(svat_attributes):
        raise ValueError("SVAT attributes require svat and landgebruik22")

    s = schema[["HRU", "svat_repr"]].copy()
    r = relation[["HRU", "svat_orig"]].copy()
    a = svat_attributes[["svat", "landgebruik22"]].copy()
    for frame, columns in ((s, ("HRU", "svat_repr")), (r, ("HRU", "svat_orig")), (a, ("svat", "landgebruik22"))):
        for column in columns:
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype(int)

    if s["HRU"].duplicated().any() or s["svat_repr"].duplicated().any():
        raise ValueError("schema HRU/svat_repr must be unique")
    if a["svat"].duplicated().any():
        raise ValueError("SVAT attributes must be unique by svat")

    members = r.merge(a, left_on="svat_orig", right_on="svat", how="left", validate="many_to_one")
    if members["landgebruik22"].isna().any():
        raise ValueError("member land use missing")
    legacy_lgn = members.groupby("HRU", sort=True)["landgebruik22"].agg(lower_tie_mode)

    representatives = s.merge(a, left_on="svat_repr", right_on="svat", how="left", validate="one_to_one")
    if representatives["landgebruik22"].isna().any():
        raise ValueError("representative land use missing")

    out = pd.DataFrame({
        "hru": representatives["HRU"].to_numpy(int),
        "representative_svat": representatives["svat_repr"].to_numpy(int),
        "legacy_lgn": representatives["HRU"].map(legacy_lgn).to_numpy(int),
        "representative_lgn": representatives["landgebruik22"].to_numpy(int),
    })
    out["legacy_is_nature"] = out["legacy_lgn"].map(is_nature_lgn)
    out["representative_is_nature"] = out["representative_lgn"].map(is_nature_lgn)
    out["lgn_discriminating"] = out["legacy_lgn"] != out["representative_lgn"]
    out["nature_discriminating"] = out["legacy_is_nature"] != out["representative_is_nature"]
    return out.sort_values("hru").reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--relation", required=True)
    parser.add_argument("--svat-info", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = compare_nature_authority(
        pd.read_csv(args.schema, low_memory=False),
        pd.read_csv(args.relation, low_memory=False),
        pd.read_csv(args.svat_info, low_memory=False),
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"HRUs: {len(result)}")
    print(f"land-use code differences: {result['lgn_discriminating'].sum()}")
    print(f"nature differences: {result['nature_discriminating'].sum()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
