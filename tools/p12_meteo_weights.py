"""Precompute sparse HRU-to-meteo-pixel area weights."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

def pixel_1km(x:float,y:float,xmin=0.0,ymax=625000.0,cell=1000.0,ncol=300,nrow=325):
    col=int((x-xmin)//cell); row=int((ymax-y)//cell)
    if not (0<=row<nrow and 0<=col<ncol): raise IndexError((x,y,row,col))
    return row,col

def build_weights(rows, mode:str):
    by_hru=defaultdict(list)
    for r in rows: by_hru[int(r["HRU"])].append(r)
    out=[]
    for hru,members in sorted(by_hru.items()):
        eq=[int(r["svat_orig"])==int(r["svat_donor"]) for r in members]
        if mode=="donor_equal":
            sel=eq
            if not any(sel): raise ValueError(f"HRU {hru}: no donor")
        elif mode=="source_current":
            sel=[not x for x in eq]
            if not any(sel): sel=[True]*len(members)
        else: raise ValueError(mode)
        pix=defaultdict(float)
        for r,s in zip(members,sel):
            if not s: continue
            # area column name is deliberately supplied by caller contract
            a=float(r["uopp_m2"])
            if a<=0: raise ValueError(f"HRU {hru}: nonpositive area")
            pix[pixel_1km(float(r["x"]),float(r["y"]))]+=a
        total=sum(pix.values())
        for (row,col),a in sorted(pix.items()):
            out.append({"hru":hru,"row":row,"col":col,"uopp_m2":a,"weight":a/total})
    return out

def aggregate_grid(weight_rows,grid):
    sums=defaultdict(float)
    for w in weight_rows:
        v=float(grid[w["row"],w["col"]])
        sums[w["hru"]]+=v*w["weight"]
    return sums
