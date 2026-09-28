import pandas as pd
from tools.build_swap_inputs import build_static_case

def test_static_case_binds_final_lookups_and_metfil():
    m=pd.DataFrame({"HRU":[7,7],"area_m2":[1,1],"soil2":[1,1],"bbc":[2,2],"lgn":[5,5],"bfe":[10,10],
      "irrigation_switch":[0,0],"rds":[1,1],"dqsat":[3,3],"svat":[1,2],"xc":[0,2],"yc":[0,0],"col":[1,2],"row":[1,1],
      "hh":[9,9],"glk":[10,10]})
    rep={"svat_repr":1,"bfe_repr":10,"rz_repr":100}
    control={"MaxPondDepth":.5,"crunoff_par":1,"tempCbotk":10,"TimStart":"20000101","TimEnd":"20001231"}
    mapped,providers=build_static_case(m,rep,control,({10:99},{(1,5):4},{(1,5):6}))
    assert mapped["soil_id"]==99 and mapped["crop_id"]==4 and mapped["METFIL"]=="7.met"
    assert providers["PONDMX"](mapped)==50
    assert providers["area"](mapped)==2
    assert providers["xc"](mapped) in (0.0,2.0)
