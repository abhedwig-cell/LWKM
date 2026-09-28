import pandas as pd
from tools.qualification_explain import explain_rows,overlap_summary,flag_summary,FLAGS

def test_explanation_preserves_multiple_reasons():
    d={f:[0,0] for f in FLAGS};d.update({"svat":[1,2]})
    d["ghg_sel"][0]=1;d["kwel_sel"][0]=1
    x=explain_rows(pd.DataFrame(d))
    assert x.loc[0,"n_reasons"]==2
    assert x.loc[0,"reason_code"]=="ghg_sel|kwel_sel"
    assert x.loc[0,"flevoland_sensitive"]

def test_overlap_counts_all_rows():
    d={f:[0,0,0] for f in FLAGS};d["svat"]=[1,2,3];d["runoff_sel"][1]=1
    assert overlap_summary(pd.DataFrame(d)).svats.sum()==3

def test_flag_summary_marks_kwel_post_correction():
    d={f:[0] for f in FLAGS};d["svat"]=[1]
    x=flag_summary(pd.DataFrame(d)).set_index("flag")
    assert x.loc["kwel_sel","stage"]=="post_flevoland_kwel_corr"
