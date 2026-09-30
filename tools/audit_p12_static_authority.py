"""Audit STATIC02/STATIC03 authority effects against the typed Runs datamodel.

Inputs:
- LWKM SQLite datamodel containing Runs and lu2crop;
- canonical bodem370 classification lookup.

This audit does not re-decide HRU identity. Runs.bodem_id and Runs.lu_id are
interpreted at the renderer boundary as the already selected representative
soil and land-use authorities.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


def _lookup(path:Path)->dict[int,int]:
    out={}
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["status"]!="QUALIFIED_REALIZED":
                continue
            out[int(r["bodem370"])]=int(r["grondsoort2"])
    return out


def audit(database:Path,lookup_csv:Path)->dict:
    soil2=_lookup(lookup_csv)
    con=sqlite3.connect(str(database))
    con.row_factory=sqlite3.Row

    crop={
        (int(r["soil2_id"]),int(r["luse_id"])):int(r["crop_id"])
        for r in con.execute("select soil2_id,luse_id,crop_id from lu2crop")
    }

    total=0
    swetr_mismatch=[]
    soil2_mismatch=[]
    crop_mismatch=[]
    missing_lookup=[]

    for r in con.execute(
        "select run_id,bodem_id,soil2_id,lu_id,crop_id,SWETR "
        "from Runs order by run_id"
    ):
        total+=1
        rid=int(r["run_id"])
        bodem=int(r["bodem_id"])
        lu=int(r["lu_id"])

        expected_swetr=0 if lu<7 else 1
        legacy_swetr=int(r["SWETR"])
        if legacy_swetr!=expected_swetr:
            swetr_mismatch.append({
                "run_id":rid,
                "representative_landuse":lu,
                "runs_swetr":legacy_swetr,
                "representative_swetr":expected_swetr,
            })

        expected_soil2=soil2.get(bodem)
        if expected_soil2 is None:
            missing_lookup.append({"run_id":rid,"bodem_id":bodem})
            continue

        legacy_soil2=int(r["soil2_id"])
        if legacy_soil2!=expected_soil2:
            row={
                "run_id":rid,
                "representative_bodem_id":bodem,
                "runs_soil2":legacy_soil2,
                "canonical_soil2":expected_soil2,
                "representative_landuse":lu,
                "runs_crop_id":int(r["crop_id"]),
            }
            soil2_mismatch.append(row)
            candidate=crop.get((expected_soil2,lu))
            if candidate is None:
                row["canonical_crop_id"]=None
            else:
                row["canonical_crop_id"]=candidate
                if candidate!=int(r["crop_id"]):
                    crop_mismatch.append(dict(row))

    con.close()
    return {
        "runs":total,
        "swetr_mismatch_count":len(swetr_mismatch),
        "soil2_mismatch_count":len(soil2_mismatch),
        "crop_id_mismatch_count":len(crop_mismatch),
        "missing_canonical_soil_lookup_count":len(missing_lookup),
        "swetr_mismatches":swetr_mismatch,
        "soil2_mismatches":soil2_mismatch,
        "crop_id_mismatches":crop_mismatch,
        "missing_canonical_soil_lookup":missing_lookup,
    }


def main(argv=None)->int:
    import argparse
    p=argparse.ArgumentParser(prog="audit-p12-static-authority")
    p.add_argument("database",type=Path)
    p.add_argument("lookup",type=Path)
    p.add_argument("--json",type=Path)
    a=p.parse_args(argv)
    result=audit(a.database,a.lookup)
    text=json.dumps(result,indent=2)
    print(text)
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(text+"\n",encoding="utf-8")
    return 0 if result["missing_canonical_soil_lookup_count"]==0 else 1


if __name__=="__main__":
    raise SystemExit(main())
