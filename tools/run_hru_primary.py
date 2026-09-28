#!/usr/bin/env python3
"""Run canonical HRU clustering control-flow with historical R/scclust backend."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from tools.hru_clustering import run_round
from tools.hru_partitioners import RScclustPartitioner

ROUNDS=[
["LDGBclus","lu2","lu4","lu7","grondsoort2","grondsoort4","pawn21","bodem370","Gt_LHM43","kwelklasse4","isdrain"],
["LDGBclus","lu2","lu4","lu7","grondsoort2","grondsoort4","pawn21","bodem370","Gt_LHM43","kwelklasse4"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","pawn21","bodem370","Gt_LHM43","kwelklasse4"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","pawn21","Gt_LHM43","kwelklasse4"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","Gt_LHM43","kwelklasse4"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","pawn21","Gt_LHM43"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","Gt_LHM43"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","pawn21","kwelklasse4"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","kwelklasse4"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4","pawn21"],
["LDGBclus","lu2","lu4","grondsoort2","grondsoort4"]]

def run(df,partitioner):
    rem=df.copy(); accepted=[]; diags=[]
    for no,cols in enumerate(ROUNDS,1):
        a,rem,q=run_round(rem,cols,partitioner,round_no=no)
        if len(a):accepted.append(a)
        if len(q):diags.append(q)
    return (pd.concat(accepted) if accepted else df.iloc[0:0].copy(),
            rem,pd.concat(diags,ignore_index=True) if diags else pd.DataFrame())

def main():
    p=argparse.ArgumentParser();p.add_argument("input_csv",type=Path);p.add_argument("output_dir",type=Path)
    p.add_argument("--rscript",default="Rscript");a=p.parse_args()
    df=pd.read_csv(a.input_csv)
    if "Oppha" not in df:df["Oppha"]=6.25
    accepted,rem,diag=run(df,RScclustPartitioner(a.rscript))
    a.output_dir.mkdir(parents=True,exist_ok=True)
    accepted.to_csv(a.output_dir/"primary_clusters.csv",index=False)
    rem.to_csv(a.output_dir/"primary_remainder.csv",index=False)
    diag.to_csv(a.output_dir/"round_diagnostics.csv",index=False)
    (a.output_dir/"manifest.json").write_text(json.dumps({"accepted_svats":len(accepted),"remainder_svats":len(rem)},indent=2))
if __name__=="__main__":main()
