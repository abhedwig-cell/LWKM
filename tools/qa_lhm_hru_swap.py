#!/usr/bin/env python3
"""
QA and effect accounting for the LHM -> SVAT -> HRU -> SWAP workflow.

Non-destructive: scientific stage definitions live in versioned configuration.
Requires pandas >= 2.0 and numpy >= 1.24.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def sniff_separator(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        sample = fh.read(16384)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def read_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep=sniff_separator(path), low_memory=False, encoding="utf-8-sig")


def resolve_col(df: pd.DataFrame, requested: str) -> str:
    if requested in df.columns:
        return requested
    lookup = {str(c).strip().casefold(): str(c) for c in df.columns}
    key = requested.strip().casefold()
    if key in lookup:
        return lookup[key]
    raise KeyError(f"Column not found: {requested!r}")


def maybe_col(df: pd.DataFrame, requested: str | None) -> str | None:
    if not requested:
        return None
    try:
        return resolve_col(df, requested)
    except KeyError:
        return None


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def flag(s: pd.Series) -> pd.Series:
    return num(s).fillna(0) > 0


def wmean(values: pd.Series, weights: pd.Series) -> float:
    v = num(values)
    w = num(weights)
    m = v.notna() & w.notna() & (w > 0)
    if not bool(m.any()):
        return float("nan")
    return float(np.average(v[m].to_numpy(float), weights=w[m].to_numpy(float)))


def wrmse(values: pd.Series, weights: pd.Series) -> float:
    v = num(values)
    w = num(weights)
    m = v.notna() & w.notna() & (w > 0)
    if not bool(m.any()):
        return float("nan")
    vv = v[m].to_numpy(float)
    ww = w[m].to_numpy(float)
    return float(math.sqrt(np.average(vv * vv, weights=ww)))


def summary(df: pd.DataFrame, id_col: str, area_col: str) -> dict[str, Any]:
    a = num(df[area_col])
    return {
        "rows": int(len(df)),
        "unique_ids": int(df[id_col].nunique(dropna=True)),
        "duplicate_id_rows": int(df[id_col].duplicated(keep=False).sum()),
        "area_m2": float(a.fillna(0).sum()),
        "missing_area_rows": int(a.isna().sum()),
        "nonpositive_area_rows": int((a.fillna(0) <= 0).sum()),
    }


def hydrology_stage(df: pd.DataFrame, area_col: str, fields: list[str], stage: str) -> list[dict[str, Any]]:
    rows = []
    a = num(df[area_col])
    for req in fields:
        c = maybe_col(df, req)
        if c is None:
            rows.append({"stage": stage, "variable": req, "status": "MISSING_COLUMN"})
            continue
        v = num(df[c])
        m = v.notna() & a.notna() & (a > 0)
        rows.append({
            "stage": stage,
            "variable": c,
            "status": "OK",
            "n_valid": int(m.sum()),
            "area_m2": float(a[m].sum()),
            "weighted_mean": wmean(v, a),
            "minimum": v.min(skipna=True),
            "p01": v.quantile(0.01),
            "median": v.median(skipna=True),
            "p99": v.quantile(0.99),
            "maximum": v.max(skipna=True),
        })
    return rows


def domain_effect(base: pd.DataFrame, selected: pd.DataFrame, area_col: str, fields: list[str]) -> list[dict[str, Any]]:
    rows = []
    ab = num(base[area_col])
    aa = num(selected[area_col])
    for req in fields:
        cb = maybe_col(base, req)
        ca = maybe_col(selected, req)
        if cb is None or ca is None:
            rows.append({"variable": req, "status": "MISSING_COLUMN"})
            continue
        before = wmean(base[cb], ab)
        after = wmean(selected[ca], aa)
        rows.append({
            "variable": cb,
            "status": "OK",
            "weighted_mean_before": before,
            "weighted_mean_after": after,
            "delta_after_minus_before": after - before,
            "rows_before": int(len(base)),
            "rows_after": int(len(selected)),
            "area_m2_before": float(ab.fillna(0).sum()),
            "area_m2_after": float(aa.fillna(0).sum()),
        })
    return rows


def correction_diagnostics(df: pd.DataFrame, area_col: str, specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    w = num(df[area_col])
    for spec in specs:
        src = maybe_col(df, spec["source"])
        dst = maybe_col(df, spec["corrected"])
        if src is None or dst is None:
            rows.append({
                "correction_id": spec["id"],
                "status": "MISSING_COLUMN",
                "official_correction": bool(spec.get("official_correction", False)),
            })
            continue
        m = pd.Series(True, index=df.index)
        if spec.get("mask_column"):
            mc = maybe_col(df, spec["mask_column"])
            if mc is None:
                rows.append({
                    "correction_id": spec["id"],
                    "status": "MISSING_MASK_COLUMN",
                    "official_correction": bool(spec.get("official_correction", False)),
                })
                continue
            m &= flag(df[mc])
        s = num(df[src])
        d = num(df[dst])
        valid = m & s.notna() & d.notna()
        delta = d - s
        tol = float(spec.get("tolerance", 0.0))
        changed = valid & (delta.abs() > tol)
        rows.append({
            "correction_id": spec["id"],
            "status": "OK",
            "source": src,
            "corrected": dst,
            "official_correction": bool(spec.get("official_correction", False)),
            "interpretation": spec.get("interpretation", ""),
            "n_evaluable": int(valid.sum()),
            "n_changed": int(changed.sum()),
            "area_m2_evaluable": float(w[valid].fillna(0).sum()),
            "area_m2_changed": float(w[changed].fillna(0).sum()),
            "weighted_mean_source": wmean(s[valid], w[valid]),
            "weighted_mean_corrected": wmean(d[valid], w[valid]),
            "weighted_mean_delta": wmean(delta[valid], w[valid]),
            "weighted_mae_delta": wmean(delta[valid].abs(), w[valid]),
            "weighted_rmse_delta": wrmse(delta[valid], w[valid]),
            "max_abs_delta": delta[valid].abs().max(skipna=True),
        })
    return rows


def qualification(df: pd.DataFrame, area_col: str, fields: list[str]) -> tuple[list[dict[str, Any]], pd.Series]:
    rows = []
    w = num(df[area_col])
    any_rule = pd.Series(False, index=df.index)
    total_area = float(w.fillna(0).sum())
    for req in fields:
        c = maybe_col(df, req)
        if c is None:
            rows.append({"rule_field": req, "status": "MISSING_COLUMN"})
            continue
        f = flag(df[c])
        any_rule |= f
        ar = float(w[f].fillna(0).sum())
        rows.append({
            "rule_field": c,
            "status": "OK",
            "n_flagged": int(f.sum()),
            "area_m2_flagged": ar,
            "fraction_rows": float(f.mean()) if len(f) else np.nan,
            "fraction_area": ar / total_area if total_area > 0 else np.nan,
        })
    ar = float(w[any_rule].fillna(0).sum())
    rows.append({
        "rule_field": "__ANY_QUALIFICATION_RULE__",
        "status": "OK",
        "n_flagged": int(any_rule.sum()),
        "area_m2_flagged": ar,
        "fraction_rows": float(any_rule.mean()) if len(any_rule) else np.nan,
        "fraction_area": ar / total_area if total_area > 0 else np.nan,
    })
    return rows, any_rule


def representation_effects(
    svat: pd.DataFrame,
    mapping: pd.DataFrame,
    hru_schema: pd.DataFrame,
    cfg: dict[str, Any],
    fields: list[str],
    area_col: str,
    svat_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mc = cfg["hru_map"]
    map_svat = resolve_col(mapping, mc["svat"])
    map_hru = resolve_col(mapping, mc["hru"])
    map_donor = maybe_col(mapping, mc.get("cluster_donor"))

    base = svat.copy()
    base["_qa_svat"] = pd.to_numeric(base[svat_id], errors="coerce")
    m = mapping.copy()
    m["_qa_svat"] = pd.to_numeric(m[map_svat], errors="coerce")
    m["_qa_hru"] = pd.to_numeric(m[map_hru], errors="coerce")

    source_cols = [c for c in [maybe_col(base, x) for x in fields] if c]
    joined = m.merge(base[["_qa_svat", area_col] + source_cols], on="_qa_svat", how="left", validate="many_to_one")

    info = {
        "map_rows": int(len(m)),
        "mapped_unique_svat": int(m["_qa_svat"].nunique(dropna=True)),
        "mapped_unique_hru": int(m["_qa_hru"].nunique(dropna=True)),
        "missing_svat_in_base": int(joined[area_col].isna().sum()),
    }
    rows = []

    if map_donor:
        m["_qa_donor"] = pd.to_numeric(m[map_donor], errors="coerce")
        info["cluster_donor_diff_rows"] = int(
            (m["_qa_svat"].notna() & m["_qa_donor"].notna() & (m["_qa_svat"] != m["_qa_donor"])).sum()
        )
        donor_base = base.rename(columns={"_qa_svat": "_qa_donor"})
        d = joined.merge(
            donor_base[["_qa_donor"] + source_cols],
            on="_qa_donor", how="left", suffixes=("_orig", "_donor")
        )
        w = num(d[area_col])
        for c in source_cols:
            a = num(d[c + "_orig"])
            b = num(d[c + "_donor"])
            delta = b - a
            rows.append({
                "representation": "cluster_donor",
                "variable": c,
                "n_pairs": int(delta.notna().sum()),
                "weighted_mean_delta": wmean(delta, w),
                "weighted_mae": wmean(delta.abs(), w),
                "weighted_rmse": wrmse(delta, w),
            })

    sc = cfg["hru_schema"]
    sh = resolve_col(hru_schema, sc["hru"])
    sr = resolve_col(hru_schema, sc["representative_svat"])
    schema = hru_schema[[sh, sr]].copy()
    schema["_qa_hru"] = pd.to_numeric(schema[sh], errors="coerce")
    schema["_qa_repr"] = pd.to_numeric(schema[sr], errors="coerce")

    r = joined.merge(schema[["_qa_hru", "_qa_repr"]], on="_qa_hru", how="left", validate="many_to_one")
    repr_base = base.rename(columns={"_qa_svat": "_qa_repr"})
    r = r.merge(
        repr_base[["_qa_repr"] + source_cols],
        on="_qa_repr", how="left", suffixes=("_orig", "_repr")
    )
    info["unique_representative_svat"] = int(r["_qa_repr"].nunique(dropna=True))
    info["missing_representative_svat_rows"] = int(r["_qa_repr"].isna().sum())
    w = num(r[area_col])
    for c in source_cols:
        a = num(r[c + "_orig"])
        b = num(r[c + "_repr"])
        delta = b - a
        rows.append({
            "representation": "hru_representative_svat",
            "variable": c,
            "n_pairs": int(delta.notna().sum()),
            "weighted_mean_delta": wmean(delta, w),
            "weighted_mae": wmean(delta.abs(), w),
            "weighted_rmse": wrmse(delta, w),
        })

    return rows, info


def report_md(path: Path, base: dict[str, Any], selected: dict[str, Any], corr: list[dict[str, Any]], q: list[dict[str, Any]], hru: dict[str, Any]) -> None:
    lines = [
        "# LHM -> SVAT -> HRU effect report",
        "",
        "## Dataset",
        f"- Rows: {base['rows']}",
        f"- Unique SVAT IDs: {base['unique_ids']}",
        f"- Area: {base['area_m2']/1e6:.3f} km2",
        "",
        "## LWKM domain selection",
        f"- Rows after selection: {selected['rows']}",
        f"- Area after selection: {selected['area_m2']/1e6:.3f} km2",
        "",
        "domain_effect.csv reports selection effects, not corrections to retained SVATs.",
        "",
        "## Correction diagnostics",
    ]
    for x in corr:
        lines.append(
            f"- {x['correction_id']}: status={x['status']}, changed={x.get('n_changed','NA')}, "
            f"official={x.get('official_correction',False)}"
        )
    lines += ["", "## Qualification"]
    for x in q:
        lines.append(f"- {x['rule_field']}: status={x['status']}, flagged={x.get('n_flagged','NA')}")
    lines += [
        "",
        "## HRU mapping",
        f"- Mapping rows: {hru.get('map_rows','NA')}",
        f"- Unique mapped SVATs: {hru.get('mapped_unique_svat','NA')}",
        f"- Unique HRUs: {hru.get('mapped_unique_hru','NA')}",
        f"- Cluster-donor changes: {hru.get('cluster_donor_diff_rows','NA')}",
        f"- Unique HRU representative SVATs: {hru.get('unique_representative_svat','NA')}",
        "",
        "## Guardrails",
        "- kwel_org -> kwel is a diagnostic until the Flevoland correction producer is bound.",
        "- A qualification flag is not itself a replacement action.",
        "- Cluster donor and HRU representative SVAT are distinct relations.",
        "- A SWAP difference is not a pure model effect until representation and input changes are accounted for.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ns = ap.parse_args()

    cfg = json.loads(ns.config.read_text(encoding="utf-8"))
    root = Path(cfg.get("data_root", "."))

    def path_for(key: str) -> Path:
        value = cfg["inputs"].get(key)
        if not value:
            raise ValueError(f"Input not configured: {key}")
        p = Path(value)
        return p if p.is_absolute() else root / p

    ns.out.mkdir(parents=True, exist_ok=True)

    svat = read_table(path_for("svat_table"))
    sid = resolve_col(svat, cfg["columns"]["svat_id"])
    area = resolve_col(svat, cfg["columns"]["area"])
    domain = resolve_col(svat, cfg["columns"]["domain_flag"])

    base = summary(svat, sid, area)
    if base["duplicate_id_rows"]:
        raise ValueError(f"SVAT key not unique: {base['duplicate_id_rows']} duplicate rows")

    selected = svat[flag(svat[domain])].copy()
    sel = summary(selected, sid, area)
    fields = cfg["columns"]["hydrology"]

    pd.DataFrame(
        hydrology_stage(svat, area, fields, "SVAT_BASE_PHYSICAL") +
        hydrology_stage(selected, area, fields, "SVAT_DOMAIN_SELECTED")
    ).to_csv(ns.out / "stage_hydrology.csv", index=False)

    pd.DataFrame(domain_effect(svat, selected, area, fields)).to_csv(ns.out / "domain_effect.csv", index=False)

    corr = correction_diagnostics(selected, area, cfg.get("correction_pairs", []))
    pd.DataFrame(corr).to_csv(ns.out / "correction_diagnostics.csv", index=False)

    qual, any_rule = qualification(selected, area, cfg["columns"]["qualification_flags"])
    pd.DataFrame(qual).to_csv(ns.out / "qualification_counts.csv", index=False)

    mapping = read_table(path_for("svat_hru_map"))
    schema = read_table(path_for("hru_schema"))
    repr_rows, hru_info = representation_effects(selected, mapping, schema, cfg, fields, area, sid)
    pd.DataFrame(repr_rows).to_csv(ns.out / "representation_effect.csv", index=False)
    pd.DataFrame([hru_info]).to_csv(ns.out / "hru_mapping_summary.csv", index=False)

    result = {
        "dataset": base,
        "selected_dataset": sel,
        "qualification_union_rows": int(any_rule.sum()),
        "hru_mapping": hru_info,
        "guardrails": {
            "correction_requires_explicit_authority": True,
            "qualification_is_not_replacement": True,
            "cluster_donor_is_not_hru_representative": True,
        },
    }
    (ns.out / "qa_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    report_md(ns.out / "report.md", base, sel, corr, qual, hru_info)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
