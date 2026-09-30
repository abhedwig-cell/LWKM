"""CLI facade for NHI/LHM -> LWKM source transfer.

Collection deliberately requires an explicit resolved plan. It never crawls
the server and guesses what might be useful.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from tools.lwkm_source_bundle import verify_bundle

def cmd_verify(args):
    m=verify_bundle(Path(args.bundle))
    print(json.dumps({"schema":m["schema"],"sources":len(m["sources"]),
                      "control":m["control_file"]},indent=2))
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
    v=s.add_parser("verify"); v.add_argument("bundle"); v.set_defaults(fn=cmd_verify)
    i=s.add_parser("inspect"); i.add_argument("bundle"); i.set_defaults(fn=cmd_inspect)
    a=p.parse_args(argv)
    return a.fn(a)

if __name__=="__main__": raise SystemExit(main())
