"""Executable >5-system fallback using *complete* aggregated physical records.

Compatible with run_dra_protected_population input (schema_version=1, hrus).
Outputs renderer-ready levels and an auditable approximation, never guessed
H1 monthly stages or spacing. Design decision: 29 historic diagnostics are
insufficient for valid .DRA bytes, hence full original records required.
"""
from __future__ import annotations
import argparse
from datetime import date
from itertools import combinations
import json
from math import isfinite
from pathlib import Path
from tools.run_dra_protected_population import physical, atomic_json
from tools.dra_level_compression import PhysicalDrainageSystem, to_render_level
from tools.dra_protected_compression import select_protected_candidate

def partitions(n,k):
    groups=[]
    def rec(i):
        if i==n:
            if len(groups)==k: yield tuple(tuple(g) for g in groups)
            return
        for group in groups:
            group.append(i)
            yield from rec(i+1)
            group.pop()
        if len(groups)<k:
            groups.append([i])
            yield from rec(i+1)
            groups.pop()
    yield from rec(0)

def level(s,day):
    if s.level_series is not None:
        lookup=dict(s.level_series)
        if day not in lookup: raise ValueError("H1/dynamic stage gap: "+day)
        return lookup[day]
    month=date.fromisoformat(day).month
    return s.peil_sum if 4<=month<=9 else s.peil_win

def stages(systems):
    dates=set()
    for s in systems:
        if s.level_series is not None: dates.update(t for t,_ in s.level_series)
    if not dates: return ("2000-01-15","2000-07-15")
    return tuple(sorted(dates))

def effective(systems):
    if not systems: raise ValueError("empty group")
    if any(s.medium=="drain_tube" for s in systems) and len(systems)>1:
        raise ValueError("pipe cannot be mixed with open channel")
    spacing={round(s.dd,9) for s in systems if s.dd is not None}
    if len(spacing)!=1: raise ValueError("missing or conflicting drainage spacing")
    g=sum(s.drainage_conductance for s in systems)
    gi=sum(s.infiltration_conductance for s in systems)
    if g<=0: raise ValueError("no drainage conductance")
    dates=stages(systems)
    series=tuple((day,sum(s.drainage_conductance*level(s,day) for s in systems)/g) for day in dates)
    # Native seasonal fields retained; if any dynamic data present, serialize
    # actual composite explicit stage axis, never replace H1 with seasons.
    explicit=any(s.level_series is not None for s in systems)
    obj=PhysicalDrainageSystem(
        source_ids=tuple(sorted(x for s in systems for x in s.source_ids)),
        hydraulic_class="infiltration_capable_open" if gi>0 else ("pipe" if systems[0].medium=="drain_tube" else "drain_only_open"),
        medium=systems[0].medium,drnres=1/g,
        infres=1/gi if gi else 100000.,
        dep=sum(s.dep*s.drainage_conductance for s in systems)/g,
        peil_sum=sum(s.peil_sum*s.drainage_conductance for s in systems)/g,
        peil_win=sum(s.peil_win*s.drainage_conductance for s in systems)/g,
        dd=systems[0].dd,
        level_series=series if explicit else None,
        drainage_conductance_raw=g,
        infiltration_conductance_raw=gi,
        physical_active=True)
    return obj

def flux(s,h,z):
    return (s.drainage_conductance*max(0,h-z),
            s.infiltration_conductance*max(0,z-h))

def loss(source,represented):
    dates=stages(source)
    # Includes every source activation threshold, not just a 0.1m grid.
    max_d=max_i=max_net=0.
    squared=0.
    for day in dates:
        heads={-1.,0.,1.,2.,3.,4.,5.}|{level(s,day) for s in source}|{level(s,day) for s in represented}
        for h in heads:
            d0=i0=d1=i1=0.
            for s in source:
                d,i=flux(s,h,level(s,day));d0+=d;i0+=i
            for s in represented:
                d,i=flux(s,h,level(s,day));d1+=d;i1+=i
            ed=1000*(d1-d0);ei=1000*(i1-i0)
            max_d=max(max_d,abs(ed));max_i=max(max_i,abs(ei));max_net=max(max_net,abs(ed-ei))
            squared+=ed*ed+ei*ei
    return dict(max_drain_error_mm_d=max_d,max_infil_error_mm_d=max_i,max_net_error_mm_d=max_net,objective=squared,head_count=len(heads),stage_count=len(dates))

def solve(systems):
    active=[s for s in systems if s.active]
    if len(active)<=5:
        return active,dict(method="NO_COMPRESSION")
    # First try the already admitted class-protected selector.
    try:
        levels,audit=select_protected_candidate(active,require_swap_interface=True)
        return levels,dict(method="PROTECTED",audit=audit)
    except (ValueError,AssertionError): pass
    tubes=[s for s in active if s.medium=="drain_tube"]
    if len(tubes)>1: raise ValueError("more than one pipe: unsupported SWAP interface")
    opens=[s for s in active if s.medium!="drain_tube"]
    count=5-len(tubes)
    if count<1 or len(opens)<count: raise ValueError("invalid active layout")
    best=None
    for part in partitions(len(opens),count):
        groups=[[opens[i] for i in ids] for ids in part]
        trial=[effective(g) for g in groups]+tubes
        try:
            rendered=[to_render_level(x) for x in trial]
            err=loss(active,trial)
        except ValueError: continue
        key=(err["objective"],tuple(tuple(g.source_ids) for g in trial))
        if best is None or key<best[0]: best=(key,trial,err)
    if best is None: raise ValueError("no parser-compatible five-level candidate")
    return best[1],dict(method="AUTO_APPROXIMATED_FIVE_LEVEL",error=best[2])

def run(source,output):
    data=json.loads(Path(source).read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not isinstance(data.get("hrus"),list):
        raise ValueError("invalid physical HRU schema")
    results=[]
    for row in data["hrus"]:
        hid=row["hru"]
        try:
            systems=[physical(s) for s in row["systems"]]
            levels,audit=solve(systems)
            rendered=[to_render_level(s) for s in levels]
            results.append(dict(hru=hid,status="RENDERER_READY_NOT_YET_DRA_FILE",audit=audit,levels=rendered))
        except (ValueError,AssertionError,TypeError,KeyError) as exc:
            results.append(dict(hru=hid,status="SOURCE_OR_INTERFACE_ERROR",error=str(exc)))
    summary=dict(schema_version=1,status="DRA_RENDER_INPUT_ONLY",hru_count=len(results),
                 error_count=sum(x["status"]=="SOURCE_OR_INTERFACE_ERROR" for x in results),
                 results=results)
    atomic_json(Path(output),summary)
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    s=run(a.input,a.output)
    print(json.dumps({"hru_count":s["hru_count"],"error_count":s["error_count"]}))
    raise SystemExit(1 if s["error_count"] else 0)
