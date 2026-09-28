"""Canonical HRU helper algorithms.

These functions implement source-bound post-clustering semantics independently
of file layout: weighted donor matching, medoid representative selection and
SVAT-level backprojection QA.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

DEFAULT_WEIGHTS_R1={
 "grondsoort2":250.0,"grondsoort4":100.0,"pawn21_rank":10.0,
 "Gt_LHM43":0.5,"kwelklasse4":0.5,"GHG_LHM43":0.01,"NettoKwel_LHM43":0.01,
}
DEFAULT_WEIGHTS_R2={**DEFAULT_WEIGHTS_R1,"codelu4":250.0}

def weighted_squared_euclidean_matrix(targets:pd.DataFrame, donors:pd.DataFrame, weights:dict[str,float])->np.ndarray:
    """Squared weighted Euclidean distance; same NN ordering as RANN::nn2 after sqrt(weight) scaling."""
    cols=list(weights)
    t=targets[cols].astype(float).to_numpy()
    d=donors[cols].astype(float).to_numpy()
    scale=np.sqrt(np.array([weights[c] for c in cols],dtype=float))
    t=t*scale; d=d*scale
    return ((t[:,None,:]-d[None,:,:])**2).sum(axis=2)

def nearest_donors(targets:pd.DataFrame, donors:pd.DataFrame, weights:dict[str,float], donor_id:str="svat")->pd.Series:
    if donors.empty: raise ValueError("No donors")
    dist=weighted_squared_euclidean_matrix(targets,donors,weights)
    idx=np.argmin(dist,axis=1)
    return pd.Series(donors.iloc[idx][donor_id].to_numpy(),index=targets.index,name="hru_cluster_donor_svat")

def medoid_existing_svat(group:pd.DataFrame, variables=("GHG_LHM43","NettoKwel_LHM43"),id_col="svat")->int:
    """Historical representative_points(method='medoid'): real row with minimum mean Euclidean distance."""
    if group.empty: raise ValueError("Empty HRU")
    x=group[list(variables)].astype(float).to_numpy()
    dist=np.sqrt(((x[:,None,:]-x[None,:,:])**2).sum(axis=2))
    return int(group.iloc[int(np.argmin(dist.mean(axis=1)))][id_col])

def robust_iqr_scale(values):
    """Historical robust_scalar: (x-median)/IQR, zeros when IQR is zero/NA."""
    x=np.asarray(values,dtype=float); med=np.nanmedian(x)
    q25,q75=np.nanpercentile(x,[25,75]);iqr=q75-q25
    if not np.isfinite(iqr) or iqr==0:return np.zeros_like(x)
    return (x-med)/iqr

def backprojection_metrics(members:pd.DataFrame,hru_values:pd.DataFrame,*,hru_col="HRU",area_col="area_m2",
                           specs=(("GHG","GHG_LHM43_orig","GHG_average"),
                                  ("NettoKwel","NettoKwel_LHM43_orig","NettoKwel_average")))->pd.DataFrame:
    x=members.merge(hru_values,on=hru_col,how="left",validate="many_to_one")
    w=pd.to_numeric(x[area_col],errors="coerce").to_numpy(float)
    rows=[]
    for name,svat_col,hru_avg_col in specs:
        a=pd.to_numeric(x[svat_col],errors="coerce").to_numpy(float)
        b=pd.to_numeric(x[hru_avg_col],errors="coerce").to_numpy(float)
        ok=np.isfinite(a)&np.isfinite(b)&np.isfinite(w)&(w>0)
        e=b[ok]-a[ok]; ww=w[ok]
        rows.append({"variable":name,"n":int(ok.sum()),"area_m2":float(ww.sum()),
                     "bias":float(np.average(e,weights=ww)),
                     "mae":float(np.average(np.abs(e),weights=ww)),
                     "rmse":float(np.sqrt(np.average(e*e,weights=ww))),
                     "max_abs":float(np.max(np.abs(e))) if len(e) else np.nan})
    return pd.DataFrame(rows)
