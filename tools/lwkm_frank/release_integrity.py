"""Verify byte integrity of the original Frank v0.1 computational producers.

This validates source release identity, not LHM-run identity or numerical
equivalence to the completed 1991-2020 CSV. Standard library Python 3.8+.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

PRODUCERS = (
    "build_svat_base.py", "build_modflow_svat.py", "build_gxg_gg.py",
    "bereken_gw_percentielen.py", "export_msw_aanvulling.py",
    "derive_static_gt.py", "maak_gebied_n.py", "export_qmodf.py",
    "maak_svat_basis.py",
)
SHARED = ("wb10_reader.py", "wb01.py", "wb03_balance.py")

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def check(source_dir, manifest):
    evidence=json.loads(Path(manifest).read_text(encoding="utf8"))["files"]
    result=[]
    for file in (*PRODUCERS,*SHARED):
        path=Path(source_dir)/file
        actual=sha256(path) if path.is_file() else None
        expected=evidence.get(file)
        result.append({"file":file,"expected":expected,"actual":actual,
                       "valid":actual is not None and actual==expected})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    args=p.parse_args()
    rows=check(args.source_dir,args.manifest)
    for row in rows:
        print("PASS" if row["valid"] else "FAIL",row["file"])
    print("VALIDATED",sum(row["valid"] for row in rows),"/",len(rows))
    return 0 if all(row["valid"] for row in rows) else 2

if __name__=="__main__":sys.exit(main())
