"""Build a validated SWP render context from the LWKM SQLite datamodel.

Scientific values are resolved upstream. This layer performs explicit domain
joins and serialization preparation for the template renderer. It is
fail-closed for missing required joins and does not use Wortelzone to override
the authoritative Runs.RDS value in the current 10,242-HRU production path.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import sqlite3
from pathlib import Path
from typing import Any

REQUIRED_HYDRAULIC=(
    "ORES","OSAT","ALFA","NPAR","KSATFIT","LEXP",
    "H_ENPR","KSATEXM","BDENS","ELAS",
)
EPOCH=date(1970,1,1)


def _rows(con,sql,args=()):
    con.row_factory=sqlite3.Row
    return [dict(r) for r in con.execute(sql,args)]


def _one(con,sql,args=(),*,label:str):
    rows=_rows(con,sql,args)
    if not rows:
        return None,f"no {label} row"
    if len(rows)>1:
        return None,f"multiple {label} rows"
    return rows[0],None


def _date_value(value:Any)->str:
    if isinstance(value,datetime):
        return value.date().isoformat()
    if isinstance(value,date):
        return value.isoformat()
    if isinstance(value,(int,float)):
        if float(value)!=int(value):
            raise ValueError(f"non-integral day-offset date: {value}")
        return (EPOCH+timedelta(days=int(value))).isoformat()
    text=str(value).strip()
    if len(text)>=10 and text[4:5]=="-" and text[7:8]=="-":
        return text[:10]
    try:
        number=float(text)
    except ValueError:
        return text
    return _date_value(number)


def _quote(value:Any)->str:
    text=str(value)
    if len(text)>=2 and text[0]==text[-1]=="'":
        return text
    return "'"+text.replace("'","''")+"'"


def _as_int(value:Any)->int:
    if value is None:
        raise ValueError("cannot convert None to int")
    return int(float(value))


def _wortelzone_diagnostic(con,run:dict)->tuple[Any|None,list[str]]:
    """Return the legacy Wortelzone value for QA only.

    Current production authority for RDS is Runs.RDS, which is generated from
    Piet's representative HRU schema. Historical databases used both crop_id
    and croporg_id column spellings, so the diagnostic join is schema-aware.
    """
    cols={r[1] for r in con.execute("pragma table_info(Wortelzone)")}
    if "soil_id" not in cols:
        return None,["Wortelzone has no soil_id column"]
    if "croporg_id" in cols and run.get("croporg_id") is not None:
        rows=_rows(
            con,
            "select RDS from Wortelzone where soil_id=? and croporg_id=?",
            (run["soil_id"],run["croporg_id"]),
        )
    elif "crop_id" in cols and run.get("crop_id") is not None:
        rows=_rows(
            con,
            "select RDS from Wortelzone where soil_id=? and crop_id=?",
            (run["soil_id"],run["crop_id"]),
        )
    else:
        return None,["Wortelzone crop key is unavailable"]
    if len(rows)==1:
        return rows[0].get("RDS"),[]
    if not rows:
        return None,["no Wortelzone QA row"]
    return None,["multiple Wortelzone QA rows"]


def build_context(db_path:str|Path,run_id:int)->dict:
    con=sqlite3.connect(str(db_path))
    con.row_factory=sqlite3.Row
    row=con.execute("select * from Runs where run_id=?",(run_id,)).fetchone()
    if row is None:
        raise KeyError(f"Unknown run_id {run_id}")
    run=dict(row)

    discr=_rows(
        con,
        "select ISUBLAY,ISOILLAY,HSUBLAY,NCOMP "
        "from discretisatie where bodem_id=? and dikte_id=? order by ISUBLAY",
        (run["bodem_id"],run["dikte_id"]),
    )
    props=_rows(
        con,
        "select * from eigenschappen where bodem_id=? order by ISOILLAY",
        (run["bodem_id"],),
    )
    rotation=_rows(
        con,
        "select CROPSTART,CROPEND,CROPNAME,CROPFIL,CROPTYPE "
        "from Gewasrotatie where climate_id=? and crop_id=? and rotation_id=? "
        "order by CROPSTART",
        (run["climate_id"],run["crop_id"],run["rotation_id"]),
    )
    scenario,scenario_issue=_one(
        con,
        "select * from Scenario where scenario_id=?",
        (run["scenario_id"],),
        label="Scenario",
    )
    output,output_issue=_one(
        con,
        "select INLIST_CSV from Output where crop_id=?",
        (run["crop_id"],),
        label="Output",
    )
    resistance,resistance_issue=_one(
        con,
        "select RSOIL from Gewasweerstand where crop_id=?",
        (run["crop_id"],),
        label="Gewasweerstand",
    )
    dznew=_rows(
        con,
        "select ICOMP,DZNEW from DZNEW where dikte_id=? order by ICOMP",
        (run["dikte_id"],),
    )

    issues=[]
    if not discr:
        issues.append("no discretisatie rows")
    if not props:
        issues.append("no eigenschappen rows")
    if not rotation:
        issues.append("no Gewasrotatie rows")
    for issue in (scenario_issue,output_issue,resistance_issue):
        if issue:
            issues.append(issue)

    hydraulic=[]
    for p in props:
        rec={k:p.get(k) for k in REQUIRED_HYDRAULIC}
        missing=[k for k,v in rec.items() if v is None]
        if missing:
            issues.append(f"soil layer {p.get('ISOILLAY')} missing {','.join(missing)}")
        hydraulic.append(rec)

    soilprofile=[]
    for d in discr:
        soilprofile.append({
            "ISUBLAY":_as_int(d["ISUBLAY"]),
            "ISOILLAY":_as_int(d["ISOILLAY"]),
            "HSUBLAY":d["HSUBLAY"],
            "NCOMP":_as_int(d["NCOMP"]),
        })

    textures=[
        {k:p[k] for k in ("PSAND","PSILT","PCLAY","ORGMAT")}
        for p in props
    ]

    croprotation=[]
    for r in rotation:
        croprotation.append({
            "CROPSTART":_date_value(r["CROPSTART"]),
            "CROPEND":_date_value(r["CROPEND"]),
            "CROPNAME":_quote(r["CROPNAME"]),
            "CROPFIL":_quote(r["CROPFIL"]),
            "CROPTYPE":_as_int(r["CROPTYPE"]),
        })

    num_nodes=_as_int(run["NUMNODNEW"])
    if len(dznew)!=num_nodes:
        issues.append(
            f"DZNEW row count {len(dznew)} != NUMNODNEW {num_nodes}"
        )

    swd=(_as_int(scenario["SWDRA"]) if scenario is not None else None)
    swinco=_as_int(run["SWINCO"])
    swbotb=_as_int(run["SWBOTB"])
    wortelzone_rds,qa_notes=_wortelzone_diagnostic(con,run)
    diagnostics=list(qa_notes)
    if wortelzone_rds is not None and float(wortelzone_rds)!=float(run["RDS"]):
        diagnostics.append(
            f"RDS differs from legacy Wortelzone: Runs={run['RDS']} "
            f"Wortelzone={wortelzone_rds}; Runs is production authority"
        )

    ctx={
        "run_id":int(run_id),
        "run":run,
        "TSTART":_date_value(run["TSTART"]),
        "TEND":_date_value(run["TEND"]),
        "INLIST_CSV":_quote(output["INLIST_CSV"]) if output is not None else None,
        "NUMNODNEW":num_nodes,
        "DZNEW":" ".join(str(d["DZNEW"]) for d in dznew),
        "METFIL":_quote(run["METFIL"]),
        "SWETR":_as_int(run["SWETR"]),
        "TABLE_CROPROTATION":croprotation,
        "SWINCO":swinco,
        "SWITCH_SWINCO_OPTION_2":swinco==2,
        "SWITCH_SWINCO_OPTION_3":swinco==3,
        "GWLI":run.get("GWLI"),
        "PONDMX":run["PONDMX"],
        "RSRO":run["RSRO"],
        "RSOIL":resistance["RSOIL"] if resistance is not None else None,
        "TABLE_SOILPROFILE":soilprofile,
        "TABLE_SOILHYDRFUNC":hydraulic,
        "TABLE_SOILTEXTURES":textures,
        "RDS":run["RDS"],
        "RDS_effective":run["RDS"],
        "RDS_run":run["RDS"],
        "RDS_wortelzone":wortelzone_rds,
        "SWDRA":swd,
        "SWITCH_SWDRA_OPTION_1":swd==1 if swd is not None else False,
        "DRFIL":_quote(run["DRFIL"]),
        "SWBBCFILE":_as_int(run["SWBBCFILE"]),
        "BBCFIL":_quote(run["BBCFIL"]),
        "SWBOTB":swbotb,
        "SWITCH_SWBOTB_OPTION_2":swbotb==2,
        "SWITCH_SWBOTB_OPTION_5":swbotb==5,
        "issues":issues,
        "diagnostics":diagnostics,
        "renderable":not issues,
    }
    con.close()
    return ctx


def validate_context(ctx:dict)->None:
    if ctx["issues"]:
        raise ValueError("SWP context unresolved: "+"; ".join(ctx["issues"]))
