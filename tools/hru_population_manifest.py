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

def bind_source_hashes(manifest, sources):
    """Bind exact bytes of release membership, representative and soil context assets."""
    required=("membership","representatives","soil_context")
    if set(sources)!=set(required):
        raise ValueError("Require membership, representatives and soil_context")
    hashes={}
    for role,path in sorted(sources.items()):
        p=Path(path)
        if not p.is_file():
            raise FileNotFoundError(p)
        h=hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda:fh.read(1024*1024),b""):
                h.update(chunk)
        hashes[role]=h.hexdigest()
    identity=manifest["identity_sha256"]
    binding=hashlib.sha256(json.dumps({"identity":identity,"sources":hashes},
        sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {**manifest,"source_sha256":hashes,"release_binding_sha256":binding}

def verify_source_binding(manifest, sources):
    if not validate_membership(manifest,manifest["hru_ids"]):
        return False
    if "source_sha256" not in manifest or "release_binding_sha256" not in manifest:
        raise ValueError("Manifest lacks source binding")
    rebound=bind_source_hashes(manifest,sources)
    if rebound["source_sha256"]!=manifest["source_sha256"] or rebound["release_binding_sha256"]!=manifest["release_binding_sha256"]:
        raise ValueError("HRU release source identity mismatch")
    return True
