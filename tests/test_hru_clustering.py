import pandas as pd
from tools.hru_clustering import robust_scale, corrected_skew, eligible_groups, staged_round_plan, next_min_size

def test_robust_scale_iqr_zero_returns_zero():
    assert (robust_scale(pd.Series([2,2,2]))==0).all()

def test_positive_skew_is_not_absolute_policy():
    assert corrected_skew([0,0,0,10])>0
    assert corrected_skew([0,10,10,10])<0

def test_area_gate():
    d=pd.DataFrame({"g":[1,1,2],"Oppha":[250,250,499]})
    assert eligible_groups(d,["g"])["g"].tolist()==[1,1]

def test_staged_remainder_moves_to_coarser_round():
    d=pd.DataFrame({"fine":["a","b","x"],"coarse":[1,1,2],"Oppha":[250,250,499]})
    p=staged_round_plan(d,[["fine"],["coarse"]],500)
    assert p.loc[0,"candidate_round"]==2
    assert p.loc[1,"candidate_round"]==2
    assert p.loc[2,"candidate_round"]==0

def test_min_size_reduction():
    size,next_fraction=next_min_size(80,.25,10)
    assert size==20
    assert abs(next_fraction-.21025)<1e-12
