"""Qualify an upstream LHM run tree for LWKM source use.

This module checks execution/provenance fitness only. It does not assess
hydrological correctness and does not take ownership of restart mechanics.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
import re
from typing import Any

from tools.lwkm_source_plan import build_plan, discover_controls, _period

DATE8=re.compile(r"(?<!\d)(\d{8})(?!\d)")


@dataclass(frozen=True)
class Gate:
    level:str
    status:str
    details:dict[str,Any]


def _dates_in_name(path:Path)->list[date]:
    out=[]
    for token in DATE8.findall(path.name):
        try:
            out.append(date(int(token[:4]),int(token[4:6]),int(token[6:8])))
        except ValueError:
            continue
    return out


def _q0_q1(controls_root:Path)->tuple[Gate,Gate,list[Path]]:
    try:
        controls=discover_controls(Path(controls_root))
    except Exception as exc:
        fail=Gate("Q0","FAIL",{"error":str(exc)})
        return fail,Gate("Q1","NOT_REACHED",{}),[]
    q0=Gate("Q0","PASS",{"control_count":len(controls),"controls":[p.name for p in controls]})
    periods=[{"control":p.name,"start":_period(p)[0],"end":_period(p)[1]} for p in controls]
    # discover_controls already rejects gaps/overlaps.
    q1=Gate("Q1","PASS",{
        "periods":periods,
        "start_year":periods[0]["start"],
        "end_year":periods[-1]["end"],
    })
    return q0,q1,controls


def _q2(controls_root:Path,profile:Path)->tuple[Gate,dict|None]:
    try:
        plan=build_plan(Path(controls_root),Path(profile))
    except Exception as exc:
        return Gate("Q2","FAIL",{"error":str(exc)}),None
    by_class={}
    for src in plan["sources"]:
        by_class[src["class"]]=by_class.get(src["class"],0)+1
    return Gate("Q2","PASS",{
        "source_count":len(plan["sources"]),
        "by_class":by_class,
        "control_count":len(plan["controls"]),
    }),plan


def _q3(plan:dict|None)->Gate:
    if plan is None:
        return Gate("Q3","NOT_REACHED",{})

    run_outputs=[x for x in plan["sources"] if x["class"]=="run_output"]
    zero=[]
    missing=[]
    period_dates:dict[str,list[date]]={}
    period_files:dict[str,int]={}

    for src in run_outputs:
        p=Path(src["path"])
        if not p.exists():
            missing.append(str(p))
            continue
        if p.stat().st_size<=0:
            zero.append(str(p))
        period=src.get("period")
        if period:
            period_files[period]=period_files.get(period,0)+1
            period_dates.setdefault(period,[]).extend(_dates_in_name(p))

    if missing or zero:
        return Gate("Q3","FAIL",{
            "missing_files":missing,
            "zero_byte_files":zero,
            "run_output_count":len(run_outputs),
        })

    end_checks=[]
    dated_periods=0
    for period in plan.get("run_chain",{}).get("periods",[]):
        label=f"{period['start_year']}-{period['end_year']}"
        dates=period_dates.get(label,[])
        expected=date(period["end_year"],12,31)
        if dates:
            dated_periods+=1
            latest=max(dates)
            end_checks.append({
                "period":label,
                "expected_end":expected.isoformat(),
                "latest_dated_output":latest.isoformat(),
                "passes":latest>=expected,
            })
        else:
            end_checks.append({
                "period":label,
                "expected_end":expected.isoformat(),
                "latest_dated_output":None,
                "passes":None,
            })

    failed_end=[x for x in end_checks if x["passes"] is False]
    if failed_end:
        return Gate("Q3","FAIL",{
            "run_output_count":len(run_outputs),
            "period_end_checks":end_checks,
            "reason":"dated run outputs do not reach one or more period ends",
        })

    if dated_periods==0:
        return Gate("Q3","PARTIAL",{
            "run_output_count":len(run_outputs),
            "period_end_checks":end_checks,
            "reason":"required files are nonzero, but filenames provide no timestamp evidence",
        })

    unknown=[x for x in end_checks if x["passes"] is None]
    status="PASS" if not unknown else "PARTIAL"
    return Gate("Q3",status,{
        "run_output_count":len(run_outputs),
        "period_end_checks":end_checks,
        "periods_with_timestamp_evidence":dated_periods,
        "periods_without_timestamp_evidence":len(unknown),
        "note":"log/exit-code evidence may strengthen Q3 but is not inferred here",
    })


def qualify(controls_root:Path,profile:Path)->dict:
    q0,q1,_controls=_q0_q1(Path(controls_root))
    if q0.status!="PASS":
        gates=[q0,q1,Gate("Q2","NOT_REACHED",{}),Gate("Q3","NOT_REACHED",{})]
    else:
        q2,plan=_q2(Path(controls_root),Path(profile))
        q3=_q3(plan) if q2.status=="PASS" else Gate("Q3","NOT_REACHED",{})
        gates=[q0,q1,q2,q3]

    qualified_through="NONE"
    for g in gates:
        if g.status=="PASS":
            qualified_through=g.level
        else:
            break
    return {
        "schema":"lwkm-upstream-run-qualification-v1",
        "controls_root":str(Path(controls_root)),
        "profile":str(Path(profile)),
        "qualified_through":qualified_through,
        "q4_ready_for_bundle_gate":qualified_through=="Q3",
        "gates":[asdict(g) for g in gates],
    }
