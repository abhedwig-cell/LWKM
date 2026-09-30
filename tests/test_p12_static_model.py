import pytest
from tools.p12_hru_representation import HRURepresentation
from tools.p12_static_model import *

def test_schema_first_flags_and_soil2():
    r=HRURepresentation(1,99,80,7,78,12)
    s=SoilClassification(78,40,10,2,1)
    x=build_static_representation(r,s)
    assert (x.bofek79,x.soil2,x.landuse,x.root_depth_cm)==(40,1,12,80)
    assert x.swetr==1 and x.is_nature

def test_soil_mismatch_fails_closed():
    r=HRURepresentation(1,99,80,7,78,12)
    with pytest.raises(ValueError):
        build_static_representation(r,SoilClassification(79,39,10,2,1))

def test_legacy_gwli_is_explicitly_isolated():
    assert initial_gwli_cm(9.0,10.0)==-100
    assert initial_gwli_cm(11.0,10.0)==0
