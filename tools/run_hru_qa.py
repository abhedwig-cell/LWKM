#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from tools.hru_qa import route_summary,regional_backprojection,admission_summary

def main():
    p=argparse.ArgumentParser();p.add_argument("membership",type=Path);p.add_argument("hru_schema",type=Path);p.add_argument("output_dir",type=Path)
    a=p.parse_args();m=pd.read_csv(a.membership);h=pd.read_csv(a.hru_schema);a.output_dir.mkdir(parents=True,exist_ok=True)
    route_summary(m).to_csv(a.output_dir/"route_summary.csv",index=False)
    if {"LDGBclus","GHG_LHM43_orig","GHG_average","NettoKwel_LHM43_orig","NettoKwel_average","area_m2"}.issubset(m.columns):
        regional_backprojection(m).to_csv(a.output_dir/"regional_backprojection.csv",index=False)
    summary=admission_summary(m,h)
    (a.output_dir/"hru_qa_summary.json").write_text(json.dumps(summary,indent=2,default=str))
if __name__=="__main__":main()
