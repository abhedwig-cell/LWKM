#!/usr/bin/env python3
"""Compare one SQLite datamodel run directly against a semantic SWP oracle.

This gate qualifies datamodel/domain joins independently of template formatting.
Exit status:
0 = context semantics match the oracle
1 = semantic differences found
2 = invalid/unrenderable context or oracle
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.swp_context import build_context, validate_context
from tools.swp_semantic_oracle import compare_semantics, context_semantics


def _load_oracle(path:Path)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if "scalars" not in data or "tables" not in data:
        raise ValueError("oracle JSON must contain scalars and tables")
    return {"scalars":data["scalars"],"tables":data["tables"]}


def compare_context(db:Path,run_id:int,oracle:Path,*,atol:float=1e-9,rtol:float=1e-9):
    ctx=build_context(db,run_id)
    validate_context(ctx)
    expected=_load_oracle(oracle)
    actual=context_semantics(ctx)
    return compare_semantics(expected,actual,atol=atol,rtol=rtol),ctx


def main(argv=None)->int:
    p=argparse.ArgumentParser(prog="compare-swp-context")
    p.add_argument("database",type=Path)
    p.add_argument("run_id",type=int)
    p.add_argument("oracle",type=Path)
    p.add_argument("--atol",type=float,default=1e-9)
    p.add_argument("--rtol",type=float,default=1e-9)
    a=p.parse_args(argv)
    try:
        diffs,ctx=compare_context(a.database,a.run_id,a.oracle,atol=a.atol,rtol=a.rtol)
    except Exception as exc:
        print(json.dumps({"status":"invalid","error":str(exc)},indent=2))
        return 2
    payload={
        "status":"match" if not diffs else "different",
        "run_id":a.run_id,
        "difference_count":len(diffs),
        "diagnostics":ctx.get("diagnostics",[]),
        "differences":[
            {"path":d.path,"expected":d.expected,"actual":d.actual}
            for d in diffs
        ],
    }
    print(json.dumps(payload,indent=2,default=str))
    return 0 if not diffs else 1


if __name__=="__main__":
    raise SystemExit(main())
