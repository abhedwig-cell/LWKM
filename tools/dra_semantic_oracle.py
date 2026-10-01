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
    level_system = None
    for raw in text.splitlines():
        stripped=raw.lstrip()
        if not stripped or stripped.startswith("*"):
            continue
        active=raw.split("!",1)[0].rstrip()
        header = re.match(r"^\s*DATOWL([1-5])\s+LEVEL([1-5])\s*$", active, re.I)
        if header:
            if header[1] != header[2]:
                raise ValueError("DRA level-table system mismatch")
            level_system = int(header[1])
            systems[level_system].setdefault("LEVEL", {})
            continue
        level = re.match(r"^\s*(\d{2}-[A-Za-z]{3}-\d{4})\s+([-+0-9.eEdD]+)\s*$", active)
        if level and level_system is not None:
            date_key = level[1].lower()
            if date_key in systems[level_system]["LEVEL"]:
                raise ValueError(f"Duplicate DRA level date {date_key}")
            systems[level_system]["LEVEL"][date_key] = float(level[2].replace('D','e').replace('d','e'))
            continue
        m=ASSIGN.match(active)
        if not m:
            continue
        key,value=m.groups()
        level_system = None
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
    for key in sorted(set(expected.get("global",{})) | set(actual.get("global",{}))):
        ev=expected.get("global",{}).get(key)
        av=actual.get("global",{}).get(key)
        if not _equal(ev,av,atol,rtol):
            diffs.append(DrainDifference(f"global.{key}",ev,av))
    for sy,erow in expected.get("systems",{}).items():
        arow=actual.get("systems",{}).get(str(sy),{})
        for key in sorted(set(erow) | set(arow)):
            ev=erow.get(key)
            av=arow.get(key)
            if key == "LEVEL":
                for day in sorted(set(ev or {}) | set(av or {})):
                    evalue=(ev or {}).get(day)
                    avalue=(av or {}).get(day)
                    if not _equal(evalue,avalue,atol,rtol):
                        diffs.append(DrainDifference(f"systems.{sy}.LEVEL.{day}",evalue,avalue))
                continue
            if not _equal(ev,av,atol,rtol):
                diffs.append(DrainDifference(f"systems.{sy}.{key}",ev,av))
    return diffs


def _equal(a,b,atol,rtol):
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isclose(float(a),float(b),abs_tol=atol,rel_tol=rtol)
    return a==b
