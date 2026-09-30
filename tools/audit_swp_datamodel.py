#!/usr/bin/env python3
"""Audit SWP renderer-domain completeness in an LWKM SQLite datamodel."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def _distribution(con, column):
    return {str(k): int(n) for k,n in con.execute(
        f"select {column},count(*) from Runs group by {column} order by {column}"
    )}


def audit_database(path:Path)->dict:
    con=sqlite3.connect(str(path))
    total=int(con.execute("select count(*) from Runs").fetchone()[0])

    checks={
        "missing_discretisatie":int(con.execute(
            """select count(*) from Runs r where not exists(
               select 1 from discretisatie d
               where d.bodem_id=r.bodem_id and d.dikte_id=r.dikte_id)"""
        ).fetchone()[0]),
        "missing_eigenschappen":int(con.execute(
            """select count(*) from Runs r where not exists(
               select 1 from eigenschappen e where e.bodem_id=r.bodem_id)"""
        ).fetchone()[0]),
        "missing_crop_rotation":int(con.execute(
            """select count(*) from Runs r where not exists(
               select 1 from Gewasrotatie g
               where g.climate_id=r.climate_id
                 and g.crop_id=r.crop_id
                 and g.rotation_id=r.rotation_id)"""
        ).fetchone()[0]),
        "missing_output":int(con.execute(
            """select count(*) from Runs r where not exists(
               select 1 from Output o where o.crop_id=r.crop_id)"""
        ).fetchone()[0]),
        "missing_gewasweerstand":int(con.execute(
            """select count(*) from Runs r where not exists(
               select 1 from Gewasweerstand g where g.crop_id=r.crop_id)"""
        ).fetchone()[0]),
        "missing_scenario":int(con.execute(
            """select count(*) from Runs r where not exists(
               select 1 from Scenario s where s.scenario_id=r.scenario_id)"""
        ).fetchone()[0]),
        "dznew_count_mismatch":int(con.execute(
            """select count(*) from Runs r
               where (select count(*) from DZNEW d where d.dikte_id=r.dikte_id)
                     != cast(r.NUMNODNEW as integer)"""
        ).fetchone()[0]),
        "hydraulic_elas_null_rows":int(con.execute(
            "select count(*) from eigenschappen where ELAS is null"
        ).fetchone()[0]),
    }

    cols={r[1] for r in con.execute("pragma table_info(Wortelzone)")}
    if "croporg_id" in cols:
        root_key="croporg_id"
    elif "crop_id" in cols:
        root_key="crop_id"
    else:
        root_key=None

    rds={"join_key":root_key,"missing":None,"mismatch":None}
    if root_key:
        rds["missing"]=int(con.execute(
            f"""select count(*) from Runs r
                where not exists(
                  select 1 from Wortelzone w
                  where w.soil_id=r.soil_id and w.{root_key}=r.{root_key})"""
        ).fetchone()[0])
        rds["mismatch"]=int(con.execute(
            f"""select count(*) from Runs r join Wortelzone w
                on w.soil_id=r.soil_id and w.{root_key}=r.{root_key}
                where abs(r.RDS-w.RDS)>1e-9"""
        ).fetchone()[0])

    result={
        "database":str(path),
        "runs":total,
        "checks":checks,
        "all_required_renderer_joins_complete":all(v==0 for v in checks.values()),
        "rds_wortelzone_qa":rds,
        "distributions":{
            key:_distribution(con,key)
            for key in ("scenario_id","SWINCO","SWBBCFILE","SWBOTB","SWETR","irrigation_id","TSTART","TEND")
        },
    }
    con.close()
    return result


def main(argv=None)->int:
    p=argparse.ArgumentParser(prog="audit-swp-datamodel")
    p.add_argument("database",type=Path)
    p.add_argument("--json",type=Path)
    a=p.parse_args(argv)
    result=audit_database(a.database)
    text=json.dumps(result,indent=2,sort_keys=True)
    print(text)
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(text+"\n",encoding="utf-8")
    return 0 if result["all_required_renderer_joins_complete"] else 1


if __name__=="__main__":
    raise SystemExit(main())
