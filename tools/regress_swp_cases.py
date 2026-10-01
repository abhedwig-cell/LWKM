#!/usr/bin/env python3
"""Run the direct-SWP renderer against a directory of realized run oracles.

The harness separates:
- historical serialization equivalence;
- explicitly pre-registered expected differences;
- unexplained differences.

It performs no scientific correction itself.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tempfile

import yaml

from tools.swp_context import build_context, validate_context
from tools.swp_full_oracle import compare_text
from tools.swp_renderer import render_text
from tools.swp_template_adapter import apply_render_profile, canonicalize_legacy_template


RUN_NAME=re.compile(r"(?:run[_-]?)?(\d+)$",re.I)


def infer_run_id(swp_path:Path)->int:
    for part in (swp_path.parent.name,swp_path.stem):
        m=RUN_NAME.search(part)
        if m:
            return int(m.group(1))

    # Fallback to run-specific file references in the realized SWP.
    text=swp_path.read_text(encoding="utf-8",errors="replace")
    for key in ("DRFIL","BBCFIL","METFIL"):
        m=re.search(
            rf"(?mi)^\s*{key}\s*=\s*'?(\d+)(?:\.met)?'?",
            text,
        )
        if m:
            return int(m.group(1))
    raise ValueError(f"Cannot infer run id from {swp_path}")


def discover_cases(root:Path,oracle_name:str="swap.swp")->list[tuple[int,Path]]:
    root=Path(root)
    paths=sorted(root.rglob(oracle_name))
    if not paths and root.is_file() and root.name==oracle_name:
        paths=[root]
    cases=[]
    seen={}
    for p in paths:
        run_id=infer_run_id(p)
        if run_id in seen:
            raise ValueError(
                f"duplicate realized SWP for run {run_id}: {seen[run_id]} and {p}"
            )
        seen[run_id]=p
        cases.append((run_id,p))
    return sorted(cases)


def _expected_map(path:Path|None)->dict[int,set[str]]:
    if path is None:
        return {}
    data=yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    raw=data.get("expected_differences",data)
    result={}
    for key,values in raw.items():
        result[int(key)]={str(v) for v in (values or [])}
    return result


def classify_differences(diffs,expected:set[str]):
    paths={d.path for d in diffs}
    expected_hit=sorted(paths & expected)
    unexplained=sorted(paths - expected)
    expected_missing=sorted(expected - paths)
    return {
        "difference_paths":sorted(paths),
        "expected_observed":expected_hit,
        "unexplained":unexplained,
        "expected_not_observed":expected_missing,
        "status":"PASS" if not paths else (
            "EXPECTED_DIFFERENCE" if not unexplained and not expected_missing
            else "FAIL"
        ),
    }


def regress_cases(
    *,
    database:Path,
    legacy_template:Path,
    profile_path:Path,
    cases_root:Path,
    expected_differences:Path|None=None,
    oracle_name:str="swap.swp",
    atol:float=1e-8,
    rtol:float=1e-8,
)->dict:
    profile=yaml.safe_load(Path(profile_path).read_text(encoding="utf-8"))
    if Path(database).suffix.lower() == ".xlsx":
        from tools.xlsx_datamodel import materialize_workbook
        with tempfile.TemporaryDirectory(prefix="lwkm-xlsx-") as directory:
            execution_db = Path(directory) / "execution.sqlite"
            ingestion = materialize_workbook(database, execution_db)
            result = regress_cases(
                database=execution_db, legacy_template=legacy_template,
                profile_path=profile_path, cases_root=cases_root,
                expected_differences=expected_differences,
                oracle_name=oracle_name, atol=atol, rtol=rtol,
            )
            result["workbook_ingestion"] = ingestion
            return result
    template=canonicalize_legacy_template(
        Path(legacy_template).read_text(encoding="utf-8",errors="replace")
    )
    expected=_expected_map(expected_differences)
    cases=discover_cases(cases_root,oracle_name)
    if not cases:
        raise FileNotFoundError(f"No realized {oracle_name} files under {cases_root}")

    rows=[]
    for run_id,oracle_path in cases:
        ctx=build_context(database,run_id)
        validate_context(ctx)
        ctx=apply_render_profile(ctx,profile)
        candidate=render_text(template,ctx)
        oracle=oracle_path.read_text(encoding="utf-8",errors="replace")
        diffs=compare_text(oracle,candidate,atol=atol,rtol=rtol)
        classification=classify_differences(diffs,expected.get(run_id,set()))
        rows.append({
            "run_id":run_id,
            "oracle":str(oracle_path),
            "difference_count":len(diffs),
            **classification,
            "differences":[
                {"path":d.path,"expected":d.expected,"actual":d.actual}
                for d in diffs
            ],
        })

    counts={}
    for row in rows:
        counts[row["status"]]=counts.get(row["status"],0)+1
    unexplained=sum(len(row["unexplained"]) for row in rows)
    missing_expected=sum(len(row["expected_not_observed"]) for row in rows)
    return {
        "schema":"lwkm-swp-multirun-regression-v1",
        "case_count":len(rows),
        "status_counts":counts,
        "unexplained_difference_paths":unexplained,
        "expected_difference_paths_not_observed":missing_expected,
        "admission_candidate":unexplained==0 and missing_expected==0,
        "cases":rows,
    }


def main(argv=None)->int:
    p=argparse.ArgumentParser(prog="regress-swp-cases")
    p.add_argument("--database",required=True,type=Path)
    p.add_argument("--legacy-template",required=True,type=Path)
    p.add_argument("--profile",required=True,type=Path)
    p.add_argument("--cases-root",required=True,type=Path)
    p.add_argument("--oracle-name",default="swap.swp")
    p.add_argument("--expected-differences",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--atol",type=float,default=1e-8)
    p.add_argument("--rtol",type=float,default=1e-8)
    a=p.parse_args(argv)

    try:
        result=regress_cases(
            database=a.database,
            legacy_template=a.legacy_template,
            profile_path=a.profile,
            cases_root=a.cases_root,
            expected_differences=a.expected_differences,
            oracle_name=a.oracle_name,
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
