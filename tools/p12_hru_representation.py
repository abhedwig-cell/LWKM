"""Typed authoritative HRU representation consumed by SWAP producers."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class HRURepresentation:
    hru:int
    representative_svat:int
    representative_root_depth_cm:float
    representative_bfe:int
    representative_soil:int
    representative_landuse:int
    provenance:str="PIET_HRU_SCHEMA"

def resolve_hru_representation(schema_row, svat_attributes)->HRURepresentation:
    """Resolve schema authority once; land use follows schema-selected representative SVAT."""
    hru=int(schema_row["hru"])
    svat=int(schema_row["svat_repr"])
    if svat not in svat_attributes:
        raise ValueError(f"HRU {hru}: representative SVAT {svat} missing")
    a=svat_attributes[svat]
    return HRURepresentation(
      hru=hru,
      representative_svat=svat,
      representative_root_depth_cm=float(schema_row["rz_repr"]),
      representative_bfe=int(schema_row["bfe_repr"]),
      representative_soil=int(schema_row["bodem_repr"]),
      representative_landuse=int(a["lgn"]),
    )
