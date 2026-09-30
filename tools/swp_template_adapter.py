"""Canonicalize the recovered historical LWKM SWP template contract.

The historical SWAPtools create_SWAP path did more than raw Mustache
substitution. This adapter makes the observed serialization-only effects
explicit so the Python renderer can reproduce them deterministically.

No scientific values are decided here.
"""
from __future__ import annotations

import re
from copy import deepcopy


TABLE_HEADERS={
    "TABLE_CROPROTATION":"    CROPSTART     CROPEND       CROPNAME        CROPFIL  CROPTYPE",
    "TABLE_SOILPROFILE":"   ISUBLAY  ISOILLAY  HSUBLAY  NCOMP",
    "TABLE_SOILHYDRFUNC":"   ORES      OSAT      ALFA      NPAR   KSATFIT      LEXP  H_ENPR   KSATEXM     BDENS      ELAS",
    "TABLE_SOILTEXTURES":"   PSAND  PSILT  PCLAY  ORGMAT",
}

# Exact observed active defaults in the recovered historical swap_wwl.swp.
# Parameterization removes hidden template policy; values come from typed
# context/profile after this transformation.
PARAMETERIZE_DEFAULTS={
    "SWETR":"0",
    "SWWBA":"0",
    "PERIOD":"0",
    "SWAUN":"2",
    "SWODAT":"1",
}


def _insert_table_header(text:str,section:str,header:str)->str:
    marker="{{#"+section+"}}"
    if marker not in text:
        raise ValueError(f"missing template section {section}")
    # Idempotent when already canonicalized.
    prefix=header+"\n"+marker
    if prefix in text:
        return text
    if header in text:
        raise ValueError(f"header for {section} exists outside canonical position")
    return text.replace(marker,prefix,1)


def _parameterize_scalar(text:str,name:str,expected_default:str)->str:
    token="{{"+name+"}}"
    # Already parameterized is fine, but reject duplicate active assignments.
    active_token=re.compile(
        rf"(?m)^\s*{re.escape(name)}\s*=\s*{re.escape(token)}(?:\s*!.*)?$"
    )
    if active_token.search(text):
        return text

    pattern=re.compile(
        rf"(?m)^(\s*{re.escape(name)}\s*=\s*)"
        rf"{re.escape(expected_default)}(\s*!.*)$"
    )
    text,n=pattern.subn(rf"\1{token}\2",text,count=1)
    if n!=1:
        raise ValueError(
            f"expected exactly one active {name}={expected_default} assignment"
        )
    return text


def canonicalize_legacy_template(template:str)->str:
    text=template
    for section,header in TABLE_HEADERS.items():
        text=_insert_table_header(text,section,header)
    for name,default in PARAMETERIZE_DEFAULTS.items():
        text=_parameterize_scalar(text,name,default)
    return text


def apply_render_profile(context:dict,profile:dict)->dict:
    """Apply serialization/output policy without changing scientific fields."""
    ctx=deepcopy(context)
    output=profile.get("renderer_output",{})
    for key in ("SWWBA","PERIOD","SWAUN","SWODAT","INLIST_CSV"):
        if key in output:
            ctx[key]=output[key]
    missing=[k for k in ("SWWBA","PERIOD","SWAUN","SWODAT","INLIST_CSV") if k not in ctx]
    if missing:
        raise ValueError(f"renderer output profile unresolved: {missing}")
    return ctx
