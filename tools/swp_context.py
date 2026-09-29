"""Build a validated SWP render context from the legacy LWKM SQLite model.

This module is intentionally fail-closed. It does not guess SWAPtools defaults.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

REQUIRED_HYDRAULIC=("ORES","OSAT","ALFA","NPAR","KSATFIT","LEXP","H_ENPR","KSATEXM","BDENS","ELAS")

def _rows(con,sql,args=()):
    con.row_factory=sqlite3.Row
    return [dict(r) for r in con.execute(sql,args)]

def build_context(db_path:str|Path,run_id:int)->dict:
    con=sqlite3.connect(str(db_path)); con.row_factory=sqlite3.Row
    row=con.execute("select * from Runs where run_id=?",(run_id,)).fetchone()
    if row is None: raise KeyError(f"Unknown run_id {run_id}")
    run=dict(row)

    discr=_rows(con,"select * from discretisatie where bodem_id=? and dikte_id=? order by ISUBLAY",
                (run["bodem_id"],run["dikte_id"]))
    props=_rows(con,"select * from eigenschappen where bodem_id=? order by ISOILLAY",(run["bodem_id"],))
    root=_rows(con,"select * from Wortelzone where soil_id=? and crop_id=?",
               (run["soil_id"],run["crop_id"]))

    issues=[]
    if not discr: issues.append("no discretisatie rows")
    if not props: issues.append("no eigenschappen rows")
    if len(root)>1: issues.append("multiple Wortelzone rows")
    if root and float(root[0]["RDS"]) != float(run["RDS"]):
        issues.append(f"RDS conflict Runs={run['RDS']} Wortelzone={root[0]['RDS']}")

    hydraulic=[]
    for p in props:
        rec={k:p.get(k) for k in REQUIRED_HYDRAULIC}
        missing=[k for k,v in rec.items() if v is None]
        if missing: issues.append(f"soil layer {p['ISOILLAY']} missing {','.join(missing)}")
        hydraulic.append(rec)

    textures=[{k:p[k] for k in ("PSAND","PSILT","PCLAY","ORGMAT")} for p in props]
    soilprofile=[{k:d[k] for k in ("ISUBLAY","ISOILLAY","HSUBLAY","NCOMP")} for d in discr]

    return {
      "run_id":run_id,"run":run,
      "TABLE_SOILPROFILE":soilprofile,
      "TABLE_SOILHYDRFUNC":hydraulic,
      "TABLE_SOILTEXTURES":textures,
      "RDS_run":run["RDS"],
      "RDS_wortelzone":root[0]["RDS"] if root else None,
      "SWBOTB":run["SWBOTB"],
      "issues":issues,
      "renderable":not issues,
    }

def validate_context(ctx:dict)->None:
    if ctx["issues"]:
        raise ValueError("SWP context unresolved: "+"; ".join(ctx["issues"]))
