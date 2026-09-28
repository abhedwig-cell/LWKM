import pandas as pd
from tools.swap_mapping import map_hru_members,case_dependency_record
from tools.plan_swap_cases import plan

def members():
    return pd.DataFrame({
      "HRU":[1,1,1],"area_m2":[1,1,1],"soil2":[1,1,2],"bbc":[2,2,7],
      "lgn":[5,5,6],"bfe":[10,10,11],"irrigation_switch":[1,0,0]})

def test_irrigation_historical_threshold_is_strictly_greater_37_percent():
    c=map_hru_members(members(),irrigation_threshold=.37)
    assert c["irrigation_id"]==0
    x=members(); x.loc[1,"irrigation_switch"]=1
    assert map_hru_members(x,irrigation_threshold=.37)["irrigation_id"]==1

def test_representative_override_is_explicit():
    c=map_hru_members(members(),{"bfe_repr":99,"lgn_repr":8,"rz_repr":120})
    assert c["bodem_id"]==99 and c["lu_id"]==8 and c["RDS"]==1.2

def test_dependency_change_regenerates_only_changed_hru():
    c1={"HRU":1,"bodem_id":1}; c2={"HRU":2,"bodem_id":1}
    a=[case_dependency_record(c1,mapping_version="v",swap_version="s",meteo_ref="m",boundary_ref="b",soil_ref="x",crop_ref="c"),
       case_dependency_record(c2,mapping_version="v",swap_version="s",meteo_ref="m",boundary_ref="b",soil_ref="x",crop_ref="c")]
    c2b={"HRU":2,"bodem_id":2}
    b=[a[0],case_dependency_record(c2b,mapping_version="v",swap_version="s",meteo_ref="m",boundary_ref="b",soil_ref="x",crop_ref="c")]
    p=plan(b,a)
    assert p["changed_or_new"]==[2] and p["unchanged"]==[1]
