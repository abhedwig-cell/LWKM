"""CLI facade for NHI/LHM -> LWKM source transfer.

Two collection routes are supported:
1. build from an already resolved explicit plan;
2. resolve that plan from authoritative LHM control files plus a versioned
   transfer profile, then immediately build and verify the bundle.

The collector never performs scientific post-processing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from tools.lwkm_source_bundle import build_bundle_from_plan, unpack_bundle, verify_bundle
from tools.lwkm_source_plan import build_plan
from tools.lhm_upstream_qualification import qualify


def _summary(manifest: dict) -> dict:
    controls = manifest.get("controls")
    if controls is None and manifest.get("control_file") is not None:
        controls = [manifest["control_file"]]
    return {
        "schema": manifest["schema"],
        "controls": len(controls or []),
        "sources": len(manifest.get("sources", [])),
        "objects": len(manifest.get("objects", [])),
    }


def _write_json(path:Path,data:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2),encoding="utf-8")


def cmd_plan(args):
    plan=build_plan(Path(args.controls),Path(args.profile))
    _write_json(Path(args.output),plan)
    print(json.dumps({
        "schema":plan["schema"],
        "controls":len(plan["controls"]),
        "sources":len(plan["sources"]),
        "output":str(Path(args.output)),
    },indent=2))
    return 0


def cmd_collect(args):
    if args.plan:
        manifest = build_bundle_from_plan(Path(args.plan), Path(args.output))
    else:
        if not args.controls or not args.profile:
            raise ValueError("collect requires either --plan or both --controls and --profile")
        plan=build_plan(Path(args.controls),Path(args.profile))
        if args.write_plan:
            _write_json(Path(args.write_plan),plan)
        with tempfile.TemporaryDirectory(prefix="lwkm-source-") as td:
            resolved=Path(td)/"resolved_collection_plan.json"
            _write_json(resolved,plan)
            manifest=build_bundle_from_plan(resolved,Path(args.output))
    print(json.dumps(_summary(manifest), indent=2))
    return 0


def cmd_qualify(args):
    result=qualify(Path(args.controls),Path(args.profile))
    q4={"status":"PENDING","reason":"bundle not supplied"}
    if args.bundle:
        if result["qualified_through"]!="Q3":
            q4={"status":"NOT_REACHED","reason":"Q0-Q3 not fully passed"}
        else:
            try:
                manifest=verify_bundle(Path(args.bundle))
                q4={"status":"PASS","bundle":_summary(manifest)}
                result["qualified_through"]="Q4"
                result["q4_ready_for_bundle_gate"]=True
            except Exception as exc:
                q4={"status":"FAIL","error":str(exc)}
    result["q4"]=q4
    if args.output:
        _write_json(Path(args.output),result)
    print(json.dumps(result,indent=2))
    return 0 if all(g["status"]=="PASS" for g in result["gates"]) and q4["status"] in {"PASS","PENDING"} else 1


def cmd_verify(args):
    m=verify_bundle(Path(args.bundle))
    print(json.dumps(_summary(m),indent=2))
    return 0


def cmd_unpack(args):
    m=unpack_bundle(Path(args.bundle),Path(args.target))
    print(json.dumps({**_summary(m),"target":str(Path(args.target))},indent=2))
    return 0


def cmd_inspect(args):
    import zipfile
    with zipfile.ZipFile(args.bundle) as z:
        m=json.loads(z.read("manifest.json"))
    print(json.dumps(m,indent=2))
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(prog="lwkm-source")
    s=p.add_subparsers(dest="cmd",required=True)

    pl=s.add_parser("plan",help="resolve an explicit collection plan from LHM controls")
    pl.add_argument("--controls",required=True)
    pl.add_argument("--profile",required=True)
    pl.add_argument("--output",required=True)
    pl.set_defaults(fn=cmd_plan)

    c=s.add_parser("collect",help="build and verify a source bundle")
    src=c.add_mutually_exclusive_group(required=True)
    src.add_argument("--plan",help="already resolved JSON collection plan")
    src.add_argument("--controls",help="LHM control file or directory/tree")
    c.add_argument("--profile",help="required with --controls")
    c.add_argument("--write-plan",help="optional path to persist the resolved plan")
    c.add_argument("--output",required=True)
    c.set_defaults(fn=cmd_collect)

    q=s.add_parser("qualify",help="evaluate Q0-Q3 and optionally the Q4 bundle gate")
    q.add_argument("--controls",required=True)
    q.add_argument("--profile",required=True)
    q.add_argument("--bundle",help="optional verified bundle for Q4")
    q.add_argument("--output",help="optional JSON qualification report")
    q.set_defaults(fn=cmd_qualify)

    v=s.add_parser("verify")
    v.add_argument("bundle")
    v.set_defaults(fn=cmd_verify)

    u=s.add_parser("unpack")
    u.add_argument("bundle")
    u.add_argument("--target",required=True)
    u.set_defaults(fn=cmd_unpack)

    i=s.add_parser("inspect")
    i.add_argument("bundle")
    i.set_defaults(fn=cmd_inspect)

    a=p.parse_args(argv)
    return a.fn(a)


if __name__=="__main__":
    raise SystemExit(main())
