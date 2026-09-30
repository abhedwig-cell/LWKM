"""Resolve an explicit LWKM source collection plan from LHM control files.

The controls are provenance authority for configured inputs. The transfer
profile is authority for what LWKM is allowed to collect. This module does not
perform scientific post-processing and does not copy restart payloads.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import re
from typing import Any

import yaml

from tools.lhm_run_chain_provenance import compare_controls, meteo_year_dependencies, parse

PERIOD_RE=re.compile(r"control_run_(\d{4})[_-](\d{4})\.ini$",re.I)


def _period(path:Path)->tuple[int,int]:
    m=PERIOD_RE.search(path.name)
    if not m:
        raise ValueError(f"Cannot derive run period from control filename: {path.name}")
    start,end=map(int,m.groups())
    if end<start:
        raise ValueError(f"Invalid period in {path.name}: {start}-{end}")
    return start,end


def discover_controls(root:Path)->list[Path]:
    root=Path(root)
    if root.is_file():
        controls=[root]
    else:
        controls=sorted(root.rglob("control_run_*.ini"))
    if not controls:
        raise FileNotFoundError(f"No control_run_*.ini files under {root}")
    controls.sort(key=lambda p:(_period(p)[0],_period(p)[1],str(p)))
    seen=[]
    prev_end=None
    for p in controls:
        start,end=_period(p)
        if prev_end is not None:
            if start<=prev_end:
                raise ValueError(f"Overlapping control periods around {p.name}")
            if start!=prev_end+1:
                raise ValueError(
                    f"Gap in control periods: previous ends {prev_end}, next starts {start}"
                )
        seen.append((start,end))
        prev_end=end
    return controls


def load_profile(path:Path)->dict:
    data=yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or data.get("schema_version")!=1:
        raise ValueError("Unsupported transfer profile schema")
    if "classes" not in data:
        raise ValueError("Transfer profile has no classes")
    return data


def _last_values(control:Path)->dict[str,Any]:
    out={}
    for item in parse(control):
        out[item.key.lower()]=item
    return out


def _strip_quotes(value:str)->str:
    value=value.strip()
    if len(value)>=2 and value[0]==value[-1] and value[0] in ("'",'"'):
        return value[1:-1]
    return value


def _configured_path(control:Path,value:str)->Path:
    raw=_strip_quotes(value)
    p=Path(raw)
    if p.is_absolute():
        return p
    # On the authoritative Windows server, drive-qualified paths are absolute
    # even though they are not interpreted as such on POSIX test runners.
    if re.match(r"^[A-Za-z]:[\\/]",raw):
        return Path(raw)
    return (control.parent/p).resolve()


def _pattern_regex(pattern:str)->re.Pattern:
    # Profile patterns use a single YYYY placeholder and otherwise literal
    # control-key characters.
    escaped=re.escape(pattern).replace("YYYY",r"(?P<year>\d{4})")
    return re.compile("^"+escaped+"$",re.I)


def _run_root(control:Path,run_cfg:dict)->Path:
    mode=run_cfg.get("base","find_ancestor")
    markers=run_cfg.get("markers",["modflow/results","metaswap/svat_per"])
    if mode=="control_parent":
        return control.parent
    if mode!="find_ancestor":
        raise ValueError(f"Unsupported run_output.base: {mode}")
    for root in (control.parent,*control.parent.parents):
        if all((root/marker).exists() for marker in markers):
            return root
    raise FileNotFoundError(
        f"Cannot locate LHM run root for {control}; expected markers {markers}"
    )


def _add_source(
    sources:list[dict],
    *,
    logical_name:str,
    source_class:str,
    path:Path,
    control:Path,
    period:str|None=None,
    producer:str|None=None,
)->None:
    if not Path(path).is_file():
        raise FileNotFoundError(f"{logical_name}: {path}")
    item={
        "logical_name":logical_name,
        "class":source_class,
        "path":str(Path(path).resolve()),
        "control_file":control.name,
    }
    if period is not None:
        item["period"]=period
    if producer is not None:
        item["producer"]=producer
    sources.append(item)


def build_plan(controls_root:Path,profile_path:Path)->dict:
    controls=discover_controls(Path(controls_root))
    profile=load_profile(Path(profile_path))
    classes=profile["classes"]
    static_keys=[str(x).lower() for x in classes.get("static_input",{}).get("keys",[])]
    period_patterns=classes.get("period_input",{}).get("key_patterns",[])
    period_regexes=[(_pattern_regex(p),p) for p in period_patterns]
    run_cfg=classes.get("run_output",{})
    output_specs=run_cfg.get("patterns",[])
    if not output_specs:
        raise ValueError("Transfer profile must declare explicit run_output.patterns")

    sources=[]
    control_records=[]
    periods=[]
    for control in controls:
        start,end=_period(control)
        period=f"{start}-{end}"
        periods.append({"control_file":control.name,"start_year":start,"end_year":end})
        control_records.append({"path":str(control.resolve()),"period":period})
        values=_last_values(control)

        for key in static_keys:
            v=values.get(key)
            if v is None or v.resolved is None:
                raise ValueError(f"{control.name}: unresolved/missing static key {key}")
            _add_source(
                sources,
                logical_name=key,
                source_class="static_input",
                path=_configured_path(control,v.resolved),
                control=control,
                period=period,
                producer="LHM_CONTROL",
            )

        # Every configured meteo family must exist once for every year in this
        # control period. Extra years in a control are ignored by this period.
        matched:dict[tuple[str,int],Any]={}
        for key,v in values.items():
            for rx,profile_pattern in period_regexes:
                m=rx.match(key)
                if not m:
                    continue
                year=int(m.group("year"))
                if start<=year<=end:
                    family=profile_pattern.replace("YYYY","").rstrip("_").lower()
                    matched[(family,year)]=v
        families=[p.replace("YYYY","").rstrip("_").lower() for p in period_patterns]
        for year in range(start,end+1):
            for family in families:
                v=matched.get((family,year))
                if v is None or v.resolved is None:
                    raise ValueError(
                        f"{control.name}: missing period input {family}_{year}"
                    )
                _add_source(
                    sources,
                    logical_name=f"{family}_{year}",
                    source_class="period_input",
                    path=_configured_path(control,v.resolved),
                    control=control,
                    period=period,
                    producer="LHM_CONTROL",
                )

        run_root=_run_root(control,run_cfg)
        for spec in output_specs:
            if not isinstance(spec,dict) or not spec.get("id") or not spec.get("glob"):
                raise ValueError("Each run_output pattern requires id and glob")
            matches=sorted(run_root.glob(spec["glob"]))
            if spec.get("required",True) and not matches:
                raise FileNotFoundError(
                    f"{control.name}: required run output {spec['id']} matched nothing "
                    f"under {run_root} with {spec['glob']}"
                )
            for p in matches:
                if not p.is_file():
                    continue
                rel=p.relative_to(run_root).as_posix()
                _add_source(
                    sources,
                    logical_name=f"{spec['id']}:{rel}",
                    source_class="run_output",
                    path=p,
                    control=control,
                    period=period,
                    producer=spec.get("producer","LHM_RUN_OUTPUT"),
                )

    chain=compare_controls(controls)
    chain["periods"]=periods
    chain["meteo_by_year"]=meteo_year_dependencies(controls)
    chain["restart_payload_included"]=bool(
        classes.get("restart",{}).get("include_payload",False)
    )

    return {
        "schema":"lwkm-source-plan-v1",
        "controls":control_records,
        "sources":sources,
        "run_chain":chain,
        "metadata":{
            "transfer_profile":profile.get("profile"),
            "profile_schema_version":profile.get("schema_version"),
            "restart_payload_included":chain["restart_payload_included"],
            "collector_policy":profile.get("policy",{}),
        },
    }
