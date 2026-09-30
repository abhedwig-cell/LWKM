"""Extract lightweight provenance assignments from NHI/LHM control files.

This intentionally preserves the original control file as authority and emits
assignments for later alias resolution; it does not attempt to reimplement the
LHM runner.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib,re

ASSIGN=re.compile(r"^\s*([^#;\[\]][^=]*?)\s*=\s*(.*?)\s*$")

@dataclass(frozen=True)
class Assignment:
    line:int
    key:str
    raw_value:str

def control_sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def assignments(path:Path):
    out=[]
    for n,line in enumerate(path.read_text(encoding="utf-8",errors="replace").splitlines(),1):
        m=ASSIGN.match(line)
        if m:
            out.append(Assignment(n,m.group(1).strip(),m.group(2).strip()))
    return out

def select(assigns,keys):
    wanted={k.lower() for k in keys}
    return [a for a in assigns if a.key.lower() in wanted]
