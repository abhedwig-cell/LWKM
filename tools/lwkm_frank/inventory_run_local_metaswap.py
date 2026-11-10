"""Inventory run-local MetaSWAP inputs, without substituting global model installation.

Run-local candidates are evidence of run-specific state. An active INI/control
binding remains necessary to establish which candidates were actually opened.
Read-only; standard library; Windows Deltaforge Python compatible.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

RUN_RE = re.compile(r"^run_(19|20)\d{2}_(19|20)\d{2}(?:_.*)?$", re.I)
NAMES = ("area_svat.inp", "mod2svat.inp", "scap_svat.inp",
         "dldra_svat.inp", "dqsat_svat.inp", "idf_svat.inp")
MAX_MATCHES = 100

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def discover(runs_root, names=NAMES):
    rows = []
    for run_dir in sorted(runs_root.iterdir(), key=lambda p: p.name.lower()):
        if not run_dir.is_dir() or not RUN_RE.fullmatch(run_dir.name):
            continue
        msw = run_dir / "metaswap"
        for name in names:
            matches = sorted((p for p in msw.rglob(name) if p.is_file()),
                             key=lambda p: str(p).lower()) if msw.is_dir() else []
            if len(matches) > MAX_MATCHES:
                raise ValueError("Too many matches for %s %s" % (run_dir, name))
            if not matches:
                rows.append(dict(run=run_dir.name, logical_file=name, relative_path="",
                                 full_path="", size_bytes="", sha256="",
                                 status="MISSING_RUN_LOCAL"))
            else:
                for path in matches:
                    rows.append(dict(run=run_dir.name, logical_file=name,
                                     relative_path=str(path.relative_to(run_dir)),
                                     full_path=str(path), size_bytes=path.stat().st_size,
                                     sha256=sha256(path),
                                     status=("CANDIDATE_MULTIPLE_RUN_LOCAL" if len(matches)>1
                                             else "CANDIDATE_RUN_LOCAL")))
    return rows

def write(runs_root, output):
    rows = discover(runs_root)
    output.mkdir(parents=True, exist_ok=True)
    names = ("run","logical_file","relative_path","full_path","size_bytes","sha256","status")
    with (output / "lhm_run_metaswap_input_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=names);writer.writeheader();writer.writerows(rows)
    by_name = {}
    for row in rows:
        by_name.setdefault(row["logical_file"], {}).setdefault(row["sha256"] or "<missing>", []).append(row["run"])
    summary = {
        "schema_version":1,
        "authority":"RUN_LOCAL_METASWAP_INPUT_CANDIDATES",
        "run_root":str(runs_root),
        "run_count":len({r["run"] for r in rows}),
        "records":len(rows),
        "missing":sum(r["status"]=="MISSING_RUN_LOCAL" for r in rows),
        "multiple":sum(r["status"]=="CANDIDATE_MULTIPLE_RUN_LOCAL" for r in rows),
        "hashes_by_logical_file":by_name,
        "caveats":[
            "Run-local file presence is not proof that the actual LHM executable opened this path.",
            "Bind effective input paths to run-local INI/launch and restart configuration.",
            "No implicit fallback to E:\\LHM_4.3.3\\Data\\2_Model_Input.",
            "Do not mix overlapping MS_daily or alternative run variants by directory name alone."
        ]
    }
    (output / "lhm_run_metaswap_input_inventory.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if not args.runs_root.is_dir():
        parser.error("Runs root does not exist: "+str(args.runs_root))
    result=write(args.runs_root,args.out)
    print("Runs:",result["run_count"],"records:",result["records"],
          "missing:",result["missing"],"multiple:",result["multiple"])
    return 0 if result["run_count"] else 2

if __name__=="__main__":sys.exit(main())
