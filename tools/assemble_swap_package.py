"""W11 immutable per-HRU package candidate assembly.

Only copies declared qualified assets. Does not run SWAP, regenerate scientific
inputs, or imply W10/W11 admission. Writes an atomic directory on the same
filesystem; refuses unqualified source assets and path traversal.
"""
from __future__ import annotations
import hashlib,json,os,shutil,tempfile
from pathlib import Path
from tools.swp_file_reference_guard import required_package_assets


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def assemble(run_id,assets,output_root,*,profile_id,code_commit,required_assets=None):
    """assets: filename -> {path, sha256, qualification_id}."""
    run_id=str(run_id)
    if not run_id or not run_id.isdecimal():
        raise ValueError("run_id must be a nonnegative numeric identifier")
    if not profile_id or not code_commit:
        raise ValueError("profile and code commit are required")
    if not {"swap.swp"}.issubset(assets):
        raise ValueError("missing swap.swp")
    if not assets:
        raise ValueError("empty package")
    swp_source=Path(assets["swap.swp"]["path"])
    if not swp_source.is_file():
        raise FileNotFoundError(swp_source)
    derived=set(required_package_assets(swp_source.read_text(encoding="utf-8")))
    if required_assets is not None:
        derived.update(required_assets)
    if derived:
        missing=derived-set(assets)
        if missing:
            raise ValueError(f"missing required referenced assets: {sorted(missing)}")
    target=Path(output_root)/f"run_{int(run_id):05d}"
    root=Path(output_root)
    root.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix=".lwkm-package-",dir=root))
    try:
        manifest={}
        for name,meta in sorted(assets.items()):
            relative=Path(name)
            if relative.is_absolute() or ".." in relative.parts or len(relative.parts)!=1 or name in (".",""):
                raise ValueError(f"unsafe package asset name: {name}")
            if name=="manifest.json":
                raise ValueError("reserved package asset name")
            if not all(meta.get(k) for k in ("path","sha256","qualification_id")):
                raise ValueError(f"unqualified package asset: {name}")
            source=Path(meta["path"])
            if not source.is_file():
                raise FileNotFoundError(source)
            actual=sha256(source)
            if actual.lower()!=str(meta["sha256"]).lower():
                raise ValueError(f"source SHA mismatch: {name}")
            shutil.copyfile(source,staging/name)
            if sha256(staging/name)!=actual:
                raise ValueError(f"copy identity mismatch: {name}")
            manifest[name]={"sha256":actual,"qualification_id":meta["qualification_id"]}
        result={"schema_version":1,"status":"PACKAGE_CANDIDATE_NOT_ADMITTED",
                "run_id":int(run_id),"profile_id":profile_id,
                "code_commit":code_commit,"assets":manifest}
        (staging/"manifest.json").write_text(
            json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        if target.exists():
            raise FileExistsError(f"immutable package already exists: {target}")
        os.replace(staging,target)
        return result
    finally:
        if staging.exists():
            shutil.rmtree(staging)
