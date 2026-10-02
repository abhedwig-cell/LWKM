#!/usr/bin/env python3
"""LWKM W01 LHM-server provenance freeze, Q0-Q4.

Standard-library only. Designed for execution on the LHM server.

Q0: capture authoritative run/root identity.
Q1: inventory the versioned source specification without copying data.
Q2: copy selected files byte-for-byte to staging and hash every file.
Q3: create manifest-bearing ZIP and sidecar SHA-256.
Q4: fresh-extraction verification against the embedded manifest.

This tool qualifies collection integrity and file identity. It does not by
itself grant semantic production admission to every collected file.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import zipfile


SCHEMA_VERSION = 1
CLASS_DIR = {
    "A": "10_lhm_dynamic",
    "B": "20_lhm_static",
    "C": "30_lwkm_run_inputs",
    "D": "40_runtime_provenance",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def iso_utc_from_timestamp(value: float) -> str:
    return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


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
        "logical_id", "root_key", "provenance_class", "required_by", "filename_pattern",
        "path_hint", "required", "max_matches", "temporal_scope",
        "expected_format", "semantic_role",
    }
    if not rows:
        raise ValueError("Source specification is empty")
    missing_columns = required - set(rows[0])
    if missing_columns:
        raise ValueError(f"Source specification missing columns: {sorted(missing_columns)}")
    seen = set()
    for row in rows:
        logical_id = row["logical_id"].strip()
        if not logical_id:
            raise ValueError("Empty logical_id in source specification")
        if logical_id in seen:
            raise ValueError(f"Duplicate logical_id in source specification: {logical_id}")
        seen.add(logical_id)
        if row["provenance_class"].strip() not in CLASS_DIR:
            raise ValueError(f"Unknown provenance_class for {logical_id}")
        if not row["root_key"].strip():
            raise ValueError(f"Empty root_key for {logical_id}")
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
        stat = path.stat()
        roots[key] = {
            "path": str(path),
            "last_write_utc": iso_utc_from_timestamp(stat.st_mtime),
        }

    output_root = Path(args.output_root).resolve()
    manifest_dir = output_root / args.run_id / "00_manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    q0_path = manifest_dir / "q0-run.json"
    if q0_path.exists() and not args.force:
        raise FileExistsError(f"Q0 record already exists: {q0_path}; use --force only for intentional replacement")

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
        "procedure": "tools/server/lwkm_source_bundle.py",
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
    unknown_roots = sorted({item["root_key"].strip().upper() for item in spec} - set(roots))
    if unknown_roots:
        raise RuntimeError(f"Source spec references undefined Q0 root keys: {unknown_roots}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    indexes = {}
    indexed_file_count = 0
    for key, root in roots.items():
        files = index_files(root)
        indexed_file_count += len(files)
        indexed = []
        for path in files:
            rel = relative_posix(path, root)
            indexed.append((path, rel, rel.lower(), path.name.lower()))
        indexes[key] = indexed

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

    fieldnames = [
        "logical_id", "source_root_key", "provenance_class", "required_by", "semantic_role",
        "expected_format", "temporal_scope", "source_path",
        "source_relative_path", "size_bytes", "last_write_utc", "selected",
        "q1_item_status", "qualification_status",
    ]
    inventory_path = output_dir / "q1-inventory.csv"
    with inventory_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
        "source_spec_sha256": sha256_file(spec_path),
        "inventory_file": str(inventory_path),
        "inventory_sha256": sha256_file(inventory_path),
        "indexed_file_count": indexed_file_count,
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
    if not roots:
        raise RuntimeError("Q0 contains no roots")

    bundle_root = Path(args.bundle_root).resolve()
    if bundle_root.exists() and any(bundle_root.iterdir()) and not args.force:
        raise FileExistsError(f"Bundle root is not empty: {bundle_root}; choose a clean directory")
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
        if cls not in CLASS_DIR:
            raise RuntimeError(f"Unknown provenance class in Q1 inventory: {cls}")

        before = source.stat()
        source_hash = sha256_file(source)
        after_hash = source.stat()
        if before.st_size != after_hash.st_size or before.st_mtime_ns != after_hash.st_mtime_ns:
            raise RuntimeError(f"Source changed while hashing: {source}")

        rel = Path(row["source_relative_path"])
        target_rel = Path(CLASS_DIR[cls]) / root_key / rel
        target = bundle_root / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

        after_copy_source = source.stat()
        if before.st_size != after_copy_source.st_size or before.st_mtime_ns != after_copy_source.st_mtime_ns:
            raise RuntimeError(f"Source changed during collection: {source}")

        staged_hash = sha256_file(target)
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

    manifest_path = manifest_dir / "files.csv"
    fields = [
        "logical_id", "source_root_key", "provenance_class", "required_by", "semantic_role",
        "expected_format", "temporal_scope", "original_source_path",
        "source_relative_path", "bundle_relative_path", "size_bytes",
        "source_last_write_utc", "sha256", "qualification_status",
    ]
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest_rows)

    q2_summary = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q2",
        "status": "Q2_STAGED_BYTE_IDENTITY_PASS",
        "run_id": q0_data["run_id"],
        "bundle_root": str(bundle_root),
        "file_count": len(manifest_rows),
        "total_bytes": sum(int(r["size_bytes"]) for r in manifest_rows),
        "files_manifest": "00_manifest/files.csv",
        "files_manifest_sha256": sha256_file(manifest_path),
        "captured_utc": utc_now(),
    }
    write_json(manifest_dir / "q2-summary.json", q2_summary)
    print(json.dumps(q2_summary, indent=2))
    return 0


def q3(args: argparse.Namespace) -> int:
    bundle_root = Path(args.bundle_root).resolve()
    manifest_path = bundle_root / "00_manifest" / "files.csv"
    q2_path = bundle_root / "00_manifest" / "q2-summary.json"
    if not manifest_path.is_file() or not q2_path.is_file():
        raise RuntimeError("Q3 requires a complete Q2 staging directory")

    q2_summary = read_json(q2_path)
    if q2_summary.get("status") != "Q2_STAGED_BYTE_IDENTITY_PASS":
        raise RuntimeError("Q3 refuses because Q2 status is not PASS")

    archive = Path(args.zip_path).resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists() and not args.force:
        raise FileExistsError(f"ZIP already exists: {archive}")

    collection = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q3",
        "status": "Q3_ARCHIVE_CONSTRUCTION_IN_PROGRESS",
        "run_id": q2_summary["run_id"],
        "bundle_directory_name": bundle_root.name,
        "file_count": q2_summary["file_count"],
        "total_bytes": q2_summary["total_bytes"],
        "files_manifest_sha256": sha256_file(manifest_path),
        "archive_name": archive.name,
        "created_utc": utc_now(),
        "note": "Archive SHA-256 is intentionally stored in the external sidecar to avoid circular self-identity.",
    }
    collection_path = bundle_root / "00_manifest" / "collection.json"
    write_json(collection_path, collection)

    compression = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(archive, "w", compression=compression, allowZip64=True) as zf:
        for path in sorted(p for p in bundle_root.rglob("*") if p.is_file()):
            zf.write(path, path.relative_to(bundle_root).as_posix())

    zip_hash = sha256_file(archive)
    sidecar = archive.with_suffix(archive.suffix + ".sha256")
    sidecar.write_text(f"{zip_hash}  {archive.name}\n", encoding="ascii")

    q3_report = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q3",
        "status": "Q3_ARCHIVE_CONSTRUCTION_PASS",
        "run_id": q2_summary["run_id"],
        "archive": str(archive),
        "archive_size_bytes": archive.stat().st_size,
        "archive_sha256": zip_hash,
        "files_manifest_sha256": sha256_file(manifest_path),
        "sidecar": str(sidecar),
        "created_utc": utc_now(),
    }
    write_json(archive.with_suffix(archive.suffix + ".q3.json"), q3_report)
    print(json.dumps(q3_report, indent=2))
    return 0


def q4(args: argparse.Namespace) -> int:
    archive = Path(args.zip_path).resolve()
    if not archive.is_file():
        raise FileNotFoundError(archive)
    archive_hash = sha256_file(archive)

    failures = []
    with tempfile.TemporaryDirectory(prefix="lwkm_q4_") as td:
        extract_root = Path(td)
        with zipfile.ZipFile(archive, "r") as zf:
            bad_crc = zf.testzip()
            if bad_crc is not None:
                failures.append(f"ZIP CRC failure: {bad_crc}")
            zf.extractall(extract_root)

        manifest_path = extract_root / "00_manifest" / "files.csv"
        if not manifest_path.is_file():
            failures.append("Missing embedded 00_manifest/files.csv")
            manifest_rows = []
        else:
            with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
                manifest_rows = list(csv.DictReader(f))

        for row in manifest_rows:
            target = extract_root / Path(row["bundle_relative_path"])
            if not target.is_file():
                failures.append(f"Missing extracted file: {row['bundle_relative_path']}")
                continue
            if target.stat().st_size != int(row["size_bytes"]):
                failures.append(f"Size mismatch: {row['bundle_relative_path']}")
                continue
            actual_hash = sha256_file(target)
            if actual_hash.lower() != row["sha256"].lower():
                failures.append(f"SHA-256 mismatch: {row['bundle_relative_path']}")

        expected_paths = {Path(r["bundle_relative_path"]).as_posix() for r in manifest_rows}
        actual_data_paths = set()
        for path in extract_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(extract_root).as_posix()
            if not rel.startswith("00_manifest/"):
                actual_data_paths.add(rel)
        extras = sorted(actual_data_paths - expected_paths)
        missing_manifest_entries = sorted(expected_paths - actual_data_paths)
        for rel in extras:
            failures.append(f"Undeclared data file in archive: {rel}")
        for rel in missing_manifest_entries:
            failures.append(f"Manifest entry missing from archive: {rel}")

    status = "LHM_SOURCE_Q4_IMMUTABLE_SNAPSHOT" if not failures else "Q4_FAIL"
    report = {
        "schema_version": SCHEMA_VERSION,
        "gate": "Q4",
        "status": status,
        "archive": str(archive),
        "archive_sha256": archive_hash,
        "verified_manifest_rows": len(manifest_rows),
        "failure_count": len(failures),
        "failures": failures,
        "verified_utc": utc_now(),
        "semantic_admission_caveat": "Q4 proves collection integrity and identity, not automatic semantic production admission of every member.",
    }
    report_path = archive.with_suffix(archive.suffix + ".q4.json")
    write_json(report_path, report)
    print(json.dumps(report, indent=2))
    return 0 if not failures else 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("q0", help="Capture authoritative run/root identity")
    p.add_argument("--root", action="append", required=True,
                   help="Declared root as KEY=PATH; repeat, e.g. RUN=D:\\LHMrun and PROJECT=D:\\LWKM")
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

    p = sub.add_parser("q1", help="Inventory source specification without copying")
    p.add_argument("--q0", required=True)
    p.add_argument("--spec", required=True)
    p.add_argument("--output-dir", required=True)
    p.set_defaults(func=q1)

    p = sub.add_parser("q2", help="Stage and hash Q1-selected files")
    p.add_argument("--q0", required=True)
    p.add_argument("--q1-summary", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--spec")
    p.add_argument("--bundle-root", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=q2)

    p = sub.add_parser("q3", help="Create immutable manifest-bearing ZIP")
    p.add_argument("--bundle-root", required=True)
    p.add_argument("--zip-path", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=q3)

    p = sub.add_parser("q4", help="Verify ZIP by fresh extraction and hashes")
    p.add_argument("--zip-path", required=True)
    p.set_defaults(func=q4)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
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
