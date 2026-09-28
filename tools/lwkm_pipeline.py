#!/usr/bin/env python3
"""LWKM canonical workflow orchestrator."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path

STAGES=["A_SVAT","B_QUALIFICATION","C_HRU","D_HRU_QA","E_SWAP_MAPPING",
        "F_SWP_GENERATION","G_SWAP_RUN","H_HYDRO_EXTRACTION","I_ACCEPTANCE","J_ANIMO"]

IMPLEMENTATION={
 "A_SVAT":"EXECUTABLE","B_QUALIFICATION":"EXECUTABLE",
 "C_HRU":"PARTIAL","D_HRU_QA":"PARTIAL","E_SWAP_MAPPING":"PARTIAL",
 "F_SWP_GENERATION":"PARTIAL","G_SWAP_RUN":"SCAFFOLD","H_HYDRO_EXTRACTION":"SCAFFOLD",
 "I_ACCEPTANCE":"SCAFFOLD","J_ANIMO":"NOT_IMPLEMENTED",
}

def status()->dict:
    return {"schema_version":1,"stages":[{"stage":s,"implementation":IMPLEMENTATION[s]} for s in STAGES]}

def run_ab(input_csv:Path,out:Path)->None:
    cmd=[sys.executable,str(Path(__file__).with_name("build_canonical_svat.py")),str(input_csv),str(out)]
    subprocess.run(cmd,check=True)

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("status")
    plan=sub.add_parser("plan");plan.add_argument("--from-stage",choices=STAGES,default=STAGES[0])
    run=sub.add_parser("run-ab");run.add_argument("input_csv",type=Path);run.add_argument("output_dir",type=Path)
    a=p.parse_args()
    if a.command=="status":
        print(json.dumps(status(),indent=2));return
    if a.command=="plan":
        start=STAGES.index(a.from_stage)
        print(json.dumps({"plan":[{"stage":s,"implementation":IMPLEMENTATION[s]} for s in STAGES[start:]]},indent=2));return
    if a.command=="run-ab":
        run_ab(a.input_csv,a.output_dir);return

if __name__=="__main__":main()
