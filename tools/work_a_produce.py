"""Source-bound one-day forcing diagnostics, explicitly research-only."""
import argparse,json
from pathlib import Path
import pandas as pd
from tools.daily_forcing import MET_COLUMNS,modern_met,effective_bbc
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def produce(snapshot,oracles,output):
    output.mkdir(parents=True,exist_ok=True);rows=[];canonical=[]
    hru=pd.read_csv(snapshot/'hru-components-RESEARCH.csv')
    for hid,g in hru.groupby('hru_id'):
        p=output/f'{hid}.bbc';p.write_text(effective_bbc(g,start='2020-07-01',end='2020-07-01'))
        rows.append(dict(hru=int(hid),kind='BBC',sha256=sha256(p),source_sha256=sha256(snapshot/'hru-components-RESEARCH.csv'),
            qualification='RESEARCH_ESTIMATED_WEL_DERIVED_GHB_UNRESOLVED_SIGNS',production_admitted=False))
    for path in sorted(oracles.glob('*/*.met')):
        hid=int(path.stem);f=pd.read_csv(path,sep=r'\s+',skiprows=1,header=None,quotechar="'")
        d=f[(f[1]==1)&(f[2]==7)&(f[3]==2020)]
        if len(d)!=1:raise ValueError('historical station date missing/duplicate')
        a=d.iloc[0];frame=pd.DataFrame([dict(date='2020-07-01',**dict(zip(MET_COLUMNS,a.iloc[4:].astype(float))))])
        canonical.append(frame.assign(hru_id=hid))
        p=output/f'{hid}.met';p.write_text(modern_met(frame,start='2020-07-01',end='2020-07-01',station=int(float(str(a.iloc[0]).strip("'")))))
        rows.append(dict(hru=hid,kind='MET',sha256=sha256(p),source_sha256=sha256(path),
            qualification='EXPLICIT_HISTORICAL_MET_SOURCE_REPLAY_NOT_MODERN_SERVER_MET',production_admitted=False))
    pd.concat(canonical,ignore_index=True).to_csv(output/'canonical-weather-RESEARCH.csv',index=False)
    atomic_json(output/'manifest.json',dict(files=rows,modern_production_packages=0,production_admitted=False,code_sha256=sha256(Path(__file__)),snapshot_audit_sha256=sha256(snapshot/'audit.json')));print(len(rows));return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['snapshot','oracles','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();produce(a.snapshot,a.oracles,a.output)
