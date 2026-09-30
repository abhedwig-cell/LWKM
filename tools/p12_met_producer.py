"""Compose P12 MET records from independently validated components."""
from __future__ import annotations
from dataclasses import dataclass
from tools.p12_wet_policy import historical_wet_policy

@dataclass(frozen=True)
class DistrictDay:
    rad:float; tmin:float; tmax:float; hum:float; wind:float; wet:float

@dataclass(frozen=True)
class MetRecord:
    station:int; day:int; month:int; year:int
    rad:float; tmin:float; tmax:float; hum:float; wind:float
    rain:float; etref:float; wet:float
    wet_source:str

def compose(station:int,day:int,month:int,year:int,rain:float,etref:float,
            district:DistrictDay,daily_max_wet:float)->MetRecord:
    w=historical_wet_policy(rain,district.wet,daily_max_wet)
    return MetRecord(station,day,month,year,district.rad,district.tmin,district.tmax,
                     district.hum,district.wind,w.rain,max(etref,0.0),w.wet,w.source.value)

def render_swap_met(x:MetRecord)->str:
    # Mirrors historical output precision, while provenance remains outside the SWAP file.
    return (f"'{x.station}'{x.day:3d}{x.month:3d}{x.year:5d}{x.rad:7.0f}"
            f"{x.tmin:8.2f}{x.tmax:8.2f} {x.hum:8.4f} {x.wind:6.2f}"
            f" {x.rain:10.4f} {x.etref:10.4f} {x.wet:6.2f}")
