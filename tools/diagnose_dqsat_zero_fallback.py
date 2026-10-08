"""Diagnostic-only fallback for zero representative-SVAT dqsat.

The original representative value is retained. If it is zero, derive a
candidate median from strictly positive member dqsat samples within the same
HRU. No production authority is implied.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def diagnostic_positive_median_fallback(
    representative: pd.DataFrame, members: pd.DataFrame
) -> pd.DataFrame:
    required_rep={"hru","representative_dqsat"}
    required_members={"hru","dqsat"}
    if not required_rep.issubset(representative):
        raise ValueError("representative table missing required columns")
    if not required_members.issubset(members):
        raise ValueError("member table missing required columns")
    r=representative.loc[:,["hru","representative_dqsat"]].copy()
    m=members.loc[:,["hru","dqsat"]].copy()
    if r.hru.duplicated().any():raise ValueError("duplicate representative HRU")
    r["representative_dqsat"]=pd.to_numeric(r.representative_dqsat,errors="raise")
    m["dqsat"]=pd.to_numeric(m.dqsat,errors="raise")
    if (~np.isfinite(r.representative_dqsat)).any() or (~np.isfinite(m.dqsat)).any():
        raise ValueError("non-finite dqsat")
    if (r.representative_dqsat<0).any() or (m.dqsat<0).any():
        raise ValueError("negative dqsat")
    if not set(r.hru).issubset(set(m.hru)):
        raise ValueError("representative HRU absent from member population")
    positive=m.loc[m.dqsat>0].groupby("hru").dqsat.agg(
        positive_member_count="count",
        positive_median="median",
        positive_mean="mean",
    )
    result=r.join(positive,on="hru")
    result["fallback_applied"]=result.representative_dqsat.eq(0)
    if result.loc[result.fallback_applied,"positive_median"].isna().any():
        raise ValueError("zero representative dqsat with no positive member fallback")
    result["diagnostic_candidate_dqsat"]=result.representative_dqsat.where(
        ~result.fallback_applied,result.positive_median)
    result["authority_status"]=np.where(
        result.fallback_applied,
        "DIAGNOSTIC_POSITIVE_MEDIAN_NOT_ADMITTED",
        "REPRESENTATIVE_SVAT_SOURCE")
    return result.sort_values("hru").reset_index(drop=True)
