"""Rooting-depth selection semantics isolated from legacy loop."""
from __future__ import annotations

def legacy_rds_candidates(members,bfe_maj,lgn_maj):
    """Exact legacy control flow: fallback is evaluated inside the member loop."""
    out=[]
    for m in members:
        if m["bfe"]==bfe_maj and m["lgn"]==lgn_maj:
            out.append(m["rds"])
        if len(out)==0:
            if m["lgn"]==lgn_maj:
                out.append(m["rds"])
    return out

def corrected_rds_candidates(members,bfe_maj,lgn_maj):
    """Preferred bfe+lgn population; lgn-only fallback only if preferred is globally empty."""
    preferred=[m["rds"] for m in members if m["bfe"]==bfe_maj and m["lgn"]==lgn_maj]
    if preferred:
        return preferred
    return [m["rds"] for m in members if m["lgn"]==lgn_maj]
