"""Fixed HRU weights by grid cell, with nearest-valid daily raster sampling."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def header(path):
    result={}
    with open(path,encoding='utf-8') as f:
        for _ in range(6):
            key,value=f.readline().split()
            result[key.lower()]=float(value)
    if set(result)!={'ncols','nrows','xllcorner','yllcorner','cellsize','nodata_value'}:
        raise ValueError('unsupported grid header')
    return result

def cells(members,h):
    for k in ['hru_id','svat_id','x_rd','y_rd','area_m2']:
        if k not in members:raise ValueError('missing membership field '+k)
    if members.svat_id.duplicated().any():raise ValueError('duplicate SVAT')
    v=members[['x_rd','y_rd','area_m2']].to_numpy(float)
    if not np.isfinite(v).all() or (members.area_m2<=0).any():raise ValueError('invalid SVAT geometry/area')
    nr,nc=int(h['nrows']),int(h['ncols'])
    col=np.floor((members.x_rd.to_numpy()-h['xllcorner'])/h['cellsize']).astype(int)
    row=nr-1-np.floor((members.y_rd.to_numpy()-h['yllcorner'])/h['cellsize']).astype(int)
    if ((col<0)|(col>=nc)|(row<0)|(row>=nr)).any():raise ValueError('SVAT outside raster')
    data=members[['hru_id','area_m2']].copy()
    data['grid_id']=row*nc+col
    grouped=data.groupby(['hru_id','grid_id'],as_index=False).area_m2.sum()
    grouped['weight']=grouped.area_m2/grouped.groupby('hru_id').area_m2.transform('sum')
    if not np.allclose(grouped.groupby('hru_id').weight.sum().to_numpy(),1,atol=1e-12,rtol=0):
        raise ValueError('weights not normalized')
    return grouped.sort_values(['hru_id','grid_id']).reset_index(drop=True)

def aggregate_grid(weights,values,geom):
    valid=np.isfinite(values)&(values!=geom['nodata_value'])
    if not valid.any():raise ValueError('no valid meteorological cell')
    if valid.all():filled=values
    else:
        _,ix=distance_transform_edt(~valid,return_indices=True)
        filled=values[tuple(ix)]
    ids=weights.grid_id.to_numpy(dtype=int)
    data=weights[['hru_id','weight']].copy()
    data['part']=filled.ravel()[ids]*weights.weight.to_numpy()
    return data.groupby('hru_id',sort=True).part.sum().reset_index(name='value')
