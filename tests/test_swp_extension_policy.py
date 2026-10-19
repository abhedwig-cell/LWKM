import pytest
from tools.swp_file_reference_guard import required_package_assets


def test_stem_references_use_explicit_versioned_extensions():
    text="METFIL='7876.met'\nDRFIL='7876'\nBBCFIL='7876'\n"
    assert required_package_assets(text,file_extensions={'DRFIL':'.dra','BBCFIL':'.bbc'})==['7876.bbc','7876.dra','7876.met','swap.swp']


def test_extension_policy_rejects_paths():
    with pytest.raises(ValueError,match='extension policy'):
        required_package_assets("METFIL='x'",file_extensions={'METFIL':'/../x'})
