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

from tools.hru_clustering import adaptive_partition,run_round
import numpy as np

class OneCluster:
    def __call__(self,g,min_size): return np.zeros(len(g),dtype=int)

def test_identical_hydrology_bypasses_partitioner():
    d=pd.DataFrame({"GHG_LHM43":[1,1],"NettoKwel_LHM43":[2,2]})
    x,q=adaptive_partition(d,None)
    assert q["reason"]=="IDENTICAL_HYDROLOGY" and (x.cluster_local==0).all()

def test_round_defers_group_below_area_threshold():
    d=pd.DataFrame({"LDGBclus":[1,1],"g":[1,1],"Oppha":[100,100],"GHG_LHM43":[1,2],"NettoKwel_LHM43":[1,2]})
    a,r,q=run_round(d,["LDGBclus","g"],OneCluster(),round_no=1)
    assert len(a)==0 and len(r)==2

def test_round_accepts_quality_pass():
    d=pd.DataFrame({"LDGBclus":[1]*80,"g":[1]*80,"Oppha":[6.25]*80,
                    "GHG_LHM43":list(range(80)),"NettoKwel_LHM43":list(range(80))})
    a,r,q=run_round(d,["LDGBclus","g"],OneCluster(),round_no=3)
    assert len(a)==80 and len(r)==0 and (a.aggr_no==3).all()
