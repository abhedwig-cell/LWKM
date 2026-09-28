"""Remaining source-bound v0.38 Runs providers."""
from __future__ import annotations
import pandas as pd

def majority_real(s):
    m=pd.to_numeric(s,errors="coerce").dropna().mode()
    if m.empty: raise ValueError("No values for majority_real")
    return float(m.iloc[0])

def historical_pre_override(members):
    bfe=members["bfe"].mode().iloc[0]; lgn=members["lgn"].mode().iloc[0]
    r=members[(members.bfe==bfe)&(members.lgn==lgn)]
    if r.empty:r=members[members.lgn==lgn]
    rds=majority_real(r["rds"])
    d=members[members.bfe==bfe]
    if d.empty:raise ValueError("No dqsat members matching pre-override BFE")
    dqsat=majority_real(d["dqsat"])
    swetr=0 if int(lgn)<7 else 1
    return {"pre_bfe":bfe,"pre_lgn":lgn,"RDS":round(rds*100),"dqsat":dqsat,"SWETR":swetr}

def apply_representative_historical(values,representative,members):
    out=dict(values)
    if representative is not None:
        out["bodem_id"]=representative["bfe_repr"]
        sid=representative["svat_repr"]
        hit=members.loc[members.svat==sid]
        if hit.empty:raise ValueError(f"Representative SVAT {sid} not in HRU members")
        out["lu_id"]=hit.iloc[0]["lgn"]
        out["RDS"]=int(round(float(representative["rz_repr"])))
    return out

def lookup_ids(values,bodem2bofek:dict,lu2crop:dict,lu2croporg:dict):
    b=int(values["bodem_id"]);s=int(values["soil2_id"]);l=int(values["lu_id"])
    return {"soil_id":bodem2bofek[b],"crop_id":lu2crop[(s,l)],"croporg_id":lu2croporg[(s,l)]}

def metfil(hru:int)->str:return f"{int(hru)}.met"
