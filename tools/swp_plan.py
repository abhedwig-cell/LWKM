"""Plan incremental SWP materialization from resolved contexts."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from tools.swp_fingerprint import dependency_fingerprints,effective_fingerprint,changed_dependencies

@dataclass(frozen=True)
class PlanItem:
    key:int
    action:str
    reasons:tuple[str,...]
    fingerprint:str

def load_cache(path:Path)->dict:
    if not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))

def plan(contexts:list[dict],cache:dict,renderer_version:str,global_config:dict|None=None)->list[PlanItem]:
    out=[]
    for ctx in contexts:
        key=int(ctx["run_id"])
        parts=dependency_fingerprints(ctx,global_config)
        fp=effective_fingerprint(parts,renderer_version)
        old=cache.get(str(key))
        if old and old.get("fingerprint")==fp:
            out.append(PlanItem(key,"skip",(),fp))
        else:
            reasons=tuple(changed_dependencies(old.get("dependencies") if old else None,parts))
            out.append(PlanItem(key,"create" if old is None else "update",reasons,fp))
    return out

def updated_cache(contexts:list[dict],renderer_version:str,global_config:dict|None=None)->dict:
    result={}
    for ctx in contexts:
        parts=dependency_fingerprints(ctx,global_config)
        result[str(int(ctx["run_id"]))]={"dependencies":parts,"fingerprint":effective_fingerprint(parts,renderer_version)}
    return result
