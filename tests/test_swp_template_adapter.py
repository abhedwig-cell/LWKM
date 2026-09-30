import pytest

from tools.swp_template_adapter import (
    TABLE_HEADERS,
    apply_render_profile,
    canonicalize_legacy_template,
)


def _legacy_fragment():
    return """SWWBA = 0 ! daily water balance
PERIOD = 0 ! interval
SWAUN = 2 ! unformatted output
SWODAT = 1 ! extra dates
SWETR = 0 ! evap method
INLIST_CSV = {{INLIST_CSV}}

{{#TABLE_CROPROTATION}}
{{CROPSTART}} {{CROPEND}} {{CROPNAME}} {{CROPFIL}} {{CROPTYPE}}
{{/TABLE_CROPROTATION}}

{{#TABLE_SOILPROFILE}}
{{ISUBLAY}} {{ISOILLAY}} {{HSUBLAY}} {{NCOMP}}
{{/TABLE_SOILPROFILE}}

{{#TABLE_SOILHYDRFUNC}}
{{ORES}} {{OSAT}} {{ALFA}} {{NPAR}} {{KSATFIT}} {{LEXP}} {{H_ENPR}} {{KSATEXM}} {{BDENS}} {{ELAS}}
{{/TABLE_SOILHYDRFUNC}}

{{#TABLE_SOILTEXTURES}}
{{PSAND}} {{PSILT}} {{PCLAY}} {{ORGMAT}}
{{/TABLE_SOILTEXTURES}}
"""


def test_canonicalizer_exposes_hidden_serialization_policy():
    out=canonicalize_legacy_template(_legacy_fragment())
    for section,header in TABLE_HEADERS.items():
        assert header+"\n{{#"+section+"}}" in out
    for key in ("SWETR","SWWBA","PERIOD","SWAUN","SWODAT"):
        assert "{{"+key+"}}" in out


def test_canonicalizer_is_idempotent():
    once=canonicalize_legacy_template(_legacy_fragment())
    twice=canonicalize_legacy_template(once)
    assert twice==once


def test_canonicalizer_fails_if_historical_default_does_not_match():
    bad=_legacy_fragment().replace("SWWBA = 0","SWWBA = 1")
    with pytest.raises(ValueError,match="SWWBA=0"):
        canonicalize_legacy_template(bad)


def test_render_profile_overrides_output_only():
    ctx={"SWETR":1,"RDS":40,"INLIST_CSV":"'old'"}
    profile={"renderer_output":{
        "SWWBA":1,
        "PERIOD":1,
        "SWAUN":0,
        "SWODAT":0,
        "INLIST_CSV":"'new'",
    }}
    out=apply_render_profile(ctx,profile)
    assert out["SWETR"]==1
    assert out["RDS"]==40
    assert out["SWWBA"]==1
    assert out["PERIOD"]==1
    assert out["SWAUN"]==0
    assert out["SWODAT"]==0
    assert out["INLIST_CSV"]=="'new'"
    assert ctx["INLIST_CSV"]=="'old'"
