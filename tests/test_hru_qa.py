import pandas as pd
from tools.hru_qa import weighted_stats,purity,route_summary,admission_summary

def test_weighted_stats_exact_zero():
    s=weighted_stats(pd.Series([0,0]),pd.Series([1,2]))
    assert s["mae"]==0 and s["rmse"]==0 and s["p95_abs"]==0

def test_purity_area_weighted():
    d=pd.DataFrame({"a":[1,1],"b":[1,2],"area_m2":[3,1]})
    assert purity(d,"a","b")==75

def test_route_summary_conserves_svats():
    d=pd.DataFrame({"svat":[1,2,3],"HRU":[1,1,2],"assignment_route":["PRIMARY_CLUSTER","PRIMARY_CLUSTER","HRU_EXTRA"],"area_m2":[1,1,2]})
    r=route_summary(d)
    assert r.svats.sum()==3 and abs(r.area_fraction.sum()-1)<1e-12

def test_admission_summary_counts():
    m=pd.DataFrame({"svat":[1,2],"HRU":[1,2],"NRU":[1,2],"assignment_route":["PRIMARY_CLUSTER","HRU_EXTRA"]})
    h=pd.DataFrame({"HRU":[1,2],"hru_representative_svat":[1,2]})
    s=admission_summary(m,h)
    assert s["svats"]==2 and s["hrus"]==2 and s["nrus"]==2
