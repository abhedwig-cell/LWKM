"""Providers for v0.38 Runs fields that are not simple constants."""
from __future__ import annotations
import math
import pandas as pd

def mean_numeric(members,col):return float(pd.to_numeric(members[col],errors="coerce").mean())

def nearest_member_to_mean_xy(members):
    x=mean_numeric(members,"xc");y=mean_numeric(members,"yc")
    d=(pd.to_numeric(members["xc"])-x)**2+(pd.to_numeric(members["yc"])-y)**2
    r=members.loc[d.idxmin()]
    return {"xc":float(r["xc"]),"yc":float(r["yc"]),"col":int(r["col"]),"row":int(r["row"])}

def gwli(members):
    return min(0,int(round((mean_numeric(members,"hh")-mean_numeric(members,"glk"))*100)))

def control_providers(control:dict):
    return {
      "PONDMX":lambda m:float(control["MaxPondDepth"])*100,
      "RSRO":lambda m:float(control["crunoff_par"]),
      "tempBot":lambda m:float(control["tempCbotk"]),
      "TSTART":lambda m:control["TimStart"],
      "TEND":lambda m:control["TimEnd"],
    }

def member_providers(members):
    loc=nearest_member_to_mean_xy(members)
    return {"GWLI":lambda m:gwli(members),"glk":lambda m:mean_numeric(members,"glk"),
            "area":lambda m:float(pd.to_numeric(members["area_m2"],errors="coerce").sum()),
            "xc":lambda m:loc["xc"],"yc":lambda m:loc["yc"],"col":lambda m:loc["col"],"row":lambda m:loc["row"]}
