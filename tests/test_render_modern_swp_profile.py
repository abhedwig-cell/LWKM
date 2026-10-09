import hashlib,json
import pytest
from tools.render_modern_swp_profile import render_profile

def profile(tmp_path,template,required):
    t=tmp_path/"modern.swp";t.write_text(template)
    p=tmp_path/"profile.json"
    p.write_text(json.dumps({"schema_version":1,"profile_id":"modern-test-v1",
                             "template_sha256":hashlib.sha256(t.read_bytes()).hexdigest(),
                             "required_context":required}))
    return t,p

def test_profile_renders_explicit_swet_and_period():
    t,p=profile(tmp_path,"SWETR={{SWETR}}\nPERIOD={{PERIOD}}\n",["SWETR","PERIOD"])
    output,audit=render_profile(t,p,{"SWETR":1,"PERIOD":0})
    assert "SWETR=1" in output and "PERIOD=0" in output
    assert audit["status"]=="MODERN_SWP_RENDER_CANDIDATE_NOT_ADMITTED"

def test_profile_rejects_missing_symbol(tmp_path):
    t,p=profile(tmp_path,"SWETR={{SWETR}}",["SWETR"])
    with pytest.raises(ValueError,match="missing required"):
        render_profile(t,p,{})

def test_profile_rejects_template_identity_mismatch(tmp_path):
    t,p=profile(tmp_path,"SWETR={{SWETR}}",["SWETR"])
    t.write_text("changed")
    with pytest.raises(ValueError,match="SHA mismatch"):
        render_profile(t,p,{"SWETR":1})
