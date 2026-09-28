import pandas as pd,pytest
from tools.flevoland_correction import build_correction_relation,apply_correction,validate_relation

def test_sparse_relation_only_contains_changed_svats():
    a=pd.DataFrame({"svat":[1,2],"kwel(mm/j)":[1.,2.]})
    b=pd.DataFrame({"svat":[1,2],"kwel(mm/j)":[1.,5.]})
    r=build_correction_relation(a,b)
    assert r.svat.tolist()==[2] and r.delta_kwel.iloc[0]==3
    x=apply_correction(a,r)
    assert x["kwel(mm/j)"].tolist()==[1.,5.]
    assert x.kwel_original.tolist()==[1.,2.]

def test_count_gate():
    r=pd.DataFrame({"svat":[1],"kwel_original":[1],"kwel_corrected":[2]})
    with pytest.raises(ValueError):validate_relation(r,4677)
