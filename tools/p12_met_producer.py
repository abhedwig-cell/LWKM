"""Compose P12 MET records from independently validated components."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from math import isfinite
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
    date(year,month,day)
    values=(rain,etref,daily_max_wet,district.rad,district.tmin,
            district.tmax,district.hum,district.wind,district.wet)
    if not all(isfinite(float(v)) for v in values):
        raise ValueError("MET requires finite daily meteorological values")
    if district.tmin>district.tmax:
        raise ValueError("MET Tmin exceeds Tmax")
    if district.rad<0 or district.wind<0 or etref<0:
        raise ValueError("MET negative radiation, wind or reference evaporation")
    if not 0<=district.hum<=1:
        raise ValueError("MET relative humidity outside 0..1")
    if not 0<=district.wet<=24 or not 0<=daily_max_wet<=24:
        raise ValueError("MET WET duration outside 0..24 hours")
    w=historical_wet_policy(rain,district.wet,daily_max_wet)
    return MetRecord(station,day,month,year,district.rad,district.tmin,district.tmax,
                     district.hum,district.wind,w.rain,max(etref,0.0),w.wet,w.source.value)

def render_swap_met(x:MetRecord)->str:
    # Mirrors historical output precision, while provenance remains outside the SWAP file.
    return (f"'{x.station}'{x.day:3d}{x.month:3d}{x.year:5d}{x.rad:7.0f}"
            f"{x.tmin:8.2f}{x.tmax:8.2f} {x.hum:8.4f} {x.wind:6.2f}"
            f" {x.rain:10.4f} {x.etref:10.4f} {x.wet:6.2f}")
