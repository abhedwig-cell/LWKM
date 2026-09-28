"""Scientific QA for canonical HRU products."""
from __future__ import annotations
import numpy as np
import pandas as pd

def weighted_stats(error:pd.Series,weight:pd.Series)->dict:
    e=pd.to_numeric(error,errors="coerce").to_numpy(float)
    w=pd.to_numeric(weight,errors="coerce").to_numpy(float)
    ok=np.isfinite(e)&np.isfinite(w)&(w>0);e=e[ok];w=w[ok]
    if not len(e):return {"n":0}
    order=np.argsort(np.abs(e));ae=np.abs(e)[order];cw=np.cumsum(w[order])/w.sum()
    def wp(p):return float(ae[min(np.searchsorted(cw,p),len(ae)-1)])
    return {"n":int(len(e)),"area":float(w.sum()),"bias":float(np.average(e,weights=w)),
            "mae":float(np.average(np.abs(e),weights=w)),
            "rmse":float(np.sqrt(np.average(e*e,weights=w))),
            "p50_abs":wp(.5),"p90_abs":wp(.9),"p95_abs":wp(.95),"max_abs":float(np.max(np.abs(e)))}

def purity(df:pd.DataFrame,source:str,representative:str,weight="area_m2")->float:
    ok=df[source].notna()&df[representative].notna()
    if not ok.any():return np.nan
    w=pd.to_numeric(df.loc[ok,weight],errors="coerce").fillna(0)
    same=df.loc[ok,source].eq(df.loc[ok,representative]).astype(float)
    return float(np.average(same,weights=w)*100) if w.sum()>0 else float(same.mean()*100)

def route_summary(membership:pd.DataFrame,weight="area_m2")->pd.DataFrame:
    x=membership.copy();x[weight]=pd.to_numeric(x[weight],errors="coerce").fillna(0)
    g=x.groupby("assignment_route",dropna=False).agg(svats=("svat","size"),area_m2=(weight,"sum"),hrus=("HRU","nunique")).reset_index()
    g["svat_fraction"]=g["svats"]/len(x);g["area_fraction"]=g["area_m2"]/x[weight].sum()
    return g

def regional_backprojection(df:pd.DataFrame,*,region="LDGBclus",weight="area_m2",
                            specs=(("GHG","GHG_LHM43_orig","GHG_average"),("NettoKwel","NettoKwel_LHM43_orig","NettoKwel_average")))->pd.DataFrame:
    rows=[]
    for reg,g in df.groupby(region,dropna=False):
        for name,src,avg in specs:
            s=weighted_stats(g[avg]-g[src],g[weight]);s.update({region:reg,"variable":name});rows.append(s)
    return pd.DataFrame(rows)

def admission_summary(membership:pd.DataFrame,hru_schema:pd.DataFrame)->dict:
    return {"svats":int(membership["svat"].nunique()),"hrus":int(membership["HRU"].nunique()),
            "nrus":int(membership["NRU"].nunique()) if "NRU" in membership else None,
            "routes":membership["assignment_route"].value_counts(dropna=False).to_dict(),
            "representatives":int(hru_schema["hru_representative_svat"].notna().sum()) if "hru_representative_svat" in hru_schema else 0}
