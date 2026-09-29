from tools.p12_wet_policy import *

def test_dry_forces_zero():
    x=historical_wet_policy(0.009,4,7); assert x==(WetResult(0,0,WetSource.FORCED_DRY_ZERO)); assert_wet_invariant(x)

def test_wet_keeps_local():
    x=historical_wet_policy(2,3,8); assert x.wet==3 and x.source==WetSource.DISTRICT; assert_wet_invariant(x)

def test_wet_missing_uses_max():
    x=historical_wet_policy(2,0,6); assert x.wet==6 and x.source==WetSource.IMPUTED; assert_wet_invariant(x)
