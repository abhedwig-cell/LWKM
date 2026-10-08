"""Fail-closed, source-lineage-protected DRA compression candidate selector.

This is a diagnostic candidate selector, not production admission. Error
thresholds are explicit provisional inputs, never silently relaxed.
"""
from __future__ import annotations
from math import isfinite
from tools.dra_level_compression import (
    PhysicalDrainageSystem, merge_systems,
    _validate_lineage, _validate_conductance_conservation,
)

REGIONAL=frozenset(("P","S","T"))
SURFACE=frozenset(("MVG","OLF"))
PROTECTED=frozenset(("H1","PIPE"))


def _level(system, season):
    return system.peil_sum if season=="sum" else system.peil_win


def _flux_error(original, equivalent):
    """Maximum absolute flux discrepancy divided by total branch conductance.

    The piecewise-linear flux error is maximized at one of the original or
    equivalent activation breakpoints, so no arbitrary groundwater grid is used.
    """
    errors=[]
    for season in ("sum","win"):
        thresholds=sorted({_level(x,season) for x in original}|{_level(equivalent,season)})
        for direction in ("drainage","infiltration"):
            attr="drainage_conductance" if direction=="drainage" else "infiltration_conductance"
            total=sum(getattr(x,attr) for x in original)
            if total<=0: continue
            for h in thresholds:
                if direction=="drainage":
                    source=sum(x.drainage_conductance*max(_level(x,season)-h,0) for x in original)
                    merged=equivalent.drainage_conductance*max(_level(equivalent,season)-h,0)
                else:
                    source=sum(x.infiltration_conductance*max(h-_level(x,season),0) for x in original)
                    merged=equivalent.infiltration_conductance*max(h-_level(equivalent,season),0)
                errors.append(abs(source-merged)/total)
    return max(errors,default=0.0)


def _merge_group(items):
    work=list(items)
    while len(work)>1:
        work=[merge_systems(work[0],work[1]),*work[2:]]
    return work[0]


def select_protected_candidate(systems, *, max_levels=5,
                               regional_error_limit_m=0.10,
                               surface_error_limit_m=0.02):
    """Return (levels, audit) or raise when no admissible candidate exists.

    Search is exhaustive over partitions of P/S/T and MVG/OLF. H1 and PIPE
    are never merged. Each group is checked against its original physical
    flux curve, not just an intermediate centroid.
    """
    active=[s for s in systems if s.active]
    by_name={}
    for s in active:
        if len(s.source_ids)!=1: raise ValueError("expected uncompressed physical inputs")
        name=s.source_ids[0]
        if name in by_name: raise ValueError("duplicate source id")
        by_name[name]=s
    if set(by_name)-REGIONAL-SURFACE-PROTECTED:
        raise ValueError("unknown physical source")
    if max_levels < 1:
        raise ValueError("max_levels must be positive")
    if len(active)<=max_levels:
        levels=sorted(active,key=lambda x:(-x.dep,x.medium,x.source_ids))
        _validate_lineage(active,levels,[])
        _validate_conductance_conservation(active,levels)
        return levels,{"status":"NO_COMPRESSION","max_error_m":0.0,"groups":[list(s.source_ids) for s in levels]}

    names=tuple(sorted(by_name))
    # Restricted growth partitions, exhaustive for at most seven sources.
    partitions=[()]
    for name in names:
        next_partitions=[]
        for partition in partitions:
            next_partitions.append(partition+((name,),))
            for i in range(len(partition)):
                next_partitions.append(partition[:i]+(partition[i]+(name,),)+partition[i+1:])
        partitions=next_partitions

    best=None
    for partition in partitions:
        if len(partition)>max_levels: continue
        if any(len(g)>1 and (
            bool(set(g)&PROTECTED) or
            not (set(g)<=REGIONAL or set(g)<=SURFACE)
        ) for g in partition): continue
        try:
            levels=[_merge_group([by_name[n] for n in g]) for g in partition]
        except ValueError:
            continue
        group_errors=[]
        for group,level in zip(partition,levels):
            err=_flux_error([by_name[n] for n in group],level)
            limit=surface_error_limit_m if set(group)<=SURFACE else regional_error_limit_m
            if not isfinite(err) or err>limit: break
            group_errors.append(err)
        else:
            key=(max(group_errors,default=0.0),sum(group_errors),tuple(sorted(tuple(sorted(g)) for g in partition)))
            if best is None or key<best[0]: best=(key,levels,partition,group_errors)
    if best is None:
        raise ValueError("NO_ACCEPTABLE_PROTECTED_FIVE_LEVEL_PARTITION")
    _,levels,partition,errors=best
    levels.sort(key=lambda x:(-x.dep,x.medium,x.source_ids))
    _validate_lineage(active,levels,[])
    _validate_conductance_conservation(active,levels)
    return levels,{"status":"CANDIDATE_NOT_ADMITTED","max_error_m":max(errors,default=0.0),
                   "groups":[list(x.source_ids) for x in levels],
                   "regional_limit_m":regional_error_limit_m,
                   "surface_limit_m":surface_error_limit_m}
