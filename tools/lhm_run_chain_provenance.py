"""Build provenance across a sequence of LHM control files.

No LHM scientific logic is reimplemented. This layer inventories configured
dependencies, resolves aliases, detects changes between periods and prepares
a deduplicated source-bundle plan.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import re,json

ASSIGN=re.compile(r"^\s*([^#;\[\]][^=]*?)\s*=\s*(.*?)\s*$")
ALIAS=re.compile(r"%\(%([^%]+)%\)s")
YEAR_KEY=re.compile(r"^(prec|evap|tmin|tmax|tmean|radiation|humidity|vapp)_(\d{4})$",re.I)

@dataclass(frozen=True)
class ControlValue:
    control_file:str
    line:int
    key:str
    raw:str
    resolved:str|None

def parse(path:Path):
    vals=[]; aliases={}
    for n,line in enumerate(path.read_text(encoding="utf-8",errors="replace").splitlines(),1):
        m=ASSIGN.match(line)
        if not m: continue
        key=m.group(1).strip(); raw=m.group(2).strip()
        if key.startswith("%") and key.endswith("%"):
            aliases[key[1:-1].lower()]=raw
        vals.append((n,key,raw))
    def resolve(v):
        prev=None
        for _ in range(30):
            if v==prev: break
            prev=v
            def sub(m):
                k=m.group(1).lower()
                return aliases.get(k,m.group(0))
            v=ALIAS.sub(sub,v)
        return v if "%(%" not in v else None
    return [ControlValue(path.name,n,k,r,resolve(r)) for n,k,r in vals]

def compare_controls(paths):
    parsed={Path(p).name:parse(Path(p)) for p in paths}
    by_key={}
    for fn,vals in parsed.items():
        for v in vals: by_key.setdefault(v.key.lower(),{})[fn]=v.resolved or v.raw
    stable={}; varying={}
    for k,mp in by_key.items():
        unique=set(mp.values())
        (stable if len(unique)==1 and len(mp)==len(parsed) else varying)[k]=mp
    return {"controls":sorted(parsed),"stable":stable,"varying":varying}

def meteo_year_dependencies(paths):
    out={}
    for p in paths:
        for v in parse(Path(p)):
            m=YEAR_KEY.match(v.key)
            if m: out.setdefault(int(m.group(2)),{})[m.group(1).lower()]=v.resolved or v.raw
    return out

def write_run_chain(paths,out:Path):
    result=compare_controls(paths)
    result["meteo_by_year"]=meteo_year_dependencies(paths)
    out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
