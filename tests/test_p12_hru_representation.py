import pytest
from tools.p12_hru_representation import *

def test_resolves_landuse_via_schema_selected_svat():
    s={"hru":12,"svat_repr":99,"rz_repr":80,"bfe_repr":301,"bodem_repr":42}
    x=resolve_hru_representation(s,{99:{"lgn":7}})
    assert x.representative_landuse==7
    assert x.representative_root_depth_cm==80
    assert x.provenance=="PIET_HRU_SCHEMA"

def test_missing_representative_svat_fails():
    with pytest.raises(ValueError):
        resolve_hru_representation({"hru":1,"svat_repr":9,"rz_repr":1,"bfe_repr":1,"bodem_repr":1},{})
