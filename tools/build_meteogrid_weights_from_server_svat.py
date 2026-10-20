"""Produce fixed HRU/grid weights from original SVAT HRU CSV + area_svat.inp.

Inputs are explicit, no donor-area substitution. Output is a CANDIDATE until
area-source discrepancies against the qualified Work B snapshot are resolved.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def run(membership, areas, template, output, *, expected_hrus=10242, expected_svats=427656):
    s=pd.read_csv(membership,usecols=['svat_orig','HRU','x','y'])
    a=pd.read_csv(areas,sep=r'\s+',header=None,usecols=[0,1],names=['svat_orig','area_m2'])
    if s.svat_orig.duplicated().any() or a.svat_orig.duplicated().any():
        raise ValueError('Duplicate SVAT ID')
    s=s.merge(a,on='svat_orig',how='left',validate='one_to_one')
    if s.area_m2.isna().any() or len(s)!=expected_svats or s.HRU.nunique()!=expected_hrus:
        raise ValueError('Missing areas or unexpected population')
    if not np.isfinite(s[['x','y','area_m2']].to_numpy(float)).all() or (s.area_m2<=0).any():
        raise ValueError('Invalid source coordinates or area')
    g={}
    with open(template,encoding='utf-8') as f:
        for _ in range(6):
            k,v=f.readline().split();g[k.lower()]=float(v)
    if set(g)!={'ncols','nrows','xllcorner','yllcorner','cellsize','nodata_value'}:
        raise ValueError('Unsupported raster header')
    nc,nr=int(g['ncols']),int(g['nrows'])
    col=np.floor((s.x.to_numpy()-g['xllcorner'])/g['cellsize']).astype(int)
    row=nr-1-np.floor((s.y.to_numpy()-g['yllcorner'])/g['cellsize']).astype(int)
    if ((col<0)|(col>=nc)|(row<0)|(row>=nr)).any():
        raise ValueError('SVAT outside grid')
    s['grid_id']=row*nc+col
    w=s.groupby(['HRU','grid_id'],as_index=False,sort=True).area_m2.sum()
    w['weight']=w.area_m2/w.groupby('HRU').area_m2.transform('sum')
    if not np.allclose(w.groupby('HRU').weight.sum(),1,rtol=0,atol=1e-12):
        raise ValueError('Invalid total weight')
    output.mkdir(parents=True,exist_ok=True)
    w.rename(columns={'HRU':'hru_id'}).to_csv(output/'hru_meteogrid_weights.csv',index=False,float_format='%.15g')
    report={'schema_version':1,'status':'CANDIDATE_PENDING_AREA_PROVENANCE_RECONCILIATION',
            'svats':len(s),'hrus':int(s.HRU.nunique()),'grid_links':len(w),
            'area_m2':float(s.area_m2.sum()),'geometry':g,
            'input_sha256':{p.name:sha(p) for p in [membership,areas,template]},
            'output_sha256':sha(output/'hru_meteogrid_weights.csv')}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('membership','areas','template','output'):
        p.add_argument('--'+key,type=Path,required=True)
    v=p.parse_args()
    print(json.dumps(run(v.membership,v.areas,v.template,v.output),indent=2))
