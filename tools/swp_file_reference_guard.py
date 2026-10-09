"""Explicit W11 SWAP file-reference preflight.

Reads active assignment lines for a versioned set of file-reference keys.
Unknown semantics are not inferred. Does not claim complete SWAP parsing.
"""
from __future__ import annotations
import re
from pathlib import Path

DEFAULT_FILE_KEYS=("METFIL","DRFIL","BBCFIL")
# Other file-bearing SWP symbols require explicit versioned profile authority.
ASSIGN=re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*(?:[!*].*)?$")


def extract_references(swp_text, *, file_keys=DEFAULT_FILE_KEYS, required_keys=()):
    keys=set(file_keys)
    if not keys or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*",k) for k in keys):
        raise ValueError("invalid file reference key policy")
    seen={}
    for line in swp_text.splitlines():
        stripped=line.lstrip()
        if not stripped or stripped[0] in ("*","!"):
            continue
        m=ASSIGN.match(line)
        if not m or m.group(1) not in keys:
            continue
        key=m.group(1)
        if key in seen:
            raise ValueError(f"duplicate SWP file assignment: {key}")
        value=m.group(2).strip().strip("'\"")
        if not value:
            raise ValueError(f"empty SWP file reference: {key}")
        path=Path(value)
        if path.is_absolute() or ".." in path.parts or len(path.parts)!=1 or "\\" in value or "/" in value:
            raise ValueError(f"unsafe SWP file reference: {key}={value}")
        seen[key]=value
    missing=set(required_keys)-set(seen)
    if missing:
        raise ValueError(f"missing required SWP file assignments: {sorted(missing)}")
    return seen


def required_package_assets(swp_text, *, file_keys=DEFAULT_FILE_KEYS, required_keys=()):
    return sorted({"swap.swp",*extract_references(
        swp_text,file_keys=file_keys,required_keys=required_keys
    ).values()})
