"""Parse and compare realized SWAP DRA semantics.

The parser focuses on scalar system parameters used by the P12 drainage
regression gate. Seasonal level tables remain available for a later extension.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any

ASSIGN=re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*([^!]+?)\s*$")
SYSTEM_FIELD=re.compile(r"^(DRARES|INFRES|SWALLO|L|ZBOTDR|SWDTYP)([1-5])$")


@dataclass(frozen=True)
class DrainDifference:
    path:str
    expected:Any
    actual:Any


def _atom(value:str)->Any:
    text=value.strip()
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def parse_dra(text:str)->dict:
    global_values={}
    systems={i:{} for i in range(1,6)}
    for raw in text.splitlines():
        stripped=raw.lstrip()
        if not stripped or stripped.startswith("*"):
            continue
        active=raw.split("!",1)[0].rstrip()
        m=ASSIGN.match(active)
        if not m:
            continue
        key,value=m.groups()
        key=key.upper()
        sm=SYSTEM_FIELD.match(key)
        if sm:
            field,system=sm.groups()
            systems[int(system)][field]=_atom(value)
        else:
            global_values[key]=_atom(value)
    return {
        "global":global_values,
        "systems":{str(k):v for k,v in systems.items()},
    }


def compare_dra(expected:dict,actual:dict,*,atol:float=1e-9,rtol:float=1e-9):
    diffs=[]
    for key,ev in expected.get("global",{}).items():
        av=actual.get("global",{}).get(key)
        if not _equal(ev,av,atol,rtol):
            diffs.append(DrainDifference(f"global.{key}",ev,av))
    for sy,erow in expected.get("systems",{}).items():
        arow=actual.get("systems",{}).get(str(sy),{})
        for key,ev in erow.items():
            av=arow.get(key)
            if not _equal(ev,av,atol,rtol):
                diffs.append(DrainDifference(f"systems.{sy}.{key}",ev,av))
    return diffs


def _equal(a,b,atol,rtol):
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isclose(float(a),float(b),abs_tol=atol,rel_tol=rtol)
    return a==b
