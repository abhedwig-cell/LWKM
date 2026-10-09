"""v0.38 BBC aggregation and serialization."""
from __future__ import annotations
import pandas as pd
import numpy as np

def water_boundary_members(members):
    x=members.loc[members["issvatwb"].astype(bool)].copy()
    return x if len(x) else members.copy()

def aggregate_qbot2(members,head_l1:pd.Series,head_l2:pd.Series)->float:
    wb=water_boundary_members(members)
    idx=wb.index
    if not idx.is_unique:
        raise ValueError("BBC member indices must be unique")
    if not idx.isin(head_l1.index).all() or not idx.isin(head_l2.index).all():
        raise ValueError("BBC head series missing required member indices")
    c1=pd.to_numeric(wb["c1"],errors="coerce").to_numpy(dtype=float)
    h1=pd.to_numeric(head_l1.loc[idx],errors="coerce").to_numpy(dtype=float)
    h2=pd.to_numeric(head_l2.loc[idx],errors="coerce").to_numpy(dtype=float)
    if not (np.isfinite(c1).all() and np.isfinite(h1).all() and np.isfinite(h2).all()):
        raise ValueError("BBC requires finite c1 and head values")
    if (c1<=0).any():
        raise ValueError("BBC c1 must be strictly positive")
    return float(100.0*np.mean((h2-h1)/c1))

def render_bbc(dates,values)->str:
    if len(dates)!=len(values) or not len(dates):
        raise ValueError("BBC dates and values must be nonempty and equally sized")
    if len(set(str(d) for d in dates))!=len(dates):
        raise ValueError("BBC dates must be unique")
    if not np.isfinite(np.asarray(values,dtype=float)).all():
        raise ValueError("BBC QBOT2 values must be finite")
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
