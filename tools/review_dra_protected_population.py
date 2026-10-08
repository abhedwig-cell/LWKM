"""Standalone machine-readable review of protected DRA candidate population.

Consumes the output of diagnose_dra_10242.py and fails closed on missing HRUs,
duplicate identities, upstream failures, or unresolved protected candidates.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

PASS={"NO_COMPRESSION","CANDIDATE_NOT_ADMITTED"}

def review(path:Path,expected_hrus:int|None=None):
    frame=pd.read_csv(path,low_memory=False)
    required={"hru","status","groups","max_error_m","compression_required"}
    if not required.issubset(frame):
        raise ValueError("missing protected candidate columns")
    if frame.hru.duplicated().any():raise ValueError("duplicate HRU")
    if expected_hrus is not None and len(frame)!=expected_hrus:
        raise ValueError("unexpected HRU population size")
    status=frame.status.fillna("MISSING_STATUS")
    bad=frame.loc[~status.isin(PASS),["hru","status"]]
    return {"schema_version":1,
            "status":"PROTECTED_CANDIDATE_SCREEN_PASS" if bad.empty else "PROTECTED_CANDIDATE_SCREEN_FAIL",
            "hru_count":len(frame),"failed_hru_count":len(bad),
            "failed_hru_ids":bad.hru.astype(str).tolist(),
            "status_counts":{str(k):int(v) for k,v in status.value_counts().items()},
            "production_admission":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate-csv",type=Path,required=True)
    p.add_argument("--output-json",type=Path,required=True)
    p.add_argument("--expected-hrus",type=int)
    a=p.parse_args()
    result=review(a.candidate_csv,a.expected_hrus)
    a.output_json.parent.mkdir(parents=True,exist_ok=True)
    a.output_json.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))
    return 1 if result["failed_hru_count"] else 0
if __name__=="__main__":raise SystemExit(main())
