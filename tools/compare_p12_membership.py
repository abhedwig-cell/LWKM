"""Compare historical and corrected P12 membership, then optional hydrology."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
from tools.p12_membership import Member,historical_selection,corrected_selection,provenance

def iter_members(path:Path):
    with path.open(newline="",encoding="utf-8-sig") as f:
        r=csv.DictReader(f)
        for row in r:
            yield int(row["HRU"]), Member(int(row["svat_orig"]),int(row["svat_donor"]),row.get("label",""))

def structural_audit(path:Path):
    groups=defaultdict(list)
    for hru,m in iter_members(path): groups[hru].append(m)
    rows=[]
    for hru,members in sorted(groups.items()):
        hist=historical_selection(members)
        corr=corrected_selection(members)
        prov=defaultdict(int)
        for m in members: prov[provenance(m)]+=1
        rows.append({
          "hru":hru,"n_members":len(members),
          "n_historical":sum(hist),"n_corrected":sum(corr),
          "historical_fallback":all(hist) and all(m.svat==m.donor for m in members),
          "selection_identical":hist==corr,
          **{k.lower():v for k,v in prov.items()}
        })
    return rows

def summary(rows):
    return {
      "n_hrus":len(rows),
      "n_changed_selection":sum(not r["selection_identical"] for r in rows),
      "n_historical_fallback":sum(r["historical_fallback"] for r in rows),
      "n_zero_corrected":sum(r["n_corrected"]==0 for r in rows),
      "n_members":sum(r["n_members"] for r in rows),
      "n_selected_historical":sum(r["n_historical"] for r in rows),
      "n_selected_corrected":sum(r["n_corrected"] for r in rows),
    }
