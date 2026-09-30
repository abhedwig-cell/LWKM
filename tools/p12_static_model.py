"""Schema-first static HRU production model.

This module deliberately separates authoritative representation from independent
spatial aggregates so provisional member majorities cannot leak into outputs.
"""
from __future__ import annotations
from dataclasses import dataclass
from tools.p12_hru_representation import HRURepresentation
from tools.p12_landuse_flags import landuse_flags

@dataclass(frozen=True)
class SoilClassification:
    bodem370:int
    bofek79:int
    pawn21:int
    grondsoort4:int
    grondsoort2:int

@dataclass(frozen=True)
class StaticRepresentation:
    hru:int
    svat_repr:int
    bodem370:int
    bofek79:int
    soil2:int
    landuse:int
    root_depth_cm:float
    swetr:int
    is_nature:bool

def build_static_representation(rep:HRURepresentation, soil:SoilClassification)->StaticRepresentation:
    if int(rep.representative_soil)!=int(soil.bodem370):
        raise ValueError((rep.representative_soil,soil.bodem370))
    flags=landuse_flags(rep.representative_landuse)
    return StaticRepresentation(
      hru=rep.hru,svat_repr=rep.representative_svat,
      bodem370=soil.bodem370,bofek79=soil.bofek79,soil2=soil.grondsoort2,
      landuse=rep.representative_landuse,
      root_depth_cm=rep.representative_root_depth_cm,
      swetr=flags.swetr,is_nature=flags.is_nature)

@dataclass(frozen=True)
class IndependentAggregates:
    meteo_district:int
    irrigation_id:int
    active_area_m2:float
    display_x:float
    display_y:float
    display_row:int
    display_col:int
    hh_mean_m:float
    ground_mean_m:float
    infiltration_mean:float

def initial_gwli_cm(hh_mean_m:float,ground_mean_m:float)->int:
    # Exact legacy arithmetic, kept separate because scientific/support audit remains open.
    return min(0,round((float(hh_mean_m)-float(ground_mean_m))*100.0))
