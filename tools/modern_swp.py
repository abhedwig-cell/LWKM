"""Explicit candidate adapter for recovered Template/wwl.swp, not legacy replay.

Scientific field values come from typed workbook contexts. The finite policy
below is versioned separately from historical oracle equivalence. Production
admission requires hydrological qualification of all upstream components.
"""
import hashlib
import re
from copy import deepcopy
from tools.swp_renderer import render_text
from tools.swp_template_adapter import TABLE_HEADERS

SOURCE_SHA256 = "ee0c23696fd5565a4b99eb81ce469a1be7c86494cfb20545dfba492820a5858a"
PROFILE_ID = "LWKM_CURRENT_TEMPLATE_CANDIDATE_20261019"
POLICY = {"LAT": 52.1, "ALT": 1.9, "ALTW": 10.0, "DTMAX": .04,
          "INLIST_CSV": "'WATBAL,ETTERMS,GWL'",
          "SWSOLU": 0, "SWITCH_SWSOLU_OPTION_1": False,
          "SINAVE": -.02, "SINAMP": 0., "SINMAX": 90.}


def prepare_template(source_bytes):
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError("current template SHA mismatch")
    text = source_bytes.decode("utf-8-sig").replace("\r\n", "\n")
    for name, header in TABLE_HEADERS.items():
        marker = "{{#" + name + "}}"
        if text.count(marker) != 1:
            raise ValueError(f"missing/duplicate table: {name}")
        text = text.replace(marker, header + "\n" + marker)
    # Current source has nine hydraulic columns; current workbook supplies ELAS.
    text = text.replace("{{BDENS}}\n", "{{BDENS}} {{ELAS}}\n")
    for name in ("SWETR", "SWDIVIDE", "SWBBCFILE", "DRFIL", "BBCFIL"):
        pattern = rf"(?m)^(\s*{name}\s*=)[^!\n]*"
        text, n = re.subn(pattern, lambda m: m[1] + " {{" + name + "}} ", text)
        if n != 1:
            raise ValueError(f"missing/duplicate scalar: {name}")
    # External BBC owns bottom data. Inactive inline sinus parameters stay
    # explicit for readability, while SWAP reads the separate BBC when enabled.
    return text


def render(source_bytes, context, *, policy=None):
    if context["issues"]:
        raise ValueError("unresolved typed context")
    values = {**context, **POLICY, **(policy or {})}
    values=deepcopy(values)
    # SWAP rejects SWDIVIDE=1 with prescribed ETref (SWETR=1).
    # Keep the workbook ET choice; select the corresponding parser branch.
    values["SWDIVIDE"]=1 if int(values["SWETR"])==0 else 0
    for key in ("GWLI", "PONDMX", "RSRO", "RSOIL", "RDS"):
        if values.get(key) is not None:
            values[key]=float(values[key])
    for table in ("TABLE_SOILPROFILE", "TABLE_SOILHYDRFUNC", "TABLE_SOILTEXTURES"):
        for row in values[table]:
            for key in row:
                if key not in ("ISUBLAY", "ISOILLAY", "NCOMP"):
                    row[key]=float(row[key])
    if context["SWINCO"] == 3:
        raise ValueError("restart input requires separately bound INIFIL")
    return render_text(prepare_template(source_bytes), values)
