import pandas as pd
from tools.generate_dra import aggregate_system,repair_system,render_dra

def members():
    return pd.DataFrame({"glk":[10,10],"cdr1":[1,1],"inf1":[1,1],"leng1":[1,0],
                         "bodh1":[8,8],"peil_sum1":[9,9],"peil_win1":[8.5,8.5]})

def test_active_drainage_uses_all_members():
    s=aggregate_system(members(),1,25)
    assert s["dd"]==100
    assert s["drnres"]==62500
    assert s["infres"]==62500

def test_high_resistance_disables_system():
    s={"drnres":20001,"infres":1,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    x=repair_system(s,1,False)
    assert x["drnres"]==100000 and x["dep"]==0

def test_nature_disables_system_four():
    s={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    assert repair_system(s,4,True)["drnres"]==100000

def test_serializer_has_five_level_header_and_tube_system_four():
    s={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    text=render_dra([s]*5,3,2000,2000,20)
    assert "NRLEVS = 5" in text and "SWDTYP4 = 1" in text and "SWALLO4 = 3" in text
