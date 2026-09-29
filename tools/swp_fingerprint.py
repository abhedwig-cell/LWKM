"""Semantic dependency fingerprints for incremental SWP rendering."""
from __future__ import annotations
import hashlib,json

def _hash(obj)->str:
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()

def dependency_fingerprints(ctx:dict,global_config:dict|None=None)->dict:
    run=ctx["run"]
    return {
      "global":_hash(global_config or {}),
      "soil_profile":_hash(ctx["TABLE_SOILPROFILE"]),
      "soil_hydraulics":_hash(ctx["TABLE_SOILHYDRFUNC"]),
      "soil_texture":_hash(ctx["TABLE_SOILTEXTURES"]),
      "rooting":_hash({"RDS":ctx.get("RDS_effective"),"crop_id":run.get("crop_id"),"rotation_id":run.get("rotation_id")}),
      "bottom":_hash({"SWBOTB":ctx.get("SWBOTB"),"botb":ctx.get("TABLE_BOTB")}),
      "run_refs":_hash({"run_id":ctx["run_id"]}),
    }

def effective_fingerprint(parts:dict[str,str],renderer_version:str)->str:
    return _hash({"renderer_version":renderer_version,"dependencies":parts})

def changed_dependencies(old:dict[str,str]|None,new:dict[str,str])->list[str]:
    if old is None:return sorted(new)
    return sorted(k for k,v in new.items() if old.get(k)!=v)
