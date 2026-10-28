"""Version-specific HRU identity manifest; count never determines ID range."""
import csv, hashlib, json
from pathlib import Path

def build_manifest(ids, *, release, source_path=None):
    values=[int(v) for v in ids]
    if not values or any(v<=0 for v in values) or len(set(values))!=len(values):
        raise ValueError("HRU IDs must be positive, unique and nonempty")
    ordered=sorted(values)
    payload="".join(str(v)+"\n" for v in ordered).encode()
    return {"schema_version":1,"release":str(release),"n_hrus":len(ordered),
            "hru_ids":ordered,"identity_sha256":hashlib.sha256(payload).hexdigest(),
            "source":str(source_path) if source_path is not None else None}

def validate_membership(manifest, ids):
    actual=set(int(v) for v in ids)
    expected=set(manifest["hru_ids"])
    if actual!=expected:
        raise ValueError(f"HRU identity mismatch: missing={sorted(expected-actual)[:20]}, unexpected={sorted(actual-expected)[:20]}")
    if len(manifest["hru_ids"])!=manifest["n_hrus"]:
        raise ValueError("Manifest count inconsistent")
    if build_manifest(manifest["hru_ids"],release=manifest["release"])["identity_sha256"]!=manifest["identity_sha256"]:
        raise ValueError("Manifest identity digest mismatch")
    return True

def write_manifest(ids,output,release,source_path=None):
    manifest=build_manifest(ids,release=release,source_path=source_path)
    Path(output).write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest
