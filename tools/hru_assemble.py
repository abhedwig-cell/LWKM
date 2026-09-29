"""Post-clustering HRU assembly."""
from __future__ import annotations
import numpy as np
import pandas as pd
from tools.hru_core import nearest_donors,DEFAULT_WEIGHTS_R1,DEFAULT_WEIGHTS_R2,medoid_existing_svat

SPECIAL={35,38,56}

def return_small_nru_groups(primary:pd.DataFrame)->tuple[pd.DataFrame,pd.DataFrame]:
    if primary.empty:return primary.copy(),primary.copy()
    keys=["cluster_local","aggr_no","LDGBclus"]
    n=primary.groupby(keys,dropna=False)["svat"].transform("size")
    minimum=primary["LDGBclus"].map(lambda x:2 if int(x) in SPECIAL else 4)
    small=n<minimum
    return primary.loc[~small].copy(),primary.loc[small].copy()

def assign_existing_hru_ids(primary:pd.DataFrame)->pd.DataFrame:
    x=primary.copy()
    keys=["aggr_no","cluster_local"]+[c for c in ["LDGBclus"] if c in x]
    sig=x[keys].astype(str).agg("|".join,axis=1)
    codes,_=pd.factorize(sig,sort=True)
    x["HRU"]=codes+1
    x["hru_cluster_donor_svat"]=x["svat"]
    x["assignment_route"]="PRIMARY_CLUSTER"
    return x

def donor_round(targets:pd.DataFrame,donors:pd.DataFrame,group_cols:list[str],weights:dict,
                min_donors:int,route:str)->tuple[pd.DataFrame,pd.DataFrame]:
    assigned=[]; remainder=[]
    for key,t in targets.groupby(group_cols,dropna=False,sort=False):
        key=key if isinstance(key,tuple) else (key,)
        mask=pd.Series(True,index=donors.index)
        for c,v in zip(group_cols,key):mask &= donors[c].eq(v)
        d=donors.loc[mask]
        if len(d)<min_donors:
            remainder.append(t);continue
        z=t.copy();z["hru_cluster_donor_svat"]=nearest_donors(t,d,weights).to_numpy()
        lookup=d.set_index("svat")["HRU"]
        z["HRU"]=z["hru_cluster_donor_svat"].map(lookup)
        z["assignment_route"]=route;assigned.append(z)
    a=pd.concat(assigned) if assigned else targets.iloc[0:0].copy()
    r=pd.concat(remainder) if remainder else targets.iloc[0:0].copy()
    return a,r

def make_hru_extra(remainder:pd.DataFrame,start_hru:int,donor_selector=None)->pd.DataFrame:
    if remainder.empty:return remainder.copy()
    x=remainder.copy(); group=["LDGBclus","lu4","grondsoort4","Gt_LHM43"]
    codes,_=pd.factorize(x[group].astype(str).agg("|".join,axis=1),sort=True)
    x["HRU"]=start_hru+codes+1
    if donor_selector is None:
        raise NotImplementedError("Historical HRUextra donor selector is not yet source-bound")
    reps={}
    for h,g in x.groupby("HRU"): reps[h]=int(donor_selector(g))
    x["hru_cluster_donor_svat"]=x["HRU"].map(reps)
    x["assignment_route"]="HRU_EXTRA"
    return x

def finalize_nru(membership:pd.DataFrame)->pd.DataFrame:
    x=membership.copy()
    x["NRUcode"]=x["HRU"].astype(str)+"_"+x["LDGBclus"].astype(str)
    codes,_=pd.factorize(x["NRUcode"],sort=True);x["NRU"]=codes+1
    return x

def representative_relation(membership:pd.DataFrame,candidate_selector=None)->pd.DataFrame:
    """Historical representative relation; categorical fallback must select candidates first."""
    if candidate_selector is None:
        raise NotImplementedError("Historical packed-code representative candidate selector is not yet source-bound")
    rows=[]
    for h,g in membership.groupby("HRU",sort=True):
        candidates=candidate_selector(g)
        if candidates is None or len(candidates)==0:
            raise ValueError(f"No representative candidates for HRU {h}")
        sid=medoid_existing_svat(candidates,("GHG_LHM43","NettoKwel_LHM43"))
        rows.append({"HRU":int(h),"hru_representative_svat":sid})
    return pd.DataFrame(rows)

def assemble(primary:pd.DataFrame,remainder:pd.DataFrame,suspected:pd.DataFrame|None=None,*,hru_extra_selector=None,representative_candidate_selector=None):
    valid,small=return_small_nru_groups(primary)
    base=assign_existing_hru_ids(valid)
    rest=pd.concat([remainder,small]+([suspected] if suspected is not None and len(suspected) else []))
    a1,rest=donor_round(rest,base,["LDGBclus","lu4"],DEFAULT_WEIGHTS_R1,4,"DONOR_LDGB_LU4")
    a2,rest=donor_round(rest,base,["LDGBclus","lu2"],DEFAULT_WEIGHTS_R2,2,"DONOR_LDGB_LU2")
    extra=make_hru_extra(rest,int(base["HRU"].max()) if len(base) else 0,hru_extra_selector)
    membership=finalize_nru(pd.concat([base,a1,a2,extra],ignore_index=True))
    reps=representative_relation(membership,representative_candidate_selector)
    return membership,reps
