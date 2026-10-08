import pandas as pd
import pytest
from tools.diagnose_dqsat_zero_fallback import diagnostic_positive_median_fallback

def test_zero_rep_gets_positive_median_without_overwriting_source():
    rep=pd.DataFrame({"hru":[20,10],"representative_dqsat":[0.,8.]})
    mem=pd.DataFrame({"hru":[20,20,20,10],"dqsat":[0.,3.,9.,8.]})
    out=diagnostic_positive_median_fallback(rep,mem).set_index("hru")
    assert out.loc[20,"representative_dqsat"]==0
    assert out.loc[20,"diagnostic_candidate_dqsat"]==6
    assert bool(out.loc[20,"fallback_applied"])
    assert out.loc[10,"diagnostic_candidate_dqsat"]==8
    assert not bool(out.loc[10,"fallback_applied"])

def test_all_zero_hru_fails_closed():
    rep=pd.DataFrame({"hru":[1],"representative_dqsat":[0.]})
    mem=pd.DataFrame({"hru":[1,1],"dqsat":[0.,0.]})
    with pytest.raises(ValueError,match="no positive member fallback"):
        diagnostic_positive_median_fallback(rep,mem)

def test_duplicate_representative_hru_fails():
    rep=pd.DataFrame({"hru":[1,1],"representative_dqsat":[0.,0.]})
    mem=pd.DataFrame({"hru":[1],"dqsat":[3.]})
    with pytest.raises(ValueError,match="duplicate representative HRU"):
        diagnostic_positive_median_fallback(rep,mem)
