"""v0.38 meteorology aggregation core."""
from __future__ import annotations
import pandas as pd
import numpy as np

HEADER="Station,DD,MM,YYYY,Rad,Tmin,Tmax,Hum,Wind,Rain,ETref,Wet"

def area_weighted_grid(members,values):
    wb=members.loc[members["issvatwb"].astype(bool)].copy()
    if wb.empty:wb=members.copy()
    if wb.empty:
        raise ValueError("MET cannot aggregate an empty HRU")
    if not wb.index.is_unique or not wb.index.isin(values.index).all():
        raise ValueError("MET member index missing or duplicated")
    w=pd.to_numeric(wb["area_m2"],errors="coerce").to_numpy(dtype=float)
    v=pd.to_numeric(values.loc[wb.index],errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(w).all() or (w<=0).any():
        raise ValueError("MET requires finite positive member areas")
    if not np.isfinite(v).all():
        raise ValueError("MET requires finite member values")
    return float((np.maximum(v,0)*w).sum()/w.sum())

def wetness_adjust(rain,wet,etref):
    rain=max(float(rain),0.0);wet=float(wet);etref=float(etref)
    if rain<0.01:return 0.0,0.0
    if wet<0.01:wet=max(0.01,wet)
    return rain,wet

def render_met_row(station,day,month,year,rad,tmin,tmax,hum,wind,rain,etref,wet):
    rain,wet=wetness_adjust(rain,wet,etref)
    return f"{station},{day},{month},{year},{rad},{tmin},{tmax},{hum},{wind},{rain},{etref},{wet}"
