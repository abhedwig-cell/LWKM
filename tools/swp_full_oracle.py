"""Full active-SWP semantic parser/comparator for multi-run regression.

Unlike the smaller scientific gate in swp_semantic_oracle, this comparator
checks every active scalar assignment plus the four dynamic tables that the
LWKM template adapter serializes. Comments and whitespace are ignored.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
import shlex
from typing import Any

from tools.swp_template_adapter import TABLE_HEADERS

ASSIGN=re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


@dataclass(frozen=True)
class FullDifference:
    path:str
    expected:Any
    actual:Any


def _active(line:str)->str:
    out=[]
    quoted=False
    for ch in line:
        if ch=="'":
            quoted=not quoted
            out.append(ch)
        elif ch=="!" and not quoted:
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _atom(value:str)->Any:
    v=value.strip()
    if len(v)>=2 and v[0]==v[-1]=="'":
        return v[1:-1].replace("''","'")
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def parse_assignments(text:str)->dict[str,list[Any]]:
    result={}
    for raw in text.splitlines():
        s=raw.lstrip()
        if not s or s.startswith("*"):
            continue
        m=ASSIGN.match(_active(raw))
        if not m:
            continue
        key,val=m.groups()
        result.setdefault(key.upper(),[]).append(_atom(val))
    return result


def _header_tokens(header:str)->tuple[str,...]:
    return tuple(header.split())


def parse_named_table(text:str,header:str)->list[tuple[Any,...]]:
    lines=text.splitlines()
    wanted=_header_tokens(header)
    start=None
    for i,raw in enumerate(lines):
        if tuple(raw.strip().split())==wanted:
            start=i+1
            break
    if start is None:
        return []

    rows=[]
    for raw in lines[start:]:
        s=raw.strip()
        if not s:
            continue
        if s.startswith("*"):
            if rows:
                break
            continue
        if "=" in s:
            if rows:
                break
            continue
        try:
            vals=shlex.split(s,posix=True)
        except ValueError:
            vals=s.split()
        if len(vals)!=len(wanted):
            if rows:
                break
            continue
        rows.append(tuple(_atom(v) for v in vals))
    return rows


def parse_full_swp(text:str)->dict:
    return {
        "assignments":parse_assignments(text),
        "tables":{
            name:parse_named_table(text,header)
            for name,header in TABLE_HEADERS.items()
        },
    }


def _equal(a:Any,b:Any,atol:float,rtol:float)->bool:
    if isinstance(a,bool) or isinstance(b,bool):
        return a==b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isclose(float(a),float(b),abs_tol=atol,rel_tol=rtol)
    return a==b


def compare_full(
    expected:dict,
    actual:dict,
    *,
    atol:float=1e-8,
    rtol:float=1e-8,
)->list[FullDifference]:
    diffs=[]
    ea=expected.get("assignments",{})
    aa=actual.get("assignments",{})
    for key in sorted(set(ea)|set(aa)):
        ev=ea.get(key)
        av=aa.get(key)
        if ev is None or av is None:
            diffs.append(FullDifference(f"assignments.{key}",ev,av))
            continue
        if len(ev)!=len(av):
            diffs.append(FullDifference(f"assignments.{key}.count",len(ev),len(av)))
            continue
        for i,(x,y) in enumerate(zip(ev,av)):
            if not _equal(x,y,atol,rtol):
                suffix=f"[{i}]" if len(ev)>1 else ""
                diffs.append(FullDifference(f"assignments.{key}{suffix}",x,y))

    et=expected.get("tables",{})
    at=actual.get("tables",{})
    for name in sorted(set(et)|set(at)):
        erows=et.get(name,[])
        arows=at.get(name,[])
        if len(erows)!=len(arows):
            diffs.append(FullDifference(f"tables.{name}.row_count",len(erows),len(arows)))
            continue
        for i,(erow,arow) in enumerate(zip(erows,arows)):
            if len(erow)!=len(arow):
                diffs.append(FullDifference(f"tables.{name}[{i}].column_count",len(erow),len(arow)))
                continue
            for j,(x,y) in enumerate(zip(erow,arow)):
                if not _equal(x,y,atol,rtol):
                    diffs.append(FullDifference(f"tables.{name}[{i}][{j}]",x,y))
    return diffs


def compare_text(expected_text:str,actual_text:str,**kwargs)->list[FullDifference]:
    return compare_full(parse_full_swp(expected_text),parse_full_swp(actual_text),**kwargs)
