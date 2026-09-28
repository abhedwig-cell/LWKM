"""v0.38 meteorology aggregation core."""
from __future__ import annotations
import pandas as pd

HEADER="Station,DD,MM,YYYY,Rad,Tmin,Tmax,Hum,Wind,Rain,ETref,Wet"

def area_weighted_grid(members,values):
    wb=members.loc[members["issvatwb"].astype(bool)].copy()
    if wb.empty:wb=members.copy()
    w=pd.to_numeric(wb["area_m2"],errors="coerce")
    v=pd.to_numeric(values.loc[wb.index],errors="coerce").clip(lower=0)
    return float((v*w).sum()/w.sum())

def wetness_adjust(rain,wet,etref):
    rain=max(float(rain),0.0);wet=float(wet);etref=float(etref)
    if rain<0.01:return 0.0,0.0
    if wet<0.01:wet=max(0.01,wet)
    return rain,wet

def render_met_row(station,day,month,year,rad,tmin,tmax,hum,wind,rain,etref,wet):
    rain,wet=wetness_adjust(rain,wet,etref)
    return f"{station},{day},{month},{year},{rad},{tmin},{tmax},{hum},{wind},{rain},{etref},{wet}"
