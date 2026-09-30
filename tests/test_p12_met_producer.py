from tools.p12_met_producer import *

def test_compose_dry_and_render():
    d=DistrictDay(100,-1,5,.8,2,4)
    x=compose(12,1,1,2018,0,1.23456,d,9)
    assert x.wet==0 and x.wet_source=="FORCED_DRY_ZERO"
    s=render_swap_met(x)
    assert "'12'" in s and "1.2346" in s

def test_compose_imputed():
    d=DistrictDay(100,-1,5,.8,2,0)
    x=compose(12,1,1,2018,3,1,d,7)
    assert x.wet==7 and x.wet_source=="IMPUTED"
