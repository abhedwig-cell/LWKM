import pandas as pd
from tools.hru_core import nearest_donors, medoid_existing_svat, backprojection_metrics

def test_weighted_donor_prefers_high_weight_soil_match():
    donors=pd.DataFrame([
      {"svat":10,"grondsoort2":1,"grondsoort4":1,"pawn21_rank":1,"Gt_LHM43":8,"kwelklasse4":1,"GHG_LHM43":100,"NettoKwel_LHM43":0},
      {"svat":20,"grondsoort2":2,"grondsoort4":2,"pawn21_rank":1,"Gt_LHM43":1,"kwelklasse4":1,"GHG_LHM43":0,"NettoKwel_LHM43":0},
    ])
    target=pd.DataFrame([{"grondsoort2":1,"grondsoort4":1,"pawn21_rank":1,"Gt_LHM43":1,"kwelklasse4":1,"GHG_LHM43":0,"NettoKwel_LHM43":0}])
    assert nearest_donors(target,donors,{"grondsoort2":250,"grondsoort4":100,"GHG_LHM43":.01,"Gt_LHM43":.5,"pawn21_rank":10,"kwelklasse4":.5,"NettoKwel_LHM43":.01}).iloc[0]==10

def test_medoid_is_existing_svat():
    g=pd.DataFrame({"svat":[1,2,3],"GHG_LHM43":[0,10,100],"NettoKwel_LHM43":[0,10,100]})
    assert medoid_existing_svat(g)==2

def test_backprojection_zero_when_exact():
    m=pd.DataFrame({"HRU":[1,1,2],"area_m2":[1,1,2],"GHG_LHM43_orig":[10,10,20],"NettoKwel_LHM43_orig":[5,5,7]})
    h=pd.DataFrame({"HRU":[1,2],"GHG_average":[10,20],"NettoKwel_average":[5,7]})
    q=backprojection_metrics(m,h).set_index("variable")
    assert q.loc["GHG","rmse"]==0
    assert q.loc["NettoKwel","mae"]==0
