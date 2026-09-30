"""Semantic dependency fingerprints for incremental SWP rendering.

Each fingerprint class corresponds to a reason the rendered main SWP may
change. Auxiliary producer content is fingerprinted elsewhere; this module
tracks only values/references that influence the SWP itself.
"""
from __future__ import annotations
import hashlib
import json


def _hash(obj)->str:
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def dependency_fingerprints(ctx:dict,global_config:dict|None=None)->dict:
    run=ctx["run"]
    return {
      "global":_hash(global_config or {}),
      "simulation":_hash({
          "TSTART":ctx.get("TSTART"),
          "TEND":ctx.get("TEND"),
          "PONDMX":ctx.get("PONDMX"),
          "RSRO":ctx.get("RSRO"),
          "NUMNODNEW":ctx.get("NUMNODNEW"),
          "DZNEW":ctx.get("DZNEW"),
          "INLIST_CSV":ctx.get("INLIST_CSV"),
      }),
      "forcing_ref":_hash({
          "METFIL":ctx.get("METFIL"),
          "SWETR":ctx.get("SWETR"),
      }),
      "crop_rotation":_hash(ctx.get("TABLE_CROPROTATION",[])),
      "initial_condition":_hash({
          "SWINCO":ctx.get("SWINCO"),
          "GWLI":ctx.get("GWLI"),
          "INIFIL":ctx.get("INIFIL"),
      }),
      "soil_profile":_hash(ctx["TABLE_SOILPROFILE"]),
      "soil_hydraulics":_hash(ctx["TABLE_SOILHYDRFUNC"]),
      "soil_texture":_hash(ctx["TABLE_SOILTEXTURES"]),
      "rooting":_hash({
          "RDS":ctx.get("RDS_effective"),
          "RSOIL":ctx.get("RSOIL"),
          "soil_id":run.get("soil_id"),
          "crop_id":run.get("crop_id"),
          "croporg_id":run.get("croporg_id"),
          "rotation_id":run.get("rotation_id"),
      }),
      "drainage_ref":_hash({
          "SWDRA":ctx.get("SWDRA"),
          "DRFIL":ctx.get("DRFIL"),
      }),
      "bottom_ref":_hash({
          "SWBBCFILE":ctx.get("SWBBCFILE"),
          "SWBOTB":ctx.get("SWBOTB"),
          "BBCFIL":ctx.get("BBCFIL"),
          "botb":ctx.get("TABLE_BOTB"),
      }),
      "run_identity":_hash({"run_id":ctx["run_id"]}),
    }


def effective_fingerprint(parts:dict[str,str],renderer_version:str)->str:
    return _hash({"renderer_version":renderer_version,"dependencies":parts})


def changed_dependencies(old:dict[str,str]|None,new:dict[str,str])->list[str]:
    if old is None:
        return sorted(new)
    return sorted(k for k,v in new.items() if old.get(k)!=v)
