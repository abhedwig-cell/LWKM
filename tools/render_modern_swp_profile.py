"""W10 explicit modern SWP profile preflight.

No historical template is assumed. Profile files declare the template SHA and
required context symbols. This gate validates identity and resolved symbols
before calling the existing strict SWP renderer. It is not a SWAP parser gate.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from tools.swp_renderer import render_text

SYMBOL=re.compile(r"{{\s*[#/]?([A-Za-z0-9_]+)\s*}}")


def render_profile(template_path,profile_path,context):
    template_path=Path(template_path)
    profile=json.loads(Path(profile_path).read_text(encoding="utf-8"))
    if profile.get("schema_version")!=1 or not profile.get("profile_id"):
        raise ValueError("invalid modern SWP profile")
    text=template_path.read_text(encoding="utf-8")
    digest=hashlib.sha256(template_path.read_bytes()).hexdigest()
    if digest!=profile.get("template_sha256"):
        raise ValueError("SWP template SHA mismatch")
    required=profile.get("required_context")
    if not isinstance(required,list) or not all(isinstance(k,str) for k in required):
        raise ValueError("SWP required_context must be an array of names")
    missing=sorted(set(required)-set(context))
    if missing:
        raise ValueError(f"missing required SWP context: {missing}")
    if profile.get("production_admitted") is True:
        raise ValueError("profile cannot self-declare production admission")
    rendered=render_text(text,context)
    if not rendered.strip():
        raise ValueError("empty rendered SWP")
    return rendered,{"profile_id":profile["profile_id"],
                     "template_sha256":digest,
                     "status":"MODERN_SWP_RENDER_CANDIDATE_NOT_ADMITTED"}
