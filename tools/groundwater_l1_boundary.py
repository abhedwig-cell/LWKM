"""W08-GW-L1: strict daily volume aggregation, positive into MODFLOW layer 1.

Input CSVs: cells(date,cell_id,flf,lat,ghb,wel), membership(hru_id,cell_id,area_m2).
Fluxes are already integrated m3 per calendar day, never instantaneous rates.
Each full cell belongs to exactly one HRU. Fractional support needs a separate
qualified allocation contract and is deliberately rejected by this version.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

COMPONENTS = ("flf", "lat", "ghb", "wel")


def aggregate(cells, membership, *, start, end, full_cell_area=62500.0):
    cells, membership = cells.copy(), membership.copy()
    if set(membership.columns) != {"hru_id", "cell_id", "area_m2"}:
        raise ValueError("membership requires exactly hru_id, cell_id, area_m2")
    if not {"date", "cell_id", *COMPONENTS}.issubset(cells.columns):
        raise ValueError("missing daily cell component columns")
    if cells.empty or membership.empty or membership.isna().any().any():
        raise ValueError("empty or incomplete membership/input")
    if membership.cell_id.duplicated().any():
        raise ValueError("duplicate cell membership: fractional/overlap unsupported")
    area = pd.to_numeric(membership.area_m2, errors="raise")
    if not np.isfinite(area).all() or not (area == full_cell_area).all():
        raise ValueError("membership must use full MODFLOW cell area")
    membership["area_m2"] = area
    dates = pd.date_range(start, end, freq="D").strftime("%Y-%m-%d").tolist()
    if not dates or cells[["date", "cell_id"]].isna().any().any():
        raise ValueError("invalid dates or cell IDs")
    if not cells.date.astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("dates must be ISO calendar days")
    if cells.duplicated(["date", "cell_id"]).any():
        raise ValueError("duplicate daily cell")
    cells = cells.loc[cells.cell_id.isin(membership.cell_id)].copy()
    if set(cells.date) != set(dates):
        raise ValueError("missing/extra calendar days")
    counts = cells.groupby("date").cell_id.nunique()
    if not (counts == len(membership)).all():
        raise ValueError("incomplete daily membership coverage")
    for name in COMPONENTS:
        cells[name] = pd.to_numeric(cells[name], errors="raise")
        if not np.isfinite(cells[name]).all():
            raise ValueError(f"nonfinite {name}")
    joined = cells.merge(membership, on="cell_id", validate="many_to_one")
    keys = ["hru_id", "date"]
    out = joined.groupby(keys, sort=True).area_m2.sum().to_frame()
    for name in COMPONENTS:
        for suffix, values in (("in", joined[name].clip(lower=0)),
                               ("out", -joined[name].clip(upper=0)),
                               ("net", joined[name])):
            col = f"{name}_{suffix}_m3_d"
            out[col] = joined.assign(value=values).groupby(keys).value.sum()
        out[f"{name}_mm_d"] = out[f"{name}_net_m3_d"] * 1000 / out.area_m2
    out["q_ext_m3_d"] = sum(out[f"{n}_net_m3_d"] for n in COMPONENTS)
    out["q_ext_mm_d"] = out.q_ext_m3_d * 1000 / out.area_m2
    return out.reset_index()


def lateral_from_faces(faces, cell_ids):
    """One oriented face, positive from_cell -> to_cell; outer cell may be external.

    face_id must be globally unique within this daily call. Return signed cell
    volumes; internal faces cancel algebraically in the selected group.
    """
    if faces.face_id.duplicated().any():
        raise ValueError("duplicate face identity")
    if faces[["face_id", "from_cell", "to_cell", "volume_m3"]].isna().any().any():
        raise ValueError("incomplete face")
    if (faces.from_cell == faces.to_cell).any() or not np.isfinite(faces.volume_m3).all():
        raise ValueError("invalid face")
    result = pd.Series(0.0, index=pd.Index(cell_ids, name="cell_id"))
    if not result.index.is_unique:
        raise ValueError("duplicate selected cell")
    for row in faces.itertuples(index=False):
        if row.from_cell in result.index:
            result.loc[row.from_cell] -= row.volume_m3
        if row.to_cell in result.index:
            result.loc[row.to_cell] += row.volume_m3
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("cells", "membership", "contract", "out"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    a = p.parse_args()
    contract = json.loads(a.contract.read_text())
    required = {"units": "m3/calendar_day", "positive": "into_layer1",
                "layer": 1, "components": list(COMPONENTS)}
    if any(contract.get(k) != v for k, v in required.items()):
        raise ValueError("unresolved source units/sign/layer/component contract")
    if not contract.get("evidence_refs"):
        raise ValueError("source semantics evidence required")
    result = aggregate(pd.read_csv(a.cells), pd.read_csv(a.membership), start=a.start, end=a.end)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(a.out, index=False, float_format="%.12g")
    audit = {"status": "W08_GW_L1_CANDIDATE_NOT_ADMITTED", "rows": len(result),
             "contract": contract, "identities": {str(x): hashlib.sha256(x.read_bytes()).hexdigest()
             for x in (a.cells, a.membership, a.contract, a.out)}}
    a.out.with_suffix(".audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"status": audit["status"], "rows": len(result)}))


if __name__ == "__main__":
    main()
