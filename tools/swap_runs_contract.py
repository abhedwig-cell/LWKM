"""Historical v0.38 Runs-table contract and strict row builder."""
from __future__ import annotations

RUN_COLUMNS=[
"run_id","scenario_id","bodem_id","soil2_id","lu_id","climate_id","SWBBCFILE","SWBOTB","dqsat",
"BBCFIL","DRFIL","METFIL","irrigation_id","solute_id","rotation_id","SWINCO","GWLI","RDS","PONDMX",
"RSRO","tempBot","glk","area","xc","yc","col","row","nusvat","TSTART","TEND","SWETR","soil_id",
"crop_id","croporg_id","dikte_id","COFANI","NUMNODNEW"]

CONSTANTS={"scenario_id":"direct","climate_id":"__","solute_id":0,"rotation_id":"max",
           "SWINCO":2,"dikte_id":1700,"COFANI":1.0,"NUMNODNEW":43}

def build_runs_row(mapped:dict,providers:dict)->dict:
    # Historical v0.38 adapter constants are configuration authority. They must
    # not be overridden accidentally by mapped/member-derived data.
    row=dict(mapped);row.update(CONSTANTS)
    hru=int(row.get("HRU",row.get("run_id")))
    row["run_id"]=hru
    row.setdefault("BBCFIL",hru);row.setdefault("DRFIL",hru)
    # METFIL is not assumed equal to HRU; historical code generates a file/station reference.
    for field,provider in providers.items():
        if field not in row or row[field] is None:row[field]=provider(mapped)
    missing=[c for c in RUN_COLUMNS if c not in row or row[c] is None]
    if missing:raise ValueError(f"Cannot emit v0.38 Runs row; unresolved fields: {missing}")
    return {c:row[c] for c in RUN_COLUMNS}

def validate_runs_row(row:dict)->None:
    if list(row)!=RUN_COLUMNS:raise ValueError("Runs row columns/order do not match v0.38 contract")
    if int(row["SWBBCFILE"])!=(0 if int(row["SWBOTB"])==7 else 1):
        raise ValueError("SWBBCFILE inconsistent with SWBOTB")
    if float(row["PONDMX"])<0:raise ValueError("Negative PONDMX")
