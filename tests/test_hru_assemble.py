import pandas as pd
from tools.hru_assemble import return_small_nru_groups,make_hru_extra,finalize_nru,representative_relation

def test_special_ldgb_allows_two_member_nru():
    d=pd.DataFrame({"svat":[1,2],"cluster_local":[0,0],"aggr_no":[1,1],"LDGBclus":[35,35]})
    keep,small=return_small_nru_groups(d)
    assert len(keep)==2 and len(small)==0

def test_normal_ldgb_rejects_three_member_nru():
    d=pd.DataFrame({"svat":[1,2,3],"cluster_local":[0]*3,"aggr_no":[1]*3,"LDGBclus":[1]*3})
    keep,small=return_small_nru_groups(d)
    assert len(keep)==0 and len(small)==3

def test_hru_extra_and_representative_are_existing_svats():
    d=pd.DataFrame({"svat":[1,2,3],"LDGBclus":[1]*3,"lu4":[2]*3,"grondsoort4":[3]*3,"Gt_LHM43":[4]*3,
                    "GHG_LHM43":[0,10,100],"NettoKwel_LHM43":[0,10,100]})
    x=make_hru_extra(d,5,lambda g: g.loc[(g.GHG_LHM43-10).abs().idxmin(),'svat'])
    assert x.HRU.nunique()==1
    assert x.hru_cluster_donor_svat.iloc[0] in {1,2,3}
    x=finalize_nru(x)
    rep=representative_relation(x)
    assert rep.hru_representative_svat.iloc[0] in {1,2,3}
