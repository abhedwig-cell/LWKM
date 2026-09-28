#!/usr/bin/env python3
"""Plan incremental SWAP case generation from dependency hashes."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from tools.swap_mapping import stable_hash

def plan(current:list[dict],previous:list[dict]|None)->dict:
    old={int(x["HRU"]):x["dependency_hash"] for x in (previous or [])}
    now={int(x["HRU"]):x["dependency_hash"] for x in current}
    changed=sorted(h for h,v in now.items() if old.get(h)!=v)
    unchanged=sorted(h for h,v in now.items() if old.get(h)==v)
    removed=sorted(set(old)-set(now))
    return {"changed_or_new":changed,"unchanged":unchanged,"removed":removed,
            "counts":{"changed_or_new":len(changed),"unchanged":len(unchanged),"removed":len(removed)}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("current",type=Path); p.add_argument("output",type=Path)
    p.add_argument("--previous",type=Path)
    a=p.parse_args()
    cur=json.loads(a.current.read_text())
    prev=json.loads(a.previous.read_text()) if a.previous and a.previous.exists() else None
    result=plan(cur,prev)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
if __name__=="__main__":main()
