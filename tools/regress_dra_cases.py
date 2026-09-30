#!/usr/bin/env python3
"""Batch regression for realized versus candidate DRA files.

This harness performs only semantic comparison. It does not reconstruct
scientific drainage inputs or decide whether an intentional difference is
physically preferable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import yaml

from tools.dra_semantic_oracle import compare_dra, parse_dra


RUN_RE=re.compile(r"(?:run[_-]?)?(\d+)$",re.I)


def infer_run_id(path:Path)->int:
    for token in (path.parent.name,path.stem):
        m=RUN_RE.search(token)
        if m:
            return int(m.group(1))
    # Historical DRA files frequently contain run-specific numeric names only.
    m=re.search(r"(\d+)",path.name)
    if m:
        return int(m.group(1))
    raise ValueError(f"Cannot infer run id from {path}")


def discover(root:Path,pattern:str="*.dra")->dict[int,Path]:
    root=Path(root)
    paths=sorted(root.rglob(pattern))
    if root.is_file() and root.match(pattern):
        paths=[root]
    out={}
    for p in paths:
        rid=infer_run_id(p)
        if rid in out:
            raise ValueError(f"duplicate DRA for run {rid}: {out[rid]} and {p}")
        out[rid]=p
    return out


def _expected(path:Path|None)->dict[int,set[str]]:
    if path is None:
        return {}
    data=yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    raw=data.get("expected_differences",data)
    return {int(k):{str(x) for x in (v or [])} for k,v in raw.items()}


def regress_dra(
    *,
    oracle_root:Path,
    candidate_root:Path,
    expected_differences:Path|None=None,
    pattern:str="*.dra",
    atol:float=1e-8,
    rtol:float=1e-8,
)->dict:
    oracle=discover(oracle_root,pattern)
    candidate=discover(candidate_root,pattern)
    if not oracle:
        raise FileNotFoundError(f"No DRA oracles under {oracle_root}")
    expected=_expected(expected_differences)

    rows=[]
    missing_candidate=sorted(set(oracle)-set(candidate))
    extra_candidate=sorted(set(candidate)-set(oracle))

    for run_id in sorted(set(oracle)&set(candidate)):
        e=parse_dra(oracle[run_id].read_text(encoding="utf-8",errors="replace"))
        a=parse_dra(candidate[run_id].read_text(encoding="utf-8",errors="replace"))
        diffs=compare_dra(e,a,atol=atol,rtol=rtol)
        paths={d.path for d in diffs}
        exp=expected.get(run_id,set())
        unexplained=sorted(paths-exp)
        expected_observed=sorted(paths&exp)
        expected_missing=sorted(exp-paths)
        if not paths:
            status="PASS"
        elif not unexplained and not expected_missing:
            status="EXPECTED_DIFFERENCE"
        else:
            status="FAIL"
        rows.append({
            "run_id":run_id,
            "oracle":str(oracle[run_id]),
            "candidate":str(candidate[run_id]),
            "status":status,
            "difference_count":len(diffs),
            "expected_observed":expected_observed,
            "expected_not_observed":expected_missing,
            "unexplained":unexplained,
            "differences":[
                {"path":d.path,"expected":d.expected,"actual":d.actual}
                for d in diffs
            ],
        })

    counts={}
    for row in rows:
        counts[row["status"]]=counts.get(row["status"],0)+1

    unexplained_total=sum(len(r["unexplained"]) for r in rows)
    expected_missing_total=sum(len(r["expected_not_observed"]) for r in rows)
    admission=(
        not missing_candidate
        and not extra_candidate
        and unexplained_total==0
        and expected_missing_total==0
    )
    return {
        "schema":"lwkm-dra-multirun-regression-v1",
        "oracle_count":len(oracle),
        "candidate_count":len(candidate),
        "compared_count":len(rows),
        "missing_candidate_runs":missing_candidate,
        "extra_candidate_runs":extra_candidate,
        "status_counts":counts,
        "unexplained_difference_paths":unexplained_total,
        "expected_difference_paths_not_observed":expected_missing_total,
        "admission_candidate":admission,
        "cases":rows,
    }


def main(argv=None)->int:
    p=argparse.ArgumentParser(prog="regress-dra-cases")
    p.add_argument("--oracle-root",required=True,type=Path)
    p.add_argument("--candidate-root",required=True,type=Path)
    p.add_argument("--expected-differences",type=Path)
    p.add_argument("--pattern",default="*.dra")
    p.add_argument("--output",type=Path)
    p.add_argument("--atol",type=float,default=1e-8)
    p.add_argument("--rtol",type=float,default=1e-8)
    a=p.parse_args(argv)
    try:
        result=regress_dra(
            oracle_root=a.oracle_root,
            candidate_root=a.candidate_root,
            expected_differences=a.expected_differences,
            pattern=a.pattern,
            atol=a.atol,
            rtol=a.rtol,
        )
    except Exception as exc:
        print(json.dumps({"status":"INVALID","error":str(exc)},indent=2))
        return 2

    text=json.dumps(result,indent=2,default=str)
    print(text)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(text+"\n",encoding="utf-8")
    return 0 if result["admission_candidate"] else 1


if __name__=="__main__":
    raise SystemExit(main())
