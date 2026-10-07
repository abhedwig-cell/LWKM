"""Conductance-only population diagnostic for the seven physical DRA systems.

This preflight deliberately does not require:
- historical HRU BODH_*1J bottom grids;
- representative dqsat;
- H1 stage time series;
- SWAP rendering.

It answers the first population question independently:
how many of the seven physical layer-1 systems are actually active per HRU, and
how often does the SWAP five-level limit require compression?
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import tempfile

import numpy as np
import pandas as pd

from tools.idf_reader import read_idf


SYSTEM_FILES = {
    "H1": ("H1_MVG", "COND_HL1_250.IDF"),
    "P": ("REMAINING", "COND_primair.IDF"),
    "S": ("REMAINING", "COND_secundair.IDF"),
    "T": ("REMAINING", "COND_tertiair.IDF"),
    "MVG": ("H1_MVG", "COND_greppels.IDF"),
    "PIPE": ("REMAINING", "COND_buisdrainage.IDF"),
    "OLF": ("REMAINING", "COND_SOF_250.IDF"),
}
LEGACY_FIVE = ("P", "S", "T", "PIPE", "OLF")
MODERN_SEVEN = tuple(SYSTEM_FILES)


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def _read_relation(path: Path) -> pd.DataFrame:
    full=pd.read_csv(path,low_memory=False)
    lower={str(c).strip().lower():c for c in full.columns}
    required=("svat_orig","hru","x","y")
    missing=[x for x in required if x not in lower]
    if missing:
        raise ValueError(f"relation missing columns {missing}")
    out=full[[lower["svat_orig"],lower["hru"],lower["x"],lower["y"]]].copy()
    out.columns=["svat","hru","x","y"]
    out["svat"]=pd.to_numeric(out["svat"],errors="raise").astype(np.int64)
    out["hru"]=pd.to_numeric(out["hru"],errors="raise").astype(np.int64)
    out["x"]=pd.to_numeric(out["x"],errors="raise").astype(float)
    out["y"]=pd.to_numeric(out["y"],errors="raise").astype(float)
    if len(out)!=427656:
        raise ValueError(f"expected 427656 relation rows, got {len(out)}")
    if out["svat"].duplicated().any():
        raise ValueError("duplicate SVAT in relation")
    if out["hru"].nunique()!=10242:
        raise ValueError(f"expected 10242 HRUs, got {out['hru'].nunique()}")
    return out


def _extract(zip_path: Path,root: Path) -> Path:
    target=root/zip_path.stem
    target.mkdir(parents=True,exist_ok=False)
    with ZipFile(zip_path) as z:
        z.extractall(target)
    return target


def _find_one(root: Path,name: str) -> Path:
    matches=list(root.rglob(name))
    if len(matches)!=1:
        raise ValueError(f"expected exactly one {name} below {root}, got {len(matches)}")
    return matches[0]


def _rows_cols(relation: pd.DataFrame,reference_idf: Path) -> tuple[np.ndarray,np.ndarray]:
    g=read_idf(reference_idf)
    x=relation["x"].to_numpy(float)
    y=relation["y"].to_numpy(float)
    colf=(x-g.xmin)/g.dx-0.5
    rowf=g.nrow-(y-g.ymin)/g.dy-0.5
    col=np.rint(colf).astype(int)
    row=np.rint(rowf).astype(int)
    if not np.allclose(colf,col,atol=1e-8) or not np.allclose(rowf,row,atol=1e-8):
        raise ValueError("relation coordinates are not exact IDF-cell centres")
    if ((row<0)|(row>=g.nrow)|(col<0)|(col>=g.ncol)).any():
        raise ValueError("relation coordinate outside drainage-grid extent")
    return row,col


def _sample_positive(path: Path,rows: np.ndarray,cols: np.ndarray) -> np.ndarray:
    g=read_idf(path)
    v=np.asarray(g.values,dtype=float)[rows,cols]
    valid=np.isfinite(v) & ~np.isclose(v,float(g.nodata))
    return valid & (v>0.0)


def diagnose_activity(
    relation_csv: Path,
    h1_mvg_zip: Path,
    remaining_zip: Path,
    output_dir: Path,
    *,
    expected_h1_mvg_sha256: str = "3c27cb509dd6d60f5ae8b434fd1ba0f4aca10d81a1b1815b077c5b52a818abfa",
    expected_remaining_sha256: str | None = None,
) -> None:
    output_dir.mkdir(parents=True,exist_ok=True)
    actual_h1=_sha256(h1_mvg_zip)
    actual_remaining=_sha256(remaining_zip)
    if actual_h1.lower()!=expected_h1_mvg_sha256.lower():
        raise ValueError(
            f"H1/MVG bundle SHA mismatch: expected={expected_h1_mvg_sha256} actual={actual_h1}"
        )
    if expected_remaining_sha256 is not None and actual_remaining.lower()!=expected_remaining_sha256.lower():
        raise ValueError(
            "remaining-source bundle SHA mismatch: "
            f"expected={expected_remaining_sha256} actual={actual_remaining}"
        )

    relation=_read_relation(relation_csv)

    with tempfile.TemporaryDirectory(prefix="lwkm_dra_activity_") as td:
        root=Path(td)
        h1root=_extract(h1_mvg_zip,root)
        remroot=_extract(remaining_zip,root)
        roots={"H1_MVG":h1root,"REMAINING":remroot}

        ref=_find_one(h1root,"COND_HL1_250.IDF")
        rows,cols=_rows_cols(relation,ref)

        activity=pd.DataFrame({
            "hru":relation["hru"].to_numpy(int),
        })
        for system,(bundle,name) in SYSTEM_FILES.items():
            activity[system]=_sample_positive(_find_one(roots[bundle],name),rows,cols)

    grouped=activity.groupby("hru",sort=True)[list(MODERN_SEVEN)].any()
    if len(grouped)!=10242:
        raise ValueError(f"expected 10242 grouped HRUs, got {len(grouped)}")

    grouped["legacy_five_active"]=grouped[list(LEGACY_FIVE)].sum(axis=1).astype(int)
    grouped["modern_seven_active"]=grouped[list(MODERN_SEVEN)].sum(axis=1).astype(int)
    grouped["added_by_H1"]=grouped["H1"] & ~grouped[list(LEGACY_FIVE)].any(axis=1)
    grouped["H1_active"]=grouped["H1"]
    grouped["MVG_active"]=grouped["MVG"]
    grouped["compression_required"]=grouped["modern_seven_active"]>5
    grouped["active_systems"]=grouped.apply(
        lambda r:"+".join(s for s in MODERN_SEVEN if bool(r[s])),
        axis=1,
    )

    out=grouped.reset_index()
    out.to_csv(output_dir/"hru_activity.csv",index=False)

    modern_dist={
        str(int(k)):int(v)
        for k,v in out["modern_seven_active"].value_counts().sort_index().items()
    }
    legacy_dist={
        str(int(k)):int(v)
        for k,v in out["legacy_five_active"].value_counts().sort_index().items()
    }
    combo_counts=out["active_systems"].value_counts()
    top_combinations=[
        {"systems":str(name),"count":int(count)}
        for name,count in combo_counts.head(30).items()
    ]
    per_system={
        system:int(out[system].sum())
        for system in MODERN_SEVEN
    }

    result={
        "schema_version":1,
        "status":"DRA_10242_ACTIVITY_PREFLIGHT_PASS",
        "source_identity":{
            "relation_sha256":_sha256(relation_csv),
            "h1_mvg_zip_sha256":actual_h1,
            "remaining_zip_sha256":actual_remaining,
            "remaining_zip_expected_sha256":expected_remaining_sha256,
        },
        "membership_rows":int(len(relation)),
        "hru_count":int(len(out)),
        "per_system_active_hru":per_system,
        "legacy_five_active_count_distribution":legacy_dist,
        "modern_seven_active_count_distribution":modern_dist,
        "hru_requiring_compression":int(out["compression_required"].sum()),
        "hru_with_H1":int(out["H1_active"].sum()),
        "hru_with_MVG":int(out["MVG_active"].sum()),
        "hru_with_H1_or_MVG":int((out["H1_active"]|out["MVG_active"]).sum()),
        "top_active_system_combinations":top_combinations,
        "output":"hru_activity.csv",
        "qualification_scope":"conductance_presence_only_not_full_DRA_admission",
    }
    (output_dir/"summary.json").write_text(
        json.dumps(result,indent=2)+"\n",
        encoding="utf-8",
    )


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--relation",type=Path,required=True)
    p.add_argument("--h1-mvg-zip",type=Path,required=True)
    p.add_argument("--remaining-zip",type=Path,required=True)
    p.add_argument("--expected-remaining-sha256")
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    diagnose_activity(
        a.relation,
        a.h1_mvg_zip,
        a.remaining_zip,
        a.output_dir,
        expected_remaining_sha256=a.expected_remaining_sha256,
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
