"""CLI facade for NHI/LHM -> LWKM source transfer.

Collection requires an explicit resolved plan. The command never crawls an LHM
installation and never guesses scientific dependencies.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.lwkm_source_bundle import build_bundle_from_plan, unpack_bundle, verify_bundle


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


def cmd_collect(args):
    manifest = build_bundle_from_plan(Path(args.plan), Path(args.output))
    print(json.dumps(_summary(manifest), indent=2))
    return 0


def cmd_verify(args):
    manifest = verify_bundle(Path(args.bundle))
    print(json.dumps(_summary(manifest), indent=2))
    return 0


def cmd_unpack(args):
    manifest = unpack_bundle(Path(args.bundle), Path(args.target))
    print(json.dumps({**_summary(manifest), "target": str(Path(args.target))}, indent=2))
    return 0


def cmd_inspect(args):
    import zipfile

    with zipfile.ZipFile(args.bundle) as z:
        manifest = json.loads(z.read("manifest.json"))
    print(json.dumps(manifest, indent=2))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="lwkm-source")
    s = p.add_subparsers(dest="cmd", required=True)

    c = s.add_parser("collect", help="build and verify a bundle from a resolved JSON plan")
    c.add_argument("--plan", required=True)
    c.add_argument("--output", required=True)
    c.set_defaults(fn=cmd_collect)

    v = s.add_parser("verify", help="verify hashes and bundle structure")
    v.add_argument("bundle")
    v.set_defaults(fn=cmd_verify)

    u = s.add_parser("unpack", help="verify and extract to a new/empty snapshot directory")
    u.add_argument("bundle")
    u.add_argument("--target", required=True)
    u.set_defaults(fn=cmd_unpack)

    i = s.add_parser("inspect", help="print manifest without extracting the bundle")
    i.add_argument("bundle")
    i.set_defaults(fn=cmd_inspect)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
