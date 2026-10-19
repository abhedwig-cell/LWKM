"""Five-component regression using existing archived products; no WEL/GHB derivation.

Cached GHB is the earlier one-day research product, NOT the server bdgghb series.
This replay tests software/algebra and preserves that historical limitation.
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.idf_reader import read_idf
from tools.modflow_daily_rasters import mosaic
from tools.groundwater_l1_boundary import aggregate
from tools.daily_forcing import effective_bbc
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def run(raw,previous,output):
    output.mkdir(parents=True,exist_ok=True)
    audit=json.loads((previous/'audit.json').read_text());sources=audit['sources']
    for s in sources:
        if sha256(Path(s['path']))!=s['sha256']:raise ValueError('archived source changed')
    for name in ['cell-components-RESEARCH.csv.gz','membership.csv.gz','hru-components-RESEARCH.csv']:
        if sha256(previous/name)!=audit['outputs'][name]:raise ValueError('cached research identity changed')
    ref=read_idf(next(raw.glob('*head_next_midnight*')))
    m=pd.read_csv(previous/'membership.csv.gz');cells=pd.read_csv(previous/'cell-components-RESEARCH.csv.gz')
    for role,axis in [('frf',1),('fff',0)]:
        a=mosaic([Path(s['path']) for s in sources if s['role'].startswith('bdg'+role)],ref)
        prev=np.zeros_like(a)
        if axis==1:prev[:,1:]=a[:,:-1]
        else:prev[1:]=a[:-1]
        # Exact existing C# authority, not a new sign hypothesis.
        cells[role]=(a-prev)[m.row.to_numpy(int),m.col.to_numpy(int)]
    comparable=np.isfinite(cells.lat)&np.isfinite(cells.frf)&np.isfinite(cells.fff)
    max_difference=float(np.max(abs(cells.loc[comparable,'lat']-(cells.loc[comparable,'frf']+cells.loc[comparable,'fff']))))
    good=np.isfinite(cells[['flf','frf','fff','ghb','wel']]).all(axis=1)
    coverage=m.assign(known=good).groupby('hru_id').agg(cells=('cell_id','size'),known=('known','sum'))
    ids=coverage.index[coverage.cells==coverage.known];members=m[m.hru_id.isin(ids)]
    selected=cells[cells.cell_id.isin(members.cell_id)].copy();selected.lat=selected.frf+selected.fff
    h=aggregate(selected,members[['hru_id','cell_id','area_m2']],start='2020-07-01',end='2020-07-01')
    joined=selected.merge(members[['hru_id','cell_id']],on='cell_id',validate='one_to_one')
    for role in ['frf','fff']:
        h[role+'_net_m3_d']=h.hru_id.map(joined.groupby('hru_id')[role].sum())
        h[role+'_mm_d']=1000*h[role+'_net_m3_d']/h.area_m2
    h.to_csv(output/'hru-five-components.csv',index=False,float_format='%.12g');coverage.to_csv(output/'coverage.csv')
    for hid,g in h.groupby('hru_id'):(output/f'{hid}.bbc').write_text(effective_bbc(g,start='2020-07-01',end='2020-07-01'))
    r=dict(population=len(coverage),complete_research_hrus=len(h),represented_cells=len(m),compared_lateral_cells=int(comparable.sum()),max_cached_lateral_difference_m3_d=max_difference,new_wel_ghb_reconstruction=False,operational_server_series_consumed=False,production_admitted=False,limitations=['Cached prior research GHB, not the current server bdgghb daily product','One-day software regression; no complete modern MET pair'],inputs={str(p):sha256(p) for p in [previous/'audit.json',previous/'cell-components-RESEARCH.csv.gz',previous/'membership.csv.gz']},outputs={p.name:sha256(p) for p in output.iterdir() if p.is_file() and p.name!='summary.json'})
    atomic_json(output/'summary.json',r);return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['raw','previous','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.raw,a.previous,a.output)))
