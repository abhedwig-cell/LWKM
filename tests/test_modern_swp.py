import pytest
from tools.modern_swp import prepare_template


def test_modern_adapter_does_not_accept_different_template():
    with pytest.raises(ValueError, match="SHA mismatch"):
        prepare_template(b"different template")

def test_explicit_pm_variant_does_not_change_datamodel_context(monkeypatch):
    from tools.modern_swp import render
    monkeypatch.setattr('tools.modern_swp.prepare_template',lambda b:'SWETR={{SWETR}}\nSWDIVIDE={{SWDIVIDE}}\n')
    c={'issues':[],'SWETR':1,'SWINCO':2,'TABLE_SOILPROFILE':[],
       'TABLE_SOILHYDRFUNC':[],'TABLE_SOILTEXTURES':[]}
    assert 'SWETR=1' in render(b'',c)
    assert 'SWETR=0' in render(b'',c,et_policy='penman_monteith')
    assert c['SWETR']==1


def test_owner_tulip_profile_is_explicit_and_does_not_change_grass(monkeypatch):
    from tools.modern_swp import render
    monkeypatch.setattr('tools.modern_swp.prepare_template',lambda b:'SWETR={{SWETR}}\nSWDIVIDE={{SWDIVIDE}}\n')
    c={'issues':[],'SWETR':1,'SWINCO':2,'TABLE_SOILPROFILE':[],
       'TABLE_SOILHYDRFUNC':[],'TABLE_SOILTEXTURES':[],
       'TABLE_CROPROTATION':[{'CROPNAME':"'tulp'"}]}
    assert 'SWETR=0' in render(b'',c,et_policy='owner_tulip_pm')
    assert 'SWETR=1' in render(b'',c,et_policy='datamodel')
    c['TABLE_CROPROTATION'][0]['CROPNAME']="'gras'"
    assert 'SWETR=1' in render(b'',c,et_policy='owner_tulip_pm')
    assert c['SWETR']==1
