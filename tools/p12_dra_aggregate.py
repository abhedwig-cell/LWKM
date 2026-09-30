"""Equivalent drainage aggregation for all-member HRUs."""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

CELL_AREA_M2=62500.0

@dataclass(frozen=True)
class DrainEquivalent:
    drares_day:float
    infres_day:float
    depth_m:float|None=None
    summer_depth_m:float|None=None
    winter_depth_m:float|None=None

def resistance(conductance_m2_day):
    c=[max(0.0,float(x)) for x in conductance_m2_day]
    if not c: raise ValueError("empty HRU")
    s=sum(c)
    r=100000.0 if s<=0 else CELL_AREA_M2*len(c)/s
    return min(100000.0,max(1.0,r))

def infiltration_resistance(conductance_m2_day,infiltration_factor):
    c=list(conductance_m2_day); f=list(infiltration_factor)
    if len(c)!=len(f) or not c: raise ValueError("shape/empty")
    s=sum(max(0.0,float(ci))*max(0.0,float(fi)) for ci,fi in zip(c,f))
    r=100000.0 if s<=0 else CELL_AREA_M2*len(c)/s
    return min(100000.0,max(1.0,r))

def weighted_depth(conductance_m2_day,ground_m,level_m):
    triples=list(zip(conductance_m2_day,ground_m,level_m))
    den=sum(max(0.0,float(c)) for c,_,_ in triples)
    if den<=0:return 0.0
    return sum(max(0.0,float(c))*(float(g)-float(z)) for c,g,z in triples)/den
