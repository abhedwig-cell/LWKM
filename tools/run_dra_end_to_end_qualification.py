"""One-command replay of existing seven-system DRA qualification stages.

This orchestrates the already-qualified source aggregator and the protected
incremental candidate runner. It does not claim SWAP production admission.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tools.diagnose_dra_10242 import diagnose
from tools.run_dra_protected_population import run
from tools.review_dra_protected_population import review
from tools.prepare_dra_positive_median_dqsat import prepare
from tools.compare_dqsat_authority import read_ascii_grid
import pandas as pd


def execute(*,relation:Path,h1_mvg_zip:Path,remaining_zip:Path,
            schema:Path,dqsat_grid:Path,output_dir:Path,
            stage_start:str,stage_end:str,
            expected_h1_sha256:str,expected_remaining_sha256:str):
    output_dir.mkdir(parents=True,exist_ok=True)
    source_dir=output_dir/"source_diagnostic"
    median_table=prepare(
        pd.read_csv(schema,low_memory=False),
        pd.read_csv(relation,low_memory=False),
        read_ascii_grid(dqsat_grid),
    )
    median_path=output_dir/"positive_median_dqsat.csv"
    median_table.to_csv(median_path,index=False)
    diagnose(relation,h1_mvg_zip,remaining_zip,source_dir,
             stage_start=stage_start,stage_end=stage_end,
             dqsat_snapshot=median_path,
             expected_h1_mvg_sha256=expected_h1_sha256,
             expected_remaining_sha256=expected_remaining_sha256)
    physical_input=source_dir/"protected_physical_inputs.json"
    if not physical_input.is_file():
        raise RuntimeError("missing physical-input handoff from source diagnostic")
    candidate_dir=output_dir/"protected_candidates"
    candidate=run(physical_input,candidate_dir)
    source_review=review(source_dir/"protected_candidate_summary.csv")
    final={"schema_version":1,
           "status":"QUALIFICATION_CANDIDATE_PASS" if (
               candidate["failed_hru_count"]==0
               and source_review["failed_hru_count"]==0
               and candidate["hru_count"]==source_review["hru_count"]
           ) else "QUALIFICATION_CANDIDATE_FAIL",
           "hru_count":candidate["hru_count"],
           "protected_runner_failed_hru":candidate["failed_hru_count"],
           "source_diagnostic_failed_hru":source_review["failed_hru_count"],
           "production_admission":False}
    (output_dir/"replay_summary.json").write_text(
        json.dumps(final,indent=2)+"\n",encoding="utf-8")
    return final


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--relation",type=Path,required=True)
    p.add_argument("--h1-mvg-zip",type=Path,required=True)
    p.add_argument("--remaining-zip",type=Path,required=True)
    p.add_argument("--schema",type=Path,required=True)
    p.add_argument("--dqsat-grid",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--stage-start",required=True)
    p.add_argument("--stage-end",required=True)
    p.add_argument("--expected-h1-sha256",required=True)
    p.add_argument("--expected-remaining-sha256",required=True)
    a=p.parse_args()
    result=execute(
        relation=a.relation,h1_mvg_zip=a.h1_mvg_zip,
        remaining_zip=a.remaining_zip,schema=a.schema,
        dqsat_grid=a.dqsat_grid,output_dir=a.output_dir,
        stage_start=a.stage_start,stage_end=a.stage_end,
        expected_h1_sha256=a.expected_h1_sha256,
        expected_remaining_sha256=a.expected_remaining_sha256)
    print(json.dumps(result))
    return 0 if result["status"]=="QUALIFICATION_CANDIDATE_PASS" else 1
if __name__=="__main__":raise SystemExit(main())
