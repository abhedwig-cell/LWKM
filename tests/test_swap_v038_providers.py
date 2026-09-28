import pandas as pd
from tools.swap_v038_providers import historical_pre_override,apply_representative_historical,lookup_ids,metfil

def test_pre_override_fields_are_computed_before_representative():
    m=pd.DataFrame({"svat":[1,2,3],"bfe":[10,10,20],"lgn":[5,5,8],"rds":[1,1,2],"dqsat":[3,3,9],"soil2":[1,1,2]})
    v=historical_pre_override(m)
    assert v["RDS"]==100 and v["dqsat"]==3 and v["SWETR"]==0
    v.update({"bodem_id":10,"lu_id":5,"soil2_id":1})
    x=apply_representative_historical(v,{"svat_repr":3,"bfe_repr":20,"rz_repr":200},m)
    assert x["bodem_id"]==20 and x["lu_id"]==8 and x["RDS"]==200
    assert x["dqsat"]==3 and x["SWETR"]==0

def test_lookup_uses_final_bfe_and_lgn_but_majority_soil2():
    v={"bodem_id":20,"soil2_id":1,"lu_id":8}
    x=lookup_ids(v,{20:79},{(1,8):4},{(1,8):5})
    assert x=={"soil_id":79,"crop_id":4,"croporg_id":5}

def test_metfil_is_hru_file():
    assert metfil(42)=="42.met"
