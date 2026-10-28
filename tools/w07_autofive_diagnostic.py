"""Deterministic fallback proposal for >5 physical drainage components.

Input is Work C2's 29-HRU retained physical-system diagnostic. Emits a concrete
five-level representation candidate and a hydraulic response audit. No production
admission is claimed: source snapshots omit dynamic H1 time series and SWAP DRA
rendering attributes needed for real model execution.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from pathlib import Path

def _class(s):
    return s["hydraulic_class"]

def _conductance(s, infiltration=False):
    if infiltration and not s.get("allow_infiltration",False): return 0.
    return 1./float(s["infres" if infiltration else "drnres"])

def _q(s,h,season):
    z=float(s[season])
    return (_conductance(s)*max(0.,h-z),
            _conductance(s,True)*max(0.,z-h))

def _eq(group):
    g=sum(_conductance(s) for s in group)
    gi=sum(_conductance(s,True) for s in group)
    zd={season:sum(_conductance(s)*float(s[season]) for s in group)/g
        for season in ("summer","winter")}
    # Single SWAP water-level series cannot separately match infiltration
    # centroid when both drainage and infiltration are active.
    return {"source":[x for s in group for x in s["source"]],
            "hydraulic_class": ("pipe" if any(_class(s)=="pipe" for s in group)
                                else "infiltration_capable_open" if gi else "drain_only_open"),
            "drnres":1/g, "infres":1/gi if gi else 100000.,
            "allow_infiltration":bool(gi), **zd}

def _partitions(n,k):
    groups=[]
    def rec(i):
        if i==n:
            if len(groups)==k: yield tuple(tuple(g) for g in groups)
            return
        for g in groups:
            g.append(i);yield from rec(i+1);g.pop()
        if len(groups)<k:
            groups.append([i]);yield from rec(i+1);groups.pop()
    yield from rec(0)

def solve(row):
    src=row["retained"]
    best=None
    # PIPE must remain separate. Only open channels can be clustered.
    pipe=[s for s in src if _class(s)=="pipe"]
    if len(pipe)!=1: raise ValueError("expected one separately represented pipe")
    others=[s for s in src if _class(s)!="pipe"]
    hvals=[i*0.1 for i in range(-10,51)]
    for partition in _partitions(len(others),4):
        groups=[[others[i] for i in idx] for idx in partition]
        eq=[_eq(g) for g in groups]+[_eq(pipe)]
        total=0.;largest=0.;drain_max=0.;infil_max=0.
        for season in ("summer","winter"):
            for h in hvals:
                d0,i0=[sum(v) for v in zip(*(_q(s,h,season) for s in src))]
                d1,i1=[sum(v) for v in zip(*(_q(s,h,season) for s in eq))]
                de=1000*(d1-d0);ie=1000*(i1-i0)
                total+=de*de+ie*ie
                largest=max(largest,abs(de+ie))
                drain_max=max(drain_max,abs(de));infil_max=max(infil_max,abs(ie))
        key=(total,tuple(tuple(x["source"]) for x in eq))
        if best is None or key<best[0]:
            best=(key,eq,largest,drain_max,infil_max)
    return {"hru":row["hru"],"status":"AUTO_APPROXIMATED_FIVE_LEVEL_DIAGNOSTIC",
            "number_source":len(src),"number_levels":5,
            "levels":best[1],"max_net_error_mm_d":best[2],
            "max_drain_error_mm_d":best[3],
            "max_infil_error_mm_d":best[4],
            "squared_error_score":best[0][0],
            "qualification":"NOT_ADMITTED_SOURCE_DIAGNOSTIC_ONLY"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    rows=json.loads(a.source.read_text())
    results=[solve(row) for row in rows]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({"schema_version":1,"count":len(results),"results":results},indent=2)+"\n")
    print(f"{len(results)} diagnostic candidate partitions")
if __name__=="__main__":main()
