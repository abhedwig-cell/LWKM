"""Explicit rainfall-duration consistency policy."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class WetSource(str,Enum):
    DISTRICT="DISTRICT"
    FORCED_DRY_ZERO="FORCED_DRY_ZERO"
    IMPUTED="IMPUTED"

@dataclass(frozen=True)
class WetResult:
    rain:float
    wet:float
    source:WetSource

def historical_wet_policy(rain:float,district_wet:float,daily_max_wet:float,threshold:float=0.01)->WetResult:
    rain=max(float(rain),0.0)
    if rain < threshold:
        return WetResult(0.0,0.0,WetSource.FORCED_DRY_ZERO)
    if district_wet < threshold:
        return WetResult(rain,max(threshold,float(daily_max_wet)),WetSource.IMPUTED)
    return WetResult(rain,float(district_wet),WetSource.DISTRICT)

def assert_wet_invariant(x:WetResult)->None:
    if x.rain==0 and x.wet!=0: raise AssertionError(x)
    if x.rain>0 and x.wet<=0: raise AssertionError(x)
