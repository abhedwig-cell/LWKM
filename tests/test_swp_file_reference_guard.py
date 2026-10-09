import pytest
from tools.swp_file_reference_guard import extract_references,required_package_assets

def test_extracts_active_file_assignments_only():
    s="* METFIL='old.met'\nMETFIL='1.met'\nDRFIL='1.dra'\nBBCFIL='1.bbc'\n"
    assert extract_references(s)=={"METFIL":"1.met","DRFIL":"1.dra","BBCFIL":"1.bbc"}
    assert required_package_assets(s)==["1.bbc","1.dra","1.met","swap.swp"]

def test_duplicate_assignment_rejected():
    with pytest.raises(ValueError,match="duplicate"):
        extract_references("METFIL='a.met'\nMETFIL='b.met'")

@pytest.mark.parametrize("value",["../a.met","/tmp/a.met","folder/a.met",""])
def test_unsafe_reference_rejected(value):
    with pytest.raises(ValueError):
        extract_references(f"METFIL='{value}'")

def test_ignores_unrecognized_file_key():
    assert extract_references("CRPFIL='crop.crp'")=={}
