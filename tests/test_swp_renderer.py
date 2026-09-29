from tools.swp_renderer import render_text
import pytest

def test_scalar_and_repeated_section():
    t="A={{A}}\n{{#ROWS}}{{X}},{{Y}}\n{{/ROWS}}"
    assert render_text(t,{"A":1,"ROWS":[{"X":2,"Y":3},{"X":4,"Y":5}]})=="A=1\n2,3\n4,5\n"

def test_boolean_section():
    assert render_text("x{{#ON}}y={{Y}}{{/ON}}z",{"ON":True,"Y":2})=="xy=2z"
    assert render_text("x{{#ON}}y{{/ON}}z",{"ON":False})=="xz"

def test_unresolved_fails():
    with pytest.raises(KeyError): render_text("{{X}}",{})
