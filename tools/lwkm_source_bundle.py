"""Create, verify and unpack portable LWKM source bundles.

The v2 bundle format supports a chain of LHM control files and content-addressed
payload deduplication. Collection remains explicit: callers provide a resolved
plan and this module never crawls an LHM installation to guess dependencies.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO


def _hash_stream(stream: BinaryIO) -> str:
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block)
    return h.hexdigest()


def sha256(path: Path) -> str:
    with Path(path).open("rb") as f:
        return _hash_stream(f)


@dataclass(frozen=True)
class Source:
    """Legacy v1 source entry kept for backwards compatibility."""

    logical_name: str
    source_path: str
    archive_path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ControlEntry:
    name: str
    source_path: str
    archive_path: str
    size: int
    sha256: str
    period: str | None = None


@dataclass(frozen=True)
class SourceEntry:
    logical_name: str
    source_class: str
    source_path: str
    object_path: str
    size: int
    sha256: str
    control_file: str | None = None
    period: str | None = None
    producer: str | None = None

    def manifest_dict(self) -> dict:
        d = asdict(self)
        d["class"] = d.pop("source_class")
        return d


def build_bundle(control: Path, resolved_sources: dict[str, Path], out_zip: Path, metadata: dict):
    """Build the historical single-control v1 bundle.

    Kept so existing callers do not change silently. New server collection
    should use :func:`build_bundle_from_plan`.
    """
    control = Path(control)
    entries = []
    for name, p in sorted(resolved_sources.items()):
        p = Path(p)
        if not p.is_file():
            raise FileNotFoundError(f"{name}: {p}")
        ap = f"sources/{name}/{p.name}"
        entries.append(Source(name, str(p), ap, p.stat().st_size, sha256(p)))
    manifest = {
        "schema": "lwkm-source-bundle-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "control_file": {"name": control.name, "sha256": sha256(control)},
        "metadata": metadata,
        "sources": [asdict(x) for x in entries],
    }
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.write(control, f"provenance/{control.name}")
        for e in entries:
            z.write(e.source_path, e.archive_path)
        z.writestr("manifest.json", json.dumps(manifest, indent=2))
    return manifest


def _resolve_plan_path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else base / p


def _validate_plan(plan: dict) -> None:
    if plan.get("schema") != "lwkm-source-plan-v1":
        raise ValueError("plan schema must be lwkm-source-plan-v1")
    controls = plan.get("controls")
    sources = plan.get("sources")
    if not isinstance(controls, list) or not controls:
        raise ValueError("plan.controls must be a non-empty list")
    if not isinstance(sources, list):
        raise ValueError("plan.sources must be a list")
    for i, item in enumerate(controls):
        if not isinstance(item, dict) or not item.get("path"):
            raise ValueError(f"plan.controls[{i}] requires path")
    seen = set()
    for i, item in enumerate(sources):
        if not isinstance(item, dict):
            raise ValueError(f"plan.sources[{i}] must be an object")
        for key in ("logical_name", "class", "path"):
            if not item.get(key):
                raise ValueError(f"plan.sources[{i}] requires {key}")
        identity = (item["logical_name"], item.get("period"), item.get("control_file"))
        if identity in seen:
            raise ValueError(f"duplicate logical source identity: {identity}")
        seen.add(identity)


def build_bundle_from_plan(plan_path: Path, out_zip: Path) -> dict:
    """Build one multi-period v2 bundle from an explicit resolved JSON plan."""
    plan_path = Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    _validate_plan(plan)
    base = plan_path.parent

    controls: list[ControlEntry] = []
    control_names: set[str] = set()
    for item in plan["controls"]:
        p = _resolve_plan_path(base, item["path"])
        if not p.is_file():
            raise FileNotFoundError(f"control: {p}")
        if p.name in control_names:
            raise ValueError(f"duplicate control basename: {p.name}")
        control_names.add(p.name)
        controls.append(
            ControlEntry(
                name=p.name,
                source_path=str(p),
                archive_path=f"provenance/control/{p.name}",
                size=p.stat().st_size,
                sha256=sha256(p),
                period=item.get("period"),
            )
        )

    sources: list[SourceEntry] = []
    objects: dict[str, dict] = {}
    object_sources: dict[str, Path] = {}
    for item in plan["sources"]:
        p = _resolve_plan_path(base, item["path"])
        if not p.is_file():
            raise FileNotFoundError(f"{item['logical_name']}: {p}")
        control_file = item.get("control_file")
        if control_file and control_file not in control_names:
            raise ValueError(
                f"source {item['logical_name']} refers to unknown control_file {control_file}"
            )
        digest = sha256(p)
        object_path = f"objects/{digest}"
        size = p.stat().st_size
        prior = objects.get(digest)
        if prior is not None and prior["size"] != size:
            raise ValueError(f"hash collision/size mismatch for {p}")
        objects[digest] = {"sha256": digest, "size": size, "archive_path": object_path}
        object_sources.setdefault(digest, p)
        sources.append(
            SourceEntry(
                logical_name=item["logical_name"],
                source_class=item["class"],
                source_path=str(p),
                object_path=object_path,
                size=size,
                sha256=digest,
                control_file=control_file,
                period=item.get("period"),
                producer=item.get("producer"),
            )
        )

    run_chain = plan.get("run_chain")
    manifest = {
        "schema": "lwkm-source-bundle-v2",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "plan_file": plan_path.name,
        "metadata": plan.get("metadata", {}),
        "controls": [asdict(x) for x in controls],
        "sources": [x.manifest_dict() for x in sources],
        "objects": [objects[k] for k in sorted(objects)],
        "run_chain_path": "provenance/run_chain.json" if run_chain is not None else None,
    }

    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for c in controls:
            z.write(c.source_path, c.archive_path)
        for digest, p in sorted(object_sources.items()):
            z.write(p, objects[digest]["archive_path"])
        z.writestr("provenance/collection_plan.json", json.dumps(plan, indent=2))
        if run_chain is not None:
            z.writestr("provenance/run_chain.json", json.dumps(run_chain, indent=2))
        z.writestr("manifest.json", json.dumps(manifest, indent=2))

    verify_bundle(out_zip)
    return manifest


def _hash_zip_member(z: zipfile.ZipFile, member: str) -> str:
    try:
        with z.open(member, "r") as f:
            return _hash_stream(f)
    except KeyError as exc:
        raise ValueError(f"missing bundle member: {member}") from exc


def _verify_v1(z: zipfile.ZipFile, manifest: dict) -> None:
    for e in manifest.get("sources", []):
        h = _hash_zip_member(z, e["archive_path"])
        if h != e["sha256"]:
            raise ValueError(f"hash mismatch: {e['logical_name']}")


def _verify_v2(z: zipfile.ZipFile, manifest: dict) -> None:
    object_map = {e["sha256"]: e for e in manifest.get("objects", [])}
    if len(object_map) != len(manifest.get("objects", [])):
        raise ValueError("duplicate object hash in manifest")

    for c in manifest.get("controls", []):
        h = _hash_zip_member(z, c["archive_path"])
        if h != c["sha256"]:
            raise ValueError(f"control hash mismatch: {c['name']}")

    verified_objects = set()
    for digest, obj in object_map.items():
        h = _hash_zip_member(z, obj["archive_path"])
        if h != digest:
            raise ValueError(f"object hash mismatch: {digest}")
        verified_objects.add(digest)

    for src in manifest.get("sources", []):
        digest = src["sha256"]
        if digest not in verified_objects:
            raise ValueError(f"source references unknown object: {src['logical_name']}")
        obj = object_map[digest]
        if src["object_path"] != obj["archive_path"] or src["size"] != obj["size"]:
            raise ValueError(f"source/object metadata mismatch: {src['logical_name']}")

    run_chain_path = manifest.get("run_chain_path")
    if run_chain_path and run_chain_path not in z.namelist():
        raise ValueError(f"missing bundle member: {run_chain_path}")


def verify_bundle(bundle: Path) -> dict:
    """Verify payload hashes and structural references, returning the manifest."""
    with zipfile.ZipFile(Path(bundle)) as z:
        try:
            manifest = json.loads(z.read("manifest.json"))
        except KeyError as exc:
            raise ValueError("missing manifest.json") from exc
        schema = manifest.get("schema")
        if schema == "lwkm-source-bundle-v1":
            _verify_v1(z, manifest)
        elif schema == "lwkm-source-bundle-v2":
            _verify_v2(z, manifest)
        else:
            raise ValueError(f"unsupported bundle schema: {schema}")
        return manifest


def unpack_bundle(bundle: Path, target: Path) -> dict:
    """Verify first, then extract into a new or empty immutable snapshot directory."""
    bundle = Path(bundle)
    target = Path(target)
    manifest = verify_bundle(bundle)
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"snapshot target is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    with zipfile.ZipFile(bundle) as z:
        for info in z.infolist():
            destination = (target / info.filename).resolve()
            if root not in destination.parents and destination != root:
                raise ValueError(f"unsafe bundle member path: {info.filename}")
        z.extractall(target)
    (target / ".lwkm-source-verified").write_text(
        json.dumps({"schema": manifest["schema"], "bundle": bundle.name}, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
