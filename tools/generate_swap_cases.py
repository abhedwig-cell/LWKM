"""Content-addressed SWAP case artifact writer.

Scientific mapping is upstream. This writer only serializes an already
qualified case specification and records hashes, so templates can be replaced
without changing mapping semantics.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path

def write_text_if_changed(path:Path,text:str)->bool:
    data=text.encode("utf-8")
    if path.exists() and path.read_bytes()==data:return False
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data); return True

def render_case_stub(case:dict)->str:
    # Transitional artifact: not a claim of full SWP compatibility yet.
    lines=["# canonical LWKM SWAP case","[case]"]
    for k in sorted(case): lines.append(f"{k}={case[k]}")
    return "\n".join(lines)+"\n"

def write_case(root:Path,case:dict,dependency_hash:str)->dict:
    hru=int(case["HRU"]); d=root/f"hru-{hru:05d}"
    text=render_case_stub(case)
    changed=write_text_if_changed(d/"case.spec",text)
    manifest={"HRU":hru,"dependency_hash":dependency_hash,
              "case_spec_sha256":hashlib.sha256(text.encode()).hexdigest(),
              "changed":changed}
    write_text_if_changed(d/"manifest.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    return manifest
