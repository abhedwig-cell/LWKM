#!/usr/bin/env python3
"""Canonical LWKM SVAT preparation.

Non-destructive replacement for the historical filter/correction/qualification
preprocessing. Input is a tabular SVAT authority. Output keeps raw values,
corrections and qualification decisions separately.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import pandas as pd

FLAG_COLUMNS = [
    "ghg_sel","gt1_sel","gt2_sel","gt8_sel",
    "kwel_sel","wegzijging_sel","runoff_sel","subinfil_sel",
]

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def require(df: pd.DataFrame, cols: list[str]) -> None:
    missing=[c for c in cols if c not in df.columns]
    if missing: raise ValueError(f"Missing required columns: {missing}")

def prepare(df: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    require(df, ["svat","lu2","kwel(mm/j)","kwel_org(mm/j)",*FLAG_COLUMNS])
    if df["svat"].duplicated().any(): raise ValueError("SVAT ids are not unique")

    # Historical authority: agriculture+nature is exactly lu2 1 or 2.
    lbn=df.loc[df["lu2"].isin([1,2])].copy()
    lbn["is_lwkm_domain"]=True

    # Preserve correction as relation; never overwrite the raw value.
    corr=lbn.loc[lbn["kwel(mm/j)"].ne(lbn["kwel_org(mm/j)"]),
                 ["svat","kwel_org(mm/j)","kwel(mm/j)"]].copy()
    corr=corr.rename(columns={"kwel_org(mm/j)":"kwel_raw_mm_y",
                              "kwel(mm/j)":"kwel_corrected_mm_y"})
    corr["delta_kwel_mm_y"]=corr["kwel_corrected_mm_y"]-corr["kwel_raw_mm_y"]
    corr["correction_id"]="FLEVOLAND_KWEL_DELTA"

    flags=lbn[FLAG_COLUMNS].fillna(0).ne(0)
    qual=pd.DataFrame({"svat":lbn["svat"].to_numpy()})
    for c in FLAG_COLUMNS: qual[c]=flags[c].to_numpy()
    qual["qualification_count"]=flags.sum(axis=1).to_numpy()
    qual["is_valid_for_hru_cluster_building"]=qual["qualification_count"].eq(0)
    qual["qualification_reason_ids"]=[
        ";".join(c for c in FLAG_COLUMNS if bool(row[c])) for _,row in flags.iterrows()
    ]
    return lbn,corr,qual

def write_csv(df: pd.DataFrame,path: Path)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False)

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("input_csv",type=Path)
    p.add_argument("output_dir",type=Path)
    p.add_argument("--expect-domain",type=int,default=427656)
    p.add_argument("--expect-flevoland",type=int,default=4677)
    p.add_argument("--expect-suspected",type=int,default=20934)
    a=p.parse_args()
    df=pd.read_csv(a.input_csv)
    lbn,corr,qual=prepare(df)
    suspected=int((~qual["is_valid_for_hru_cluster_building"]).sum())
    actual={"domain":len(lbn),"flevoland":len(corr),"suspected":suspected}
    expected={"domain":a.expect_domain,"flevoland":a.expect_flevoland,"suspected":a.expect_suspected}
    failures={k:{"expected":expected[k],"actual":actual[k]} for k in expected if expected[k]!=actual[k]}
    if failures: raise SystemExit("Regression gate failed: "+json.dumps(failures,sort_keys=True))

    out=a.output_dir
    write_csv(lbn,out/"svat_lbn.csv")
    write_csv(corr,out/"flevoland_correction.csv")
    write_csv(qual,out/"svat_qualification.csv")
    manifest={
      "schema_version":1,
      "input":{"path":str(a.input_csv),"sha256":sha256(a.input_csv),"rows":len(df)},
      "outputs":{
        "svat_lbn":{"rows":len(lbn)},
        "flevoland_correction":{"rows":len(corr)},
        "svat_qualification":{"rows":len(qual),"suspected":suspected},
      },
      "regression_gates":{"expected":expected,"actual":actual,"passed":True},
      "semantics":{
        "domain":"lu2 in {1,2}",
        "flevoland":"kwel_corrected != kwel_raw; both retained",
        "qualification":"any of eight historical flags => not valid for HRU cluster building",
        "destructive_donor_copy":False,
      },
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")

if __name__=="__main__": main()
