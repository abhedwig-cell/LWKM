#!/usr/bin/env python3
"""W01 orchestrator for the LWKM LHM-server provenance freeze.

Standard-library only. This front-end performs Q0-Q2 and delegates the actual
portable ZIP format and internal verification to tools.lwkm_source_bundle.

Q0: capture explicit named source roots and run identity.
Q1: inventory the versioned source specification without copying data.
Q2: stage selected files byte-for-byte, hash them, and emit a resolved bundle plan.
Q3: build the tested content-addressed LWKM source bundle.
Q4: verify and fresh-extract the bundle, then re-hash extracted objects.

Collection integrity is not the same as semantic production admission.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile

from tools import lwkm_source_bundle as bundle


SCHEMA_VERSION = 1
CLASS_DIR = {
    "A": "10_lhm_dynamic",
    "B": "20_lhm_static",
    "C": "30_lwkm_run_inputs",
    "D": "40_runtime_provenance",
}
BUNDLE_CLASS = {
    "A": "run_output",
    "B": "static_input",
    "C": "lwkm_run_input",
    "D": "runtime_provenance",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def iso_utc_from_timestamp(value: float) -> str:
    return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_bool(text: str) -> bool:
    return str(text).strip().lower() in {"1", "true", "yes", "y"}


def normalize_hint(text: str) -> str:
    return str(text or "").replace("\\", "/").strip("/").lower()


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def index_files(root: Path) -> list[Path]:
    files = []
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "$RECYCLE.BIN", "System Volume Information"}]
        for name in names:
            files.append(Path(base) / name)
    return files


def load_spec(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {
        "logical_id", "root_key", "provenance_class", "required_by",
        "filename_pattern", "path_hint", "required", "max_matches",
        "temporal_scope", "expected_format", "semantic_role",
    }
    if not rows:
        raise ValueError("Source specification is empty")
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"Source specification missing columns: {sorted(missing)}")
    seen = set()
    for row in rows:
        logical_id = row["logical_id"].strip()
        if not logical_id:
            raise ValueError("Empty logical_id in source specification")
        if logical_id in seen:
            raise ValueError(f"Duplicate logical_id in source specification: {logical_id}")
        seen.add(logical_id)
        if not row["root_key"].strip():
            raise ValueError(f"Empty root_key for {logical_id}")
        if row["provenance_class"].strip() not in CLASS_DIR:
            raise ValueError(f"Unknown provenance_class for {logical_id}")
        if not row["filename_pattern"].strip():
            raise ValueError(f"Empty filename_pattern for {logical_id}")
    return rows


def q0(args: argparse.Namespace) -> int:
    roots = {}
    for raw in args.root:
        if "=" not in raw:
            raise ValueError(f"--root must be KEY=PATH, got: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip().upper()
        if not key:
            raise ValueError(f"Empty root key in: {raw}")
        if key in roots:
            raise ValueError(f"Duplicate root key: {key}")
        path = Path(value.strip()).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"Root {key} does not exist or is not a directory: {path}")
        roots[key] = {
            "path": str(path),
            "last_write_utc": iso_utc_from_timestamp(path.stat().st_mtime),
        }

    output_root = Path(args.output_root).resolve()
    manifest_dir = output_root / args.run_id / "00_manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    q0_path = manifest_dir / "q0-run.json"
    if q0_path.exists() and not args.force:
        raise FileExistsError(f"Q0 record already exists: {q0_path}")

    obj = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q0",
        "status": "Q0_RUN_IDENTITY_CAPTURED_NOT_YET_ADMITTED",
        "run_id": args.run_id,
        "server_hostname": socket.gethostname(),
        "roots": roots,
        "model_version": args.model_version,
        "simulation_start": args.simulation_start,
        "simulation_end": args.simulation_end,
        "completed_run_assertion": bool(args.completed_run),
        "restart_history": args.restart_history,
        "notes": args.notes,
        "collection_operator": os.environ.get("USERNAME") or os.environ.get("USER") or "unknown",
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "captured_utc": utc_now(),
        "procedure": "tools/server/lwkm_w01.py",
    }
    write_json(q0_path, obj)
    print(json.dumps({
        "gate": "Q0",
        "status": obj["status"],
        "q0": str(q0_path),
        "roots": {k: v["path"] for k, v in roots.items()},
    }, indent=2))
    return 0


def q1(args: argparse.Namespace) -> int:
    q0_data = read_json(Path(args.q0))
    roots = {}
    for key, record in q0_data.get("roots", {}).items():
        path = Path(record["path"]).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"Q0 root {key} is no longer available: {path}")
        roots[key.upper()] = path
    if not roots:
        raise RuntimeError("Q0 contains no roots")

    spec_path = Path(args.spec).resolve()
    spec = load_spec(spec_path)
    unknown = sorted({r["root_key"].strip().upper() for r in spec} - set(roots))
    if unknown:
        raise RuntimeError(f"Source spec references undefined Q0 root keys: {unknown}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    indexes = {}
    indexed_count = 0
    for key, root in roots.items():
        files = index_files(root)
        indexed_count += len(files)
        indexes[key] = [
            (p, relative_posix(p, root), relative_posix(p, root).lower(), p.name.lower())
            for p in files
        ]

    inventory_rows = []
    summary_items = []
    missing_required = []
    ambiguous = []

    for item in spec:
        logical_id = item["logical_id"].strip()
        root_key = item["root_key"].strip().upper()
        pattern = item["filename_pattern"].strip().lower()
        hint = normalize_hint(item["path_hint"])
        required = parse_bool(item["required"])
        max_matches = int(item["max_matches"]) if item["max_matches"].strip() else None

        matches = []
        for path, rel, rel_lower, name_lower in indexes[root_key]:
            if not fnmatch.fnmatch(name_lower, pattern):
                continue
            if hint and hint not in rel_lower:
                continue
            matches.append((path, rel))
        matches.sort(key=lambda x: x[1].lower())

        if required and not matches:
            item_status = "MISSING_REQUIRED"
            missing_required.append(logical_id)
        elif not matches:
            item_status = "OPTIONAL_NOT_FOUND"
        elif max_matches is not None and len(matches) > max_matches:
            item_status = "AMBIGUOUS_TOO_MANY_MATCHES"
            ambiguous.append(logical_id)
        else:
            item_status = "RESOLVED"

        selected = item_status == "RESOLVED"
        summary_items.append({
            "logical_id": logical_id,
            "root_key": root_key,
            "status": item_status,
            "match_count": len(matches),
            "required": required,
            "max_matches": max_matches,
        })

        for path, rel in matches:
            stat = path.stat()
            inventory_rows.append({
                "logical_id": logical_id,
                "source_root_key": root_key,
                "provenance_class": item["provenance_class"].strip(),
                "required_by": item["required_by"].strip(),
                "semantic_role": item["semantic_role"].strip(),
                "expected_format": item["expected_format"].strip(),
                "temporal_scope": item["temporal_scope"].strip(),
                "source_path": str(path),
                "source_relative_path": rel,
                "size_bytes": stat.st_size,
                "last_write_utc": iso_utc_from_timestamp(stat.st_mtime),
                "selected": str(selected).lower(),
                "q1_item_status": item_status,
                "qualification_status": "RECOVERED_UNQUALIFIED",
            })

    fields = [
        "logical_id", "source_root_key", "provenance_class", "required_by",
        "semantic_role", "expected_format", "temporal_scope", "source_path",
        "source_relative_path", "size_bytes", "last_write_utc", "selected",
        "q1_item_status", "qualification_status",
    ]
    inventory_path = output_dir / "q1-inventory.csv"
    with inventory_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(inventory_rows)

    status = "Q1_PASS" if not missing_required and not ambiguous else "Q1_FAIL"
    summary = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q1",
        "status": status,
        "run_id": q0_data["run_id"],
        "roots": {k: str(v) for k, v in roots.items()},
        "source_spec": str(spec_path),
        "source_spec_sha256": bundle.sha256(spec_path),
        "inventory_file": str(inventory_path),
        "inventory_sha256": bundle.sha256(inventory_path),
        "indexed_file_count": indexed_count,
        "matched_file_rows": len(inventory_rows),
        "missing_required": missing_required,
        "ambiguous": ambiguous,
        "items": summary_items,
        "captured_utc": utc_now(),
    }
    write_json(output_dir / "q1-summary.json", summary)
    shutil.copy2(spec_path, output_dir / spec_path.name)
    print(json.dumps({
        "gate": "Q1",
        "status": status,
        "inventory": str(inventory_path),
        "missing_required": missing_required,
        "ambiguous": ambiguous,
    }, indent=2))
    return 0 if status == "Q1_PASS" else 2


def q2(args: argparse.Namespace) -> int:
    q0_data = read_json(Path(args.q0))
    q1_summary = read_json(Path(args.q1_summary))
    if q1_summary.get("status") != "Q1_PASS":
        raise RuntimeError("Q2 refuses to run because Q1 is not PASS")

    inventory_path = Path(args.inventory).resolve()
    with inventory_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    selected = [r for r in rows if parse_bool(r["selected"])]
    if not selected:
        raise RuntimeError("No selected Q1 files to collect")

    roots = {
        key.upper(): Path(record["path"]).resolve()
        for key, record in q0_data.get("roots", {}).items()
    }
    bundle_root = Path(args.bundle_root).resolve()
    if bundle_root.exists() and any(bundle_root.iterdir()) and not args.force:
        raise FileExistsError(f"Bundle root is not empty: {bundle_root}")
    bundle_root.mkdir(parents=True, exist_ok=True)
    manifest_dir = bundle_root / "00_manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(Path(args.q0), manifest_dir / "q0-run.json")
    shutil.copy2(Path(args.q1_summary), manifest_dir / "q1-summary.json")
    shutil.copy2(inventory_path, manifest_dir / "q1-inventory.csv")
    if args.spec:
        shutil.copy2(Path(args.spec), manifest_dir / Path(args.spec).name)

    manifest_rows = []
    for row in selected:
        source = Path(row["source_path"]).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Selected source disappeared: {source}")
        root_key = row["source_root_key"].strip().upper()
        if root_key not in roots:
            raise RuntimeError(f"Q1 inventory references undefined Q0 root: {root_key}")
        source_root = roots[root_key]
        try:
            source.relative_to(source_root)
        except ValueError as exc:
            raise RuntimeError(f"Selected source escaped Q0 root {root_key}: {source}") from exc

        cls = row["provenance_class"]
        before = source.stat()
        source_hash = bundle.sha256(source)
        after_hash = source.stat()
        if before.st_size != after_hash.st_size or before.st_mtime_ns != after_hash.st_mtime_ns:
            raise RuntimeError(f"Source changed while hashing: {source}")

        rel = Path(row["source_relative_path"])
        target_rel = Path(CLASS_DIR[cls]) / root_key / rel
        target = bundle_root / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

        after_copy = source.stat()
        if before.st_size != after_copy.st_size or before.st_mtime_ns != after_copy.st_mtime_ns:
            raise RuntimeError(f"Source changed during collection: {source}")
        staged_hash = bundle.sha256(target)
        if source_hash != staged_hash:
            raise RuntimeError(f"Hash mismatch after copy: {source} -> {target}")

        manifest_rows.append({
            "logical_id": row["logical_id"],
            "source_root_key": root_key,
            "provenance_class": cls,
            "required_by": row["required_by"],
            "semantic_role": row["semantic_role"],
            "expected_format": row["expected_format"],
            "temporal_scope": row["temporal_scope"],
            "original_source_path": str(source),
            "source_relative_path": row["source_relative_path"],
            "bundle_relative_path": target_rel.as_posix(),
            "size_bytes": before.st_size,
            "source_last_write_utc": iso_utc_from_timestamp(before.st_mtime),
            "sha256": source_hash,
            "qualification_status": "PROVENANCE_BOUND",
        })

    files_manifest = manifest_dir / "files.csv"
    fields = [
        "logical_id", "source_root_key", "provenance_class", "required_by",
        "semantic_role", "expected_format", "temporal_scope",
        "original_source_path", "source_relative_path", "bundle_relative_path",
        "size_bytes", "source_last_write_utc", "sha256",
        "qualification_status",
    ]
    with files_manifest.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest_rows)

    control_rows = [r for r in manifest_rows if r["logical_id"] == "HRU_SWAP_CONTROL"]
    if len(control_rows) != 1:
        raise RuntimeError("Q2 requires exactly one selected HRU_SWAP_CONTROL to bind the bundle plan")
    control_name = Path(control_rows[0]["bundle_relative_path"]).name
    period = "-".join(filter(None, [q0_data.get("simulation_start"), q0_data.get("simulation_end")]))

    plan = {
        "schema": "lwkm-source-plan-v1",
        "metadata": {
            "run_id": q0_data["run_id"],
            "server_hostname": q0_data.get("server_hostname"),
            "roots": q0_data.get("roots", {}),
            "model_version": q0_data.get("model_version"),
            "simulation_start": q0_data.get("simulation_start"),
            "simulation_end": q0_data.get("simulation_end"),
            "source_spec_sha256": q1_summary.get("source_spec_sha256"),
            "q1_inventory_sha256": q1_summary.get("inventory_sha256"),
            "files_manifest_sha256": bundle.sha256(files_manifest),
            "qualification_status": "PROVENANCE_BOUND",
        },
        "controls": [{
            "path": str((bundle_root / control_rows[0]["bundle_relative_path"]).resolve()),
            "period": period or None,
        }],
        "sources": [],
        "run_chain": {
            "run_id": q0_data["run_id"],
            "period": period or None,
            "q0": "00_manifest/q0-run.json",
            "q1": "00_manifest/q1-summary.json",
            "files_manifest": "00_manifest/files.csv",
        },
    }
    for i, row in enumerate(sorted(manifest_rows, key=lambda r: (r["logical_id"], r["bundle_relative_path"]))):
        if row["logical_id"] == "HRU_SWAP_CONTROL":
            continue
        staged = (bundle_root / row["bundle_relative_path"]).resolve()
        plan["sources"].append({
            "logical_name": f"{row['logical_id']}::{i:06d}",
            "class": BUNDLE_CLASS[row["provenance_class"]],
            "path": str(staged),
            "control_file": control_name,
            "period": period or None,
            "producer": "W01_Q2_BYTE_IDENTICAL_STAGING",
        })

    plan_path = manifest_dir / "resolved-bundle-plan.json"
    write_json(plan_path, plan)
    q2_summary = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q2",
        "status": "Q2_STAGED_BYTE_IDENTITY_PASS",
        "run_id": q0_data["run_id"],
        "bundle_root": str(bundle_root),
        "file_count": len(manifest_rows),
        "total_bytes": sum(int(r["size_bytes"]) for r in manifest_rows),
        "files_manifest": str(files_manifest),
        "files_manifest_sha256": bundle.sha256(files_manifest),
        "resolved_bundle_plan": str(plan_path),
        "resolved_bundle_plan_sha256": bundle.sha256(plan_path),
        "captured_utc": utc_now(),
    }
    write_json(manifest_dir / "q2-summary.json", q2_summary)
    print(json.dumps(q2_summary, indent=2))
    return 0


def q3(args: argparse.Namespace) -> int:
    plan = Path(args.plan).resolve()
    archive = Path(args.zip_path).resolve()
    if archive.exists() and not args.force:
        raise FileExistsError(f"ZIP already exists: {archive}")
    manifest = bundle.build_bundle_from_plan(plan, archive)
    archive_hash = bundle.sha256(archive)
    sidecar = Path(str(archive) + ".sha256")
    sidecar.write_text(f"{archive_hash}  {archive.name}\n", encoding="ascii")
    report = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q3",
        "status": "Q3_ARCHIVE_CONSTRUCTION_PASS",
        "archive": str(archive),
        "archive_sha256": archive_hash,
        "bundle_schema": manifest["schema"],
        "object_count": len(manifest.get("objects", [])),
        "source_count": len(manifest.get("sources", [])),
        "sidecar": str(sidecar),
        "created_utc": utc_now(),
    }
    write_json(Path(str(archive) + ".q3.json"), report)
    print(json.dumps(report, indent=2))
    return 0


def q4(args: argparse.Namespace) -> int:
    archive = Path(args.zip_path).resolve()
    if not archive.is_file():
        raise FileNotFoundError(archive)
    manifest = bundle.verify_bundle(archive)
    failures = []
    with tempfile.TemporaryDirectory(prefix="lwkm_q4_") as td:
        snapshot = Path(td) / "snapshot"
        bundle.unpack_bundle(archive, snapshot)
        for obj in manifest.get("objects", []):
            extracted = snapshot / obj["archive_path"]
            if not extracted.is_file():
                failures.append(f"Missing extracted object: {obj['archive_path']}")
                continue
            if extracted.stat().st_size != obj["size"]:
                failures.append(f"Size mismatch: {obj['archive_path']}")
                continue
            if bundle.sha256(extracted) != obj["sha256"]:
                failures.append(f"SHA-256 mismatch: {obj['archive_path']}")

    status = "LHM_SOURCE_Q4_IMMUTABLE_SNAPSHOT" if not failures else "Q4_FAIL"
    report = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q4",
        "status": status,
        "archive": str(archive),
        "archive_sha256": bundle.sha256(archive),
        "bundle_schema": manifest["schema"],
        "verified_object_count": len(manifest.get("objects", [])),
        "failure_count": len(failures),
        "failures": failures,
        "verified_utc": utc_now(),
        "semantic_admission_caveat":
            "Q4 proves collection integrity and identity, not automatic semantic production admission of every member.",
    }
    write_json(Path(str(archive) + ".q4.json"), report)
    print(json.dumps(report, indent=2))
    return 0 if not failures else 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("q0")
    p.add_argument("--root", action="append", required=True,
                   help="Named root KEY=PATH; repeat, e.g. RUN=D:\\LHMrun PROJECT=D:\\LWKM")
    p.add_argument("--output-root", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--model-version", default="")
    p.add_argument("--simulation-start", default="")
    p.add_argument("--simulation-end", default="")
    p.add_argument("--restart-history", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--completed-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=q0)

    p = sub.add_parser("q1")
    p.add_argument("--q0", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--output-dir", required=True)
    p.set_defaults(func=q1)

    p = sub.add_parser("q2")
    p.add_argument("--q0", required=True)
    p.add_argument("--q1-summary", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--spec")
    p.add_argument("--bundle-root", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=q2)

    p = sub.add_parser("q3")
    p.add_argument("--plan", required=True)
    p.add_argument("--zip-path", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=q3)

    p = sub.add_parser("q4")
    p.add_argument("--zip-path", required=True)
    p.set_defaults(func=q4)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "command": args.command,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, indent=2), file=sys.stderr)
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
