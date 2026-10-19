"""Resolve exact observed native paths; never invent GHB/WEL output locations."""
import argparse,json
from pathlib import Path
import pandas as pd
from tools.run_dra_protected_population import atomic_json


def make(manifest,controls,output):
    frame=pd.read_csv(manifest,encoding='utf-8-sig');items=[]
    for row in frame.itertuples(index=False):
        if row.Status!='FOUND':continue
        items.append(dict(logical_id=row.Component,path=row.Source,role=row.Component,date='2020-07-01',layer=1,
            package=row.Component.split('_')[0],units='SOURCE_UNITS_REQUIRE_ORIGINAL_BUDGET_CONFIRMATION',consumer='GW_L1_AND_BALANCE_QA',
            semantics_evidence='Original collected manifest; verify LIST/INI and time semantics; bdgwel is an estimate',sha256=row.SHA256.lower()))
    atomic_json(output,dict(schema_version=1,items=items,controls=[dict(path=str(p.resolve())) for p in controls],
        unresolved_requirements=['Original layer1 WEL budget, not estimated bdgwel','Original layer1 GHB daily budget and activity masks','Meteorological INI bindings and complete daily variables','Original LIST units/sign/time verification']))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--control',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();make(a.manifest,a.control,a.output)
