"""Independent boundary-only lateral cancellation check on the real snapshot."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.idf_reader import read_idf
from tools.modflow_daily_rasters import mosaic
from tools.run_dra_protected_population import atomic_json


def check(root,snapshot,output):
    grid=read_idf(next(root.glob('*head_next_midnight*')))
    r=mosaic(sorted(root.glob('bdgfrf*')),grid);f=mosaic(sorted(root.glob('bdgfff*')),grid)
    membership=pd.read_csv(snapshot/'membership.csv.gz');results=pd.read_csv(snapshot/'hru-components-RESEARCH.csv');rows=[]
    for rec in results.itertuples(index=False):
        members=membership[membership.hru_id==rec.hru_id]
        mask=np.zeros(grid.values.shape,dtype=bool);mask[members.row.to_numpy(int),members.col.to_numpy(int)]=True
        east=np.zeros_like(mask);east[:,:-1]=mask[:,1:]
        south=np.zeros_like(mask);south[:-1]=mask[1:]
        total=0.
        for face,nextmask in [(r,east),(f,south)]:
            outward=face[mask&~nextmask];inward=face[~mask&nextmask]
            if not np.isfinite(outward).all() or not np.isfinite(inward).all():raise ValueError('unknown selected boundary face')
            total+=outward.sum()-inward.sum()
        rows.append(dict(hru_id=int(rec.hru_id),cell_sum_m3_d=float(rec.lat_net_m3_d),boundary_only_m3_d=float(total),difference_m3_d=float(total-rec.lat_net_m3_d)))
    max_error=max(abs(r['difference_m3_d']) for r in rows)
    if max_error>1e-7:raise ValueError('internal-face cancellation mismatch')
    audit=dict(rows=rows,maximum_difference_m3_d=max_error,production_admitted=False,tolerance_m3_d=1e-7)
    atomic_json(output,audit);print(json.dumps(audit));return audit

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['root','snapshot','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();check(a.root,a.snapshot,a.output)
