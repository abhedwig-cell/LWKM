"""Bind archived five-component research fixture to the operational processor.

Re-encodes an existing cached GHB product; never recalculates GHB or WEL.
Not a replacement for collecting the owner's existing server bdgghb products.
"""
import argparse,json,struct
from pathlib import Path
import numpy as np
import pandas as pd
from tools.idf_reader import read_idf
from tools.process_daily_budget_plan import process
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def run(snapshot,authority,output):
    output.mkdir(parents=True,exist_ok=True)
    a=json.loads((snapshot/'audit.json').read_text())
    def binding(p):return dict(path=str(p.resolve()),sha256=sha256(p))
    for name in ['cell-components-RESEARCH.csv.gz','membership.csv.gz','hru-components-RESEARCH.csv']:
        if sha256(snapshot/name)!=a['outputs'][name]:raise ValueError('cached identity changed')
    m=pd.read_csv(snapshot/'membership.csv.gz');cells=pd.read_csv(snapshot/'cell-components-RESEARCH.csv.gz')
    ids=pd.read_csv(snapshot/'hru-components-RESEARCH.csv').hru_id
    selected=m[m.hru_id.isin(ids)];selected.to_csv(output/'membership.csv',index=False)
    head=read_idf(next(Path(a['sources'][0]['path']).parent.glob('*head_next_midnight*')))
    def raster(name,values):
        p=output/(name+'.idf');v=np.asarray(values,dtype='<f4');valid=v[v!=-9999]
        header=struct.pack('<3i10f',1271,head.ncol,head.nrow,head.xmin,head.xmax,head.ymin,head.ymax,float(valid.min()),float(valid.max()),-9999,0,head.dx,head.dy)
        p.write_bytes(header+v.tobytes());return binding(p)
    ghb=np.full(head.values.shape,-9999,dtype=float)
    valid=np.isfinite(cells.ghb);ghb[m.loc[valid,'row'],m.loc[valid,'col']]=cells.loc[valid,'ghb']
    ghb_binding=raster('cached-ghb-reencoded-not-new-reconstruction',ghb)
    mask=np.full(head.values.shape,-9999,dtype=float);mask[selected.row,selected.col]=1
    active=raster('selected-membership-support',mask)
    evidence=binding(authority)
    components={}
    for role in ['flf','frf','fff','wel']:
        parts=[dict(path=s['path'],sha256=s['sha256']) for s in a['sources'] if s['role'].startswith('bdg'+role)]
        operation={'frf':'SAVED_CURRENT_MINUS_PREVIOUS_COLUMN','fff':'SAVED_CURRENT_MINUS_PREVIOUS_ROW'}.get(role,'CELL_NET')
        components[role]=[dict(layer=1,positive_multiplier=1,spatial_operation=operation,partitions=parts)]
    components['ghb']=[dict(layer=1,positive_multiplier=1,partitions=[ghb_binding])]
    contract=dict(grid=active,model_activity_mask=active,membership=binding(output/'membership.csv'),layer=1,units='m3/day_rate',start='2020-07-01',end='2020-07-01',wel_provenance='RECONSTRUCTED_OPERATIONAL',ghb_provenance='RECONSTRUCTED_OPERATIONAL',reconstructed_products={r:dict(method='Existing archived research product; reuse only',limitations=['Historical one-day research product, not current server daily series','GHB cached prior end-head product; do not substitute for same-day server reconstruction'],evidence=binding(snapshot/'audit.json')) for r in ['wel','ghb']},intervals=[dict(start='2020-07-01',end='2020-07-02',components=components)])
    contract.update({k:evidence for k in ['signs_evidence','units_evidence','time_evidence','package_coverage_evidence']})
    atomic_json(output/'plan.json',contract)
    first=process(output/'plan.json',output/'daily');second=process(output/'plan.json',output/'daily')
    atomic_json(output/'reuse-proof.json',dict(files_reused=all(f['reused'] for d in second['days'] for f in d['files'].values()),production_admitted=False))
    return first

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['snapshot','authority','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();r=run(a.snapshot,a.authority,a.output);print(len(r['days']))
