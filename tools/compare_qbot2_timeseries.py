"""Stream historical vs corrected QBOT2 over native Deltares IDF head snapshots."""
from __future__ import annotations
from pathlib import Path
import re, csv
import numpy as np
from tools.idf_reader import read_idf,row_col
from tools.p12_membership import Member,historical_selection,corrected_selection

DATE_RE=re.compile(r"head_(\d{14})_l1\.IDF$",re.I)

def load_members(csv_path:Path,c1_path:Path):
    c1=read_idf(c1_path)
    groups={}
    with csv_path.open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            h=int(r["HRU"]); x=float(r["x"]); y=float(r["y"])
            rr,cc=row_col(c1,x,y); cv=float(c1.values[rr,cc])
            if not np.isfinite(cv) or cv<=0 or cv==c1.nodata:
                raise ValueError(f"invalid c1 HRU={h} svat={r['svat_orig']}: {cv}")
            groups.setdefault(h,[]).append((Member(int(r["svat_orig"]),int(r["svat_donor"]),r.get("label","")),x,y,cv))
    return groups

def compare_snapshot(groups,h1_path:Path,h2_path:Path):
    h1=read_idf(h1_path); h2=read_idf(h2_path)
    out=[]
    for h,members in groups.items():
        ms=[x[0] for x in members]; hs=historical_selection(ms); cs=corrected_selection(ms)
        q=[]
        for _,x,y,c in members:
            r1,c1=row_col(h1,x,y); r2,c2=row_col(h2,x,y)
            a=float(h1.values[r1,c1]); b=float(h2.values[r2,c2])
            if any((not np.isfinite(v)) for v in (a,b)) or a==h1.nodata or b==h2.nodata:
                raise ValueError(f"invalid head HRU={h} x={x} y={y}")
            q.append(100.0*(b-a)/c)
        old=float(np.mean([v for v,s in zip(q,hs) if s]))
        new=float(np.mean([v for v,s in zip(q,cs) if s]))
        out.append((h,old,new,new-old))
    return out

def paired_heads(directory:Path):
    for p1 in sorted(directory.glob("head_*_l1.IDF")):
        m=DATE_RE.match(p1.name)
        if not m: continue
        p2=directory/(p1.name[:-6]+"l2.IDF")
        if p2.exists(): yield m.group(1),p1,p2
