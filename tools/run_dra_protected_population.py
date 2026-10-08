"""HRU-agnostic, fail-closed DRA compression runner (aggregated-input stage).

Consumes one JSON document with physical-system parameters per HRU, applies the
protected hydraulic selector, and writes an atomic, reproducible qualification
bundle. This is NOT the upstream raster aggregator or a SWAP DRA renderer.

Input:
{"schema_version":1,"hrus":[{"hru":"101","systems":[{
 "source_id":"P","hydraulic_class":"infiltration_capable_open",
 "medium":"open_channel","drainage_conductance":0.1,
 "infiltration_conductance":0.05,"dep":1.0,
 "peil_sum":0.5,"peil_win":0.7,"dd":40.0}]}]}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from tools.dra_level_compression import PhysicalDrainageSystem, to_render_level
from tools.dra_protected_compression import select_protected_candidate

ALGORITHM_VERSION="protected-compression-v1"


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def physical(raw):
    required=("source_id","hydraulic_class","medium","drainage_conductance",
              "infiltration_conductance","dep","peil_sum","peil_win","dd")
    missing=set(required)-set(raw)
    if missing:
        raise ValueError(f"missing physical fields: {sorted(missing)}")
    gd=float(raw["drainage_conductance"])
    gi=float(raw["infiltration_conductance"])
    if not (0<=gd and 0<=gi):
        raise ValueError("negative conductance")
    from math import isfinite
    if not all(isfinite(float(raw[k])) for k in required[3:]):
        raise ValueError("non-finite physical input")
    if gd==0 and gi>0:
        raise ValueError("infiltration without drainage conductance")
    series=raw.get("level_series")
    if series is not None:
        series=tuple((str(t),float(v)) for t,v in series)
    return PhysicalDrainageSystem(
        source_ids=(str(raw["source_id"]),),
        hydraulic_class=str(raw["hydraulic_class"]),
        medium=str(raw["medium"]),
        drnres=1/gd if gd else 100000.,
        infres=1/gi if gi else 100000.,
        dep=float(raw["dep"]),
        peil_sum=float(raw["peil_sum"]),
        peil_win=float(raw["peil_win"]),
        dd=float(raw["dd"]),
        level_series=series,
        drainage_conductance_raw=gd,
        infiltration_conductance_raw=gi,
        physical_active=gd>0,
    )


def atomic_json(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".pending-",suffix=".json",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            f.write(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def run(source:Path,output:Path,*,regional_limit=0.10,surface_limit=0.02):
    payload=json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema_version")!=1 or not isinstance(payload.get("hrus"),list):
        raise ValueError("expected schema_version=1 and hrus array")
    cfg={"algorithm":ALGORITHM_VERSION,"regional_limit_m":regional_limit,
         "surface_limit_m":surface_limit}
    if regional_limit<0 or surface_limit<0:
        raise ValueError("negative error limit")
    old={}
    manifest_path=output/"qualification.json"
    if manifest_path.exists():
        try:
            prior=json.loads(manifest_path.read_text(encoding="utf-8"))
            if prior.get("config")==cfg:
                old={str(x["hru"]):x for x in prior.get("results",[])
                     if x.get("status") in ("CANDIDATE_NOT_ADMITTED","NO_COMPRESSION")}
        except (ValueError,KeyError,TypeError):
            old={}
    ids=set()
    results=[]
    for item in payload["hrus"]:
        hid=str(item["hru"])
        if hid in ids: raise ValueError(f"duplicate HRU: {hid}")
        ids.add(hid)
        systems=item["systems"]
        if not isinstance(systems,list): raise ValueError("systems must be an array")
        # Canonical order makes input row permutations fingerprint-identical.
        ordered=sorted(systems,key=lambda x:str(x["source_id"]))
        fingerprint=digest({"config":cfg,"systems":ordered})
        previous=old.get(hid)
        if previous and previous.get("fingerprint")==fingerprint:
            results.append(previous)
            continue
        try:
            physicals=[physical(x) for x in ordered]
            levels,audit=select_protected_candidate(
                physicals,regional_error_limit_m=regional_limit,
                surface_error_limit_m=surface_limit)
            # This is a parser-bound preflight, not SWAP rendering.
            rendered=[to_render_level(x) for x in levels]
            record={"hru":hid,"fingerprint":fingerprint,
                    "status":audit["status"],"audit":audit,
                    "levels":[{"source_ids":list(x["source_ids"]),
                               "drnres":x["drnres"],"infres":x["infres"],
                               "dd":x["dd"],"dep":x["dep"],
                               "peil_sum":x["peil_sum"],"peil_win":x["peil_win"],
                               "medium":x["medium"],
                               "allow_infiltration":x["allow_infiltration"],
                               "level_series":x["level_series"]}
                              for x in rendered]}
        except (ValueError,AssertionError,KeyError,TypeError) as exc:
            record={"hru":hid,"fingerprint":fingerprint,
                    "status":"FAIL_CLOSED","error":str(exc)}
        results.append(record)
    results.sort(key=lambda x:x["hru"])
    failed=sum(x["status"]=="FAIL_CLOSED" for x in results)
    report={"schema_version":1,"status":"QUALIFICATION_PASS" if not failed else "QUALIFICATION_FAIL",
            "config":cfg,"input_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "hru_count":len(results),"failed_hru_count":failed,"results":results}
    atomic_json(manifest_path,report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--regional-limit-m",type=float,default=.10)
    p.add_argument("--surface-limit-m",type=float,default=.02)
    a=p.parse_args()
    result=run(a.input,a.output_dir,regional_limit=a.regional_limit_m,
               surface_limit=a.surface_limit_m)
    print(json.dumps({k:result[k] for k in ("status","hru_count","failed_hru_count")}))
    return 1 if result["failed_hru_count"] else 0

if __name__=="__main__":
    raise SystemExit(main())
