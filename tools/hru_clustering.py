"""Generic staged HRU clustering scaffolding.

The round schedule is configuration. Exact scclust equivalence is a regression
requirement; this module provides source-bound grouping, robust scaling,
quality metrics and staged remainder semantics.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

def robust_scale(s:pd.Series)->np.ndarray:
    x=pd.to_numeric(s,errors="coerce").to_numpy(float)
    med=np.nanmedian(x); q1=np.nanquantile(x,.25); q3=np.nanquantile(x,.75); iqr=q3-q1
    if not np.isfinite(iqr) or iqr==0: return np.zeros(len(x))
    return (x-med)/iqr

def corrected_skew(x)->float:
    x=np.asarray(x,dtype=float); x=x[np.isfinite(x)]; n=len(x)
    if n<=2:return 0.0
    sd=x.std(ddof=1)
    if sd==0:return 0.0
    return float(n/((n-1)*(n-2))*np.sum(((x-x.mean())/sd)**3))

def cluster_quality(g:pd.DataFrame, ghg="GHG_LHM43", nkw="NettoKwel_LHM43")->dict:
    out={}
    for name,col in [("GHG",ghg),("NettoKwel",nkw)]:
        x=pd.to_numeric(g[col],errors="coerce").dropna().to_numpy(float)
        center=float(np.mean(x)) if len(x) else np.nan
        e=np.abs(x-center)
        out[f"mae_{name}"]=float(e.mean()) if len(e) else np.nan
        out[f"skew_{name}"]=corrected_skew(x)
    return out

def eligible_groups(df:pd.DataFrame,group_cols:list[str],min_area_ha:float=500,area_ha_col="Oppha")->pd.DataFrame:
    area=pd.to_numeric(df[area_ha_col],errors="coerce")
    sums=df.assign(_area=area).groupby(group_cols,dropna=False)["_area"].transform("sum")
    return df.loc[sums>=min_area_ha].copy()

def split_round_input(remainder:pd.DataFrame,group_cols:list[str],min_area_ha:float=500,area_ha_col="Oppha"):
    eligible=eligible_groups(remainder,group_cols,min_area_ha,area_ha_col)
    ids=set(eligible.index)
    deferred=remainder.loc[~remainder.index.isin(ids)].copy()
    return eligible,deferred

def accept_quality(q:dict,mae_ghg=1000,mae_nkw=500,positive_skew_limit=2)->bool:
    return (q["mae_GHG"]<=mae_ghg and q["mae_NettoKwel"]<=mae_nkw
            and q["skew_GHG"]<=positive_skew_limit and q["skew_NettoKwel"]<=positive_skew_limit)

def next_min_size(n:int,fraction:float,min_size:int,reduction_factor:float=.841)->tuple[int,float]:
    size=max(min_size,int(np.floor(n*fraction)))
    return size,fraction*reduction_factor

def staged_round_plan(df:pd.DataFrame,rounds:list[list[str]],min_area_ha=500,area_ha_col="Oppha")->pd.DataFrame:
    """Diagnostic routing before scclust: first round where group area is eligible."""
    rem=df.copy(); parts=[]
    for no,cols in enumerate(rounds,1):
        eligible,deferred=split_round_input(rem,cols,min_area_ha,area_ha_col)
        if len(eligible):
            x=eligible.copy(); x["candidate_round"]=no; parts.append(x)
        rem=deferred
    if len(rem):
        x=rem.copy(); x["candidate_round"]=0; parts.append(x)
    return pd.concat(parts).sort_index() if parts else df.assign(candidate_round=0)

class PartitionerProtocol:
    """Callable interface: partition(group, min_size) -> integer labels."""
    def __call__(self, group:pd.DataFrame, min_size:int)->np.ndarray:
        raise NotImplementedError

def identical_hydrology(group:pd.DataFrame,cols=("GHG_LHM43","NettoKwel_LHM43"))->bool:
    return all(pd.to_numeric(group[c],errors="coerce").nunique(dropna=False)<=1 for c in cols)

def adaptive_partition(group:pd.DataFrame,partitioner,*,initial_fraction=.25,reduction_factor=.841,
                       min_size=10,mae_ghg=1000,mae_nkw=500,skew_limit=2)->tuple[pd.DataFrame,dict]:
    g=group.copy()
    if identical_hydrology(g):
        g["cluster_local"]=0
        return g,{"accepted":True,"reason":"IDENTICAL_HYDROLOGY","iterations":0,"min_size":len(g)}
    fraction=initial_fraction; iterations=0; last_size=None
    while True:
        size=max(min_size,int(np.floor(len(g)*fraction)))
        if last_size==size and size<=min_size:
            return g.assign(cluster_local=-1),{"accepted":False,"reason":"MIN_SIZE_LIMIT","iterations":iterations,"min_size":size}
        labels=np.asarray(partitioner(g,size))
        if len(labels)!=len(g):raise ValueError("Partitioner returned wrong label count")
        candidate=g.assign(cluster_local=labels)
        ok=True
        for _,cluster in candidate.groupby("cluster_local"):
            if not accept_quality(cluster_quality(cluster),mae_ghg,mae_nkw,skew_limit):
                ok=False;break
        iterations+=1
        if ok:return candidate,{"accepted":True,"reason":"QUALITY_PASS","iterations":iterations,"min_size":size}
        if size<=min_size:
            return g.assign(cluster_local=-1),{"accepted":False,"reason":"MIN_SIZE_LIMIT","iterations":iterations,"min_size":size}
        last_size=size; fraction*=reduction_factor

def run_round(remainder:pd.DataFrame,group_cols:list[str],partitioner,*,round_no:int,min_area_ha=500,
              area_ha_col="Oppha",special_ldgb=(35,38,56))->tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    eligible,deferred=split_round_input(remainder,group_cols,min_area_ha,area_ha_col)
    accepted=[]; failed=[]; diagnostics=[]
    for keys,g in eligible.groupby(group_cols,dropna=False,sort=False):
        ldgb=int(g["LDGBclus"].iloc[0]); minimum=4 if ldgb in special_ldgb else 10
        clustered,diag=adaptive_partition(g,partitioner,min_size=minimum)
        diag.update({"round":round_no,"n":len(g),"LDGBclus":ldgb}); diagnostics.append(diag)
        if diag["accepted"]:
            clustered["aggr_no"]=round_no; accepted.append(clustered)
        else: failed.append(g)
    a=pd.concat(accepted) if accepted else remainder.iloc[0:0].copy()
    f=pd.concat(failed) if failed else remainder.iloc[0:0].copy()
    rem=pd.concat([deferred,f]).sort_index()
    return a,rem,pd.DataFrame(diagnostics)
