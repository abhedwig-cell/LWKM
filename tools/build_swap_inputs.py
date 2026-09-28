#!/usr/bin/env python3
"""Build canonical compatibility inputs replacing HRUlist2SWAP v0.38 outputs."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from tools.swap_mapping import map_hru_members,case_dependency_record
from tools.swap_runs_contract import build_runs_row,validate_runs_row,RUN_COLUMNS
from tools.swap_v038_providers import historical_pre_override,apply_representative_historical,lookup_ids,metfil
from tools.swap_runs_providers import control_providers,member_providers
from tools.generate_bbc import render_bbc
from tools.generate_dra import aggregate_system,repair_system,render_dra

def build_static_case(members,representative,control,lookups):
    mapped=map_hru_members(members,None,irrigation_threshold=.37)
    pre=historical_pre_override(members);mapped.update(pre)
    mapped=apply_representative_historical(mapped,representative,members)
    mapped.update(lookup_ids(mapped,*lookups))
    mapped["METFIL"]=metfil(mapped["HRU"])
    providers={**control_providers(control),**member_providers(members)}
    # Time-dependent and externally aggregated fields remain explicit inputs.
    return mapped,providers

def main():
    p=argparse.ArgumentParser()
    p.add_argument("members_csv",type=Path);p.add_argument("representatives_csv",type=Path)
    p.add_argument("output_dir",type=Path);p.add_argument("--control-json",type=Path,required=True)
    p.add_argument("--lookups-json",type=Path,required=True);p.add_argument("--dynamic-json",type=Path,required=True)
    a=p.parse_args()
    members=pd.read_csv(a.members_csv);reps=pd.read_csv(a.representatives_csv).set_index("HRU")
    control=json.loads(a.control_json.read_text());raw=json.loads(a.lookups_json.read_text())
    b2b={int(k):v for k,v in raw["bodem2bofek"].items()}
    l2c={tuple(map(int,k.split(","))):v for k,v in raw["lu2crop"].items()}
    l2o={tuple(map(int,k.split(","))):v for k,v in raw["lu2croporg"].items()}
    dynamic=json.loads(a.dynamic_json.read_text())
    out=a.output_dir; (out/"bbc").mkdir(parents=True,exist_ok=True);(out/"dra").mkdir(exist_ok=True);(out/"met").mkdir(exist_ok=True)
    rows=[];deps=[]
    for h,g in members.groupby("HRU",sort=True):
        rep=reps.loc[int(h)].to_dict() if int(h) in reps.index else None
        mapped,providers=build_static_case(g,rep,control,(b2b,l2c,l2o))
        dyn=dynamic.get(str(int(h)))
        if dyn is None:raise ValueError(f"Missing dynamic provider payload for HRU {h}")
        providers.update({k:(lambda m,v=v:v) for k,v in dyn["runs_fields"].items()})
        row=build_runs_row(mapped,providers);validate_runs_row(row);rows.append(row)
        if "bbc_text" not in dyn or "met_text" not in dyn:raise ValueError(f"Missing BBC/MET payload for HRU {h}")
        (out/"bbc"/f"{int(h)}.bbc").write_text(dyn["bbc_text"])
        (out/"met"/f"{int(h)}.met").write_text(dyn["met_text"])
        systems=[repair_system(aggregate_system(g,sy,mapped["dqsat"]),sy,bool(dyn.get("isnatuur",False))) for sy in range(1,6)]
        dra=render_dra(systems,int(dyn["n_horizons"]),int(control["year_start"]),int(control["year_end"]),float(dyn["infil_avg"]))
        (out/"dra"/f"{int(h)}.dra").write_text(dra)
        deps.append(case_dependency_record(row,mapping_version="HRU10242_V038",swap_version=str(control["swap_version"]),
                    meteo_ref=dyn["meteo_ref"],boundary_ref=dyn["boundary_ref"],soil_ref=dyn["soil_ref"],crop_ref=dyn["crop_ref"]))
    pd.DataFrame(rows,columns=RUN_COLUMNS).to_csv(out/"Runs.csv",index=False)
    (out/"dependencies.json").write_text(json.dumps(deps,indent=2))
    (out/"manifest.json").write_text(json.dumps({"profile":"HRU10242_V038","cases":len(rows),"complete":True},indent=2))
if __name__=="__main__":main()
