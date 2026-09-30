"""Land-use-dependent HRU flags must derive from authoritative representation."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LanduseFlags:
    swetr:int
    is_nature:bool

def landuse_flags(lgn:int)->LanduseFlags:
    lgn=int(lgn)
    return LanduseFlags(
      swetr=0 if lgn<7 else 1,
      is_nature=(10<lgn<21 and lgn!=18),
    )
