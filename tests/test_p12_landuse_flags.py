from tools.p12_landuse_flags import *
def test_boundaries():
    assert landuse_flags(6).swetr==0
    assert landuse_flags(7).swetr==1
    assert landuse_flags(11).is_nature
    assert not landuse_flags(18).is_nature
    assert not landuse_flags(21).is_nature
