"""Geometry-safe mosaics and oriented face divergence. Unknown cells stay NaN."""
import numpy as np
from tools.idf_reader import read_idf


def mosaic(paths,reference):
    result=np.full(reference.values.shape,np.nan)
    for path in paths:
        g=read_idf(path)
        if g.dx!=reference.dx or g.dy!=reference.dy:raise ValueError('resolution mismatch')
        c=(g.xmin-reference.xmin)/g.dx;r=(reference.ymax-g.ymax)/g.dy
        if abs(c-round(c))>1e-6 or abs(r-round(r))>1e-6:raise ValueError('grid misalignment')
        c,r=int(round(c)),int(round(r))
        if min(c,r)<0 or c+g.ncol>reference.ncol or r+g.nrow>reference.nrow:raise ValueError('partition outside grid')
        view=result[r:r+g.nrow,c:c+g.ncol];valid=np.isfinite(g.values)&(g.values!=g.nodata)
        if (np.isfinite(view)&valid).any():raise ValueError('overlapping valid partition cells')
        view[valid]=g.values[valid]
    return result


def into_cell_from_faces(right,front):
    if right.shape!=front.shape:raise ValueError('face geometries differ')
    # Faces beyond the model's left/top outer edge do not exist; package fluxes
    # carry boundary exchange. Missing interior face data remain missing.
    left=np.zeros_like(right);up=np.zeros_like(front)
    left[:,1:]=right[:,:-1];up[1:]=front[:-1]
    return left-right+up-front


def integrate_intervals(intervals,*,start,end):
    """Full half-open calendar days, constant m3/day rates, no gaps/overlap."""
    import pandas as pd
    lo=pd.Timestamp(start);hi=pd.Timestamp(end)+pd.Timedelta(days=1)
    cursor=lo;out={d.date().isoformat():None for d in pd.date_range(lo,hi-pd.Timedelta(days=1))}
    for a,b,rate in intervals:
        a,b=pd.Timestamp(a),pd.Timestamp(b)
        if a!=cursor or b<=a or b>hi:raise ValueError('interval coverage gap/overlap/order')
        if not np.isfinite(rate).all():raise ValueError('nonfinite interval rate')
        while a<b:
            edge=min(b,a.normalize()+pd.Timedelta(days=1));day=a.date().isoformat()
            value=np.asarray(rate,dtype=float)*(edge-a).total_seconds()/86400.
            out[day]=value if out[day] is None else out[day]+value;a=edge
        cursor=b
    if cursor!=hi or any(x is None for x in out.values()):raise ValueError('incomplete interval coverage')
    return out
