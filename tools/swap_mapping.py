"""Declarative HRU -> SWAP case mapping primitives."""
from __future__ import annotations
import hashlib, json
import pandas as pd

def majority(s:pd.Series):
    m=s.dropna().mode()
    return m.iloc[0] if len(m) else None

def map_hru_members(members:pd.DataFrame, representative:dict|None=None, irrigation_threshold=.37)->dict:
    if members.empty: raise ValueError("HRU has no members")
    out={}
    out["HRU"]=int(members["HRU"].iloc[0])
    out["area_m2"]=float(pd.to_numeric(members["area_m2"]).sum())
    out["nusvat"]=int(len(members))
    out["soil2_id"]=majority(members["soil2"])
    out["SWBOTB"]=int(majority(members["bbc"]))
    out["SWBBCFILE"]=0 if out["SWBOTB"]==7 else 1
    out["lu_id"]=majority(members["lgn"])
    out["bodem_id"]=majority(members["bfe"])
    irrig=pd.to_numeric(members["irrigation_switch"],errors="coerce").fillna(0)
    frac=float((irrig>0).mean())
    out["irrigation_fraction"]=frac
    out["irrigation_id"]=majority(irrig[irrig>0]) if frac>irrigation_threshold else 0
    if representative is not None:
        if representative.get("bfe_repr") is not None:
            out["bodem_id"]=representative["bfe_repr"]
        if representative.get("lgn_repr") is not None:
            out["lu_id"]=representative["lgn_repr"]
        if representative.get("rz_repr") is not None:
            out["RDS"]=float(representative["rz_repr"])/100.0
    return out

def stable_hash(value)->str:
    payload=json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(payload).hexdigest()

def case_dependency_record(case:dict,*,mapping_version:str,swap_version:str,
                           meteo_ref:str,boundary_ref:str,soil_ref:str,crop_ref:str)->dict:
    deps={"case":case,"mapping_version":mapping_version,"swap_version":swap_version,
          "meteo_ref":meteo_ref,"boundary_ref":boundary_ref,"soil_ref":soil_ref,"crop_ref":crop_ref}
    return {"HRU":case["HRU"],"dependency_hash":stable_hash(deps),"dependencies":deps}
