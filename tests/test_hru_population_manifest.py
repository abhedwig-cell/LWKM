import pytest
from tools.hru_population_manifest import build_manifest, validate_membership

def test_sparse_hru_population():
    a=build_manifest([9001,101,205],release="next")
    assert a["n_hrus"]==3
    assert a["hru_ids"]==[101,205,9001]
    assert validate_membership(a,[205,9001,101])
    with pytest.raises(ValueError,match="identity mismatch"):
        validate_membership(a,[101,205,9002])

def test_duplicate_and_corruption():
    with pytest.raises(ValueError):
        build_manifest([101,101],release="x")
    a=build_manifest([10,20],release="x")
    a["hru_ids"][0]=11
    with pytest.raises(ValueError,match="digest mismatch"):
        validate_membership(a,[11,20])
