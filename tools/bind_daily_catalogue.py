"""Replace forcing in C2 asset catalogues; never inherit an old MET/BBC fallback."""
import argparse,json
from pathlib import Path
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def bind(base,pairs,output):
    old=json.loads(base.read_text());new=json.loads(pairs.read_text());runs={};statuses=[]
    for row in new['runs']:
        hid=str(row['hru_id']);entry=old['runs'].get(hid)
        if row['status']!='FORCING_PAIR_CANDIDATE':statuses.append(dict(hru_id=int(hid),status='BLOCKED_DAILY_FORCING'));continue
        if entry is None:statuses.append(dict(hru_id=int(hid),status='BLOCKED_NONFORCING_ASSETS'));continue
        assets={n:m for n,m in entry['assets'].items() if Path(n).suffix.lower() not in ['.bbc','.met']}
        for n,m in row['assets'].items():
            if Path(n).suffix.lower() not in ['.bbc','.met']:raise ValueError('unexpected forcing asset type')
            assets[n]={k:v for k,v in m.items() if k!='reused'}
        if {n for n in assets if Path(n).suffix.lower() in ['.bbc','.met']}!={hid+'.bbc',hid+'.met'}:raise ValueError('forcing reference identity mismatch')
        runs[hid]=dict(assets=assets);statuses.append(dict(hru_id=int(hid),status='CATALOGUE_CANDIDATE_READY'))
    catalogue={**old,'profile_id':'LWKM_WORK_A_DAILY_CANDIDATE','runs':runs}
    # The consumer period belongs to the daily input manifest, not the old C2 run.
    if not new.get('start') or not new.get('end'):raise ValueError('daily forcing period missing')
    catalogue.update(start=new['start'],end=new['end'])
    atomic_json(output,catalogue);atomic_json(output.with_suffix('.audit.json'),dict(base_sha256=sha256(base),pairs_sha256=sha256(pairs),bound=len(runs),runs=statuses,production_admitted=False));return catalogue

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['base','pairs','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(len(bind(a.base,a.pairs,a.output)['runs']))
