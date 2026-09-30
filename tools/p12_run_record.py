"""Typed replacement for legacy Fortran -> Runs CSV -> R template handoff."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RunRepresentation:
    bodem_id:int
    soil2_id:int
    landuse_id:int
    root_depth_cm:float
    swetr:int
    soil_id:int
    crop_id:int
    croporg_id:int

@dataclass(frozen=True)
class RunBoundary:
    swbbcfile:int
    swbotb:int
    swinco:int
    dqsat_m:float
    gwli_cm:int
    bbc_file:str

@dataclass(frozen=True)
class RunFiles:
    dra_file:str
    met_file:str

@dataclass(frozen=True)
class RunGeometry:
    active_area_m2:float
    display_x_m:float
    display_y_m:float
    display_col:int
    display_row:int
    source_member_count:int

@dataclass(frozen=True)
class RunConfig:
    scenario_id:str
    start_date:str
    end_date:str
    irrigation_id:int
    pond_max_cm:float
    runoff_resistance:float
    bottom_temperature_c:float
    thickness_id:int=1700
    cofani:float=1.0
    num_nodes:int=43

@dataclass(frozen=True)
class P12RunRecord:
    run_id:int
    representation:RunRepresentation
    boundary:RunBoundary
    files:RunFiles
    geometry:RunGeometry
    config:RunConfig
