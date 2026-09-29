"""Audit historical vs donor-equal HRU water-balance membership."""
from __future__ import annotations
import pandas as pd

def classify_membership(df:pd.DataFrame)->pd.DataFrame:
    """Columns: svat, hru, svatdonor; optional area."""
    d=df.copy()
    d["donor_equal"]=d["svat"].astype(int).eq(d["svatdonor"].astype(int))
    d["historical_isverdacht"]=~d["donor_equal"]
    # reproduce fallback: when no non-donor members, historical code selects all
    any_non=d.groupby("hru")["historical_isverdacht"].transform("any")
    d["historical_issvatwb"]=d["historical_isverdacht"] | ~any_non
    d["candidate_issvatwb"]=d["donor_equal"]
    return d

def summarize(df:pd.DataFrame)->pd.DataFrame:
    d=classify_membership(df)
    if "area" not in d: d["area"]=1.0
    d["hist_area"]=d["area"].where(d["historical_issvatwb"],0)
    d["candidate_area"]=d["area"].where(d["candidate_issvatwb"],0)
    return d.groupby("hru",sort=True).agg(
      n_members=("svat","size"),
      n_donor_equal=("donor_equal","sum"),
      n_historical_wb=("historical_issvatwb","sum"),
      historical_area=("hist_area","sum"),
      candidate_area=("candidate_area","sum"),
    ).reset_index()
