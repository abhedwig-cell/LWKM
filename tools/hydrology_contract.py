"""Canonical model-neutral hydrology extraction contract helpers."""
from __future__ import annotations
import pandas as pd

REQUIRED=["case_id","time","location_type","location_id","variable","value","unit","sign_convention"]

def validate_hydrology(df:pd.DataFrame)->dict:
    missing=[c for c in REQUIRED if c not in df.columns]
    if missing:return {"valid":False,"missing_columns":missing}
    dup=df.duplicated(["case_id","time","location_type","location_id","variable"])
    bad_value=pd.to_numeric(df["value"],errors="coerce").isna()
    return {"valid":not dup.any() and not bad_value.any(),
            "rows":len(df),"duplicate_keys":int(dup.sum()),"non_numeric_values":int(bad_value.sum()),
            "cases":int(df["case_id"].nunique()),"variables":sorted(map(str,df["variable"].unique()))}

def normalize_records(records:list[dict])->pd.DataFrame:
    df=pd.DataFrame(records)
    result=validate_hydrology(df)
    if not result["valid"]:raise ValueError(result)
    return df[REQUIRED].sort_values(["case_id","time","location_type","location_id","variable"]).reset_index(drop=True)
