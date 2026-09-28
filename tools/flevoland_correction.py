"""Explicit sparse Flevoland kwel correction relation.

The historical producer is missing. Canonical reconstruction therefore models
the observed correction as data, never as an implicit raster overwrite.
"""
from __future__ import annotations
import pandas as pd

REQUIRED=["svat","kwel_original","kwel_corrected"]

def build_correction_relation(original:pd.DataFrame,corrected:pd.DataFrame,svat="svat",kwel="kwel(mm/j)")->pd.DataFrame:
    a=original[[svat,kwel]].rename(columns={kwel:"kwel_original"})
    b=corrected[[svat,kwel]].rename(columns={kwel:"kwel_corrected"})
    x=a.merge(b,on=svat,how="inner",validate="one_to_one")
    x["delta_kwel"]=x.kwel_corrected-x.kwel_original
    return x.loc[x.delta_kwel.ne(0)].copy()

def apply_correction(base:pd.DataFrame,relation:pd.DataFrame,svat="svat",kwel="kwel(mm/j)")->pd.DataFrame:
    if relation[svat].duplicated().any():raise ValueError("Duplicate SVAT in correction relation")
    x=base.copy()
    corr=relation.set_index(svat)["kwel_corrected"]
    hit=x[svat].isin(corr.index)
    x["kwel_original"]=x[kwel]
    x.loc[hit,kwel]=x.loc[hit,svat].map(corr)
    x["kwel_was_corrected"]=hit
    return x

def validate_relation(relation:pd.DataFrame,expected_count=4677):
    missing=[c for c in REQUIRED if c not in relation]
    if missing:raise ValueError(f"Missing correction fields {missing}")
    if relation.svat.duplicated().any():raise ValueError("Duplicate SVAT correction")
    if len(relation)!=expected_count:raise ValueError(f"Expected {expected_count} corrected SVATs, got {len(relation)}")
