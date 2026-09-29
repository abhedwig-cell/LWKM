"""Membership policy for historical and corrected P12 producers."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Member:
    svat:int
    donor:int
    label:str=""

def donor_equal(m:Member)->bool:
    return m.svat == m.donor

def historical_selection(members:list[Member])->list[bool]:
    selected=[not donor_equal(m) for m in members]
    return selected if any(selected) else [True]*len(members)

def corrected_selection(members:list[Member])->list[bool]:
    selected=[donor_equal(m) for m in members]
    if not any(selected):
        raise ValueError("HRU has no donor-source member")
    return selected

def provenance(m:Member)->str:
    rest=m.label.strip().lower()=="restgroep"
    if donor_equal(m):
        return "RESTGROUP_DONOR" if rest else "DONOR_SOURCE"
    return "RESTGROUP_TARGET" if rest else "MATCHED_TARGET"
