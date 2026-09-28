"""v0.38 BBC aggregation and serialization."""
from __future__ import annotations
import pandas as pd

def water_boundary_members(members):
    x=members.loc[members["issvatwb"].astype(bool)].copy()
    return x if len(x) else members.copy()

def aggregate_qbot2(members,head_l1:pd.Series,head_l2:pd.Series)->float:
    wb=water_boundary_members(members)
    idx=wb.index
    q=((head_l2.loc[idx]-head_l1.loc[idx])/pd.to_numeric(wb["c1"],errors="coerce")).mean()
    return float(100*q)

def render_bbc(dates,values)->str:
    lines=["SWBOTB=2","SW2=2","      DATE2     QBOT2"]
    for d,v in zip(dates,values):lines.append(f"{str(d):>11}{float(v):10.4f}")
    lines.append("* End of table")
    return "\n".join(lines)+"\n"

def render_bbch(dates,haquif,c1_avg)->str:
    lines=["SWBOTB=3","SWBOTB3RESVERT=0","SWBOTB3IMPL=1","SW3=2","SW4=0","SHAPE=1.0","SHAPE_3=1.0","HDRAIN=0.0",
           f"RIMLAY={float(c1_avg):10.2f}","      DATE3     HAQUIF"]
    for d,v in zip(dates,haquif):lines.append(f"{str(d):>11} {float(v):10.1f}")
    lines.append("* End of table")
    return "\n".join(lines)+"\n"
