import pytest
from tools.swp_file_reference_guard import required_package_assets

def test_explicit_profile_can_require_crop_and_initial_files():
    swp="METFIL='1.met'\nCRPFIL='crop.crp'\nINIFIL='initial.ini'\n"
    assets=required_package_assets(
        swp,file_keys=("METFIL","CRPFIL","INIFIL"),
        required_keys=("METFIL","CRPFIL","INIFIL"))
    assert assets==["1.met","crop.crp","initial.ini","swap.swp"]

def test_missing_profile_required_key_fails_closed():
    with pytest.raises(ValueError,match="missing required SWP"):
        required_package_assets(
            "METFIL='1.met'",file_keys=("METFIL","INIFIL"),
            required_keys=("METFIL","INIFIL"))
