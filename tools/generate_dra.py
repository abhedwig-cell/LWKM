"""Active v0.38 drainage aggregation and DRA serialization."""
from __future__ import annotations
import numpy as np
import pandas as pd

def conductance_weighted_depth(glk,bottom,cdr):
    g=pd.to_numeric(glk,errors="coerce").to_numpy(float)
    b=pd.to_numeric(bottom,errors="coerce").to_numpy(float)
    c=pd.to_numeric(cdr,errors="coerce").fillna(0).to_numpy(float)
    return float(np.sum(c*(g-b))/np.sum(c)) if np.sum(c)>0 else 0.0

def aggregate_system(members,sy:int,dqsat_maj:float):
    cdr=pd.to_numeric(members[f"cdr{sy}"],errors="coerce").fillna(0)
    inf=pd.to_numeric(members[f"inf{sy}"],errors="coerce").fillna(0)
    n=len(members);cs=float(cdr.sum());ins=float((cdr*inf).sum())
    leng=float(pd.to_numeric(members[f"leng{sy}"],errors="coerce").fillna(0).sum())
    dd=float(dqsat_maj)*4 if leng>0 else 100.0
    dra=min(100000.0,max(1.0,62500.0*n/cs if cs>0 else 100000.0))
    infres=min(100000.0,max(1.0,62500.0*n/ins if ins>0 else 100000.0))
    dep=conductance_weighted_depth(members["glk"],members[f"bodh{sy}"],cdr)
    glkavg=float(pd.to_numeric(members["glk"],errors="coerce").mean())
    ps=glkavg-conductance_weighted_depth(members["glk"],members[f"peil_sum{sy}"],cdr)
    pw=glkavg-conductance_weighted_depth(members["glk"],members[f"peil_win{sy}"],cdr)
    # Historical repair converts levels to positive depth below surface and caps by drainage depth.
    ps=min(max(0.0,-ps+glkavg),max(0.0,dep));pw=min(max(0.0,-pw+glkavg),max(0.0,dep));dep=max(0.0,dep)
    return {"drnres":dra,"infres":infres,"dd":dd,"dep":dep,"peil_sum":ps,"peil_win":pw}

def repair_system(s:dict,sy:int,isnatuur:bool)->dict:
    x=dict(s)
    if x["drnres"]>20000 or (sy==4 and isnatuur):
        x.update({"peil_sum":0.0,"peil_win":0.0,"dep":0.0,"drnres":100000.0,"infres":100000.0})
    return x

def render_dra(systems:list[dict],n_horizons:int,year_start:int,year_end:int,infil_avg:float)->str:
    lines=["DRAMET = 3","SWDIVD = 1","COFANI ="+" 1.0"*int(n_horizons),"SWDISLAY = 0","NRLEVS = 5","SWINTFL = 0","SWTOPNRSRF = 0",""]
    for sy,s in enumerate(systems,1):
        swallo=3 if sy>3 or s["infres"]>20000 or infil_avg<10 else 1
        lines += [f"DRARES{sy} = {s['drnres']:8.0f}",f"INFRES{sy} = {s['infres']:8.0f}",
                  f"SWALLO{sy} = {swallo}",f"L{sy} = {max(1.0,s['dd']):8.0f}",
                  f"ZBOTDR{sy} = {-s['dep']*100:8.2f}",f"SWDTYP{sy} = {1 if sy==4 else 2}"," ",
                  f"    DATOWL{sy}   LEVEL{sy}",f" 01-jan-{year_start} {-s['peil_win']*100:8.2f}"]
        for y in range(year_start,year_end+1):
            lines += [f" 01-apr-{y} {-s['peil_sum']*100:8.2f}",f" 01-oct-{y} {-s['peil_win']*100:8.2f}"]
        lines.append("* End of table")
    return "\n".join(lines)+"\n"
