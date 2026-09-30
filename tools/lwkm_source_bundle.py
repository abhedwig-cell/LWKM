"""Create and verify a portable LWKM source bundle from resolved LHM sources."""
from __future__ import annotations
import hashlib,json,zipfile
from dataclasses import dataclass,asdict
from pathlib import Path
from datetime import datetime,timezone

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

@dataclass(frozen=True)
class Source:
    logical_name:str
    source_path:str
    archive_path:str
    size:int
    sha256:str

def build_bundle(control:Path,resolved_sources:dict[str,Path],out_zip:Path,metadata:dict):
    entries=[]
    for name,p in sorted(resolved_sources.items()):
        p=Path(p)
        if not p.is_file(): raise FileNotFoundError(f"{name}: {p}")
        ap=f"sources/{name}/{p.name}"
        entries.append(Source(name,str(p),ap,p.stat().st_size,sha256(p)))
    manifest={
      "schema":"lwkm-source-bundle-v1",
      "created_utc":datetime.now(timezone.utc).isoformat(),
      "control_file":{"name":control.name,"sha256":sha256(control)},
      "metadata":metadata,
      "sources":[asdict(x) for x in entries],
    }
    out_zip.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out_zip,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(control,f"provenance/{control.name}")
        for e in entries:z.write(e.source_path,e.archive_path)
        z.writestr("manifest.json",json.dumps(manifest,indent=2))
    return manifest

def verify_bundle(bundle:Path):
    with zipfile.ZipFile(bundle) as z:
        m=json.loads(z.read("manifest.json"))
        for e in m["sources"]:
            h=hashlib.sha256(z.read(e["archive_path"])).hexdigest()
            if h!=e["sha256"]: raise ValueError(f"hash mismatch: {e['logical_name']}")
        return m
