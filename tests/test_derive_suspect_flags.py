import pandas as pd
from tools.derive_suspect_flags import derive_gt12_compat,derive_all_compat

def row(**kw):
    d={"ghg":60,"glg":100,"kwelwegz":0,"gt":4,"runoff":0,"ontw_netto":0,
       "is_agriculture":True,"is_polder":False,"is_lwkm_domain":True,"lgn":1,"bofek":20}
    d.update(kw);return d

def test_gt1_excludes_peat_grass():
    d=pd.DataFrame([row(glg=40,bofek=20),row(glg=40,bofek=10)])
    x=derive_gt12_compat(d)
    assert x.gt1_sel.tolist()==[1,0]

def test_gt2_excludes_bollen_and_peat_boomteelt():
    d=pd.DataFrame([row(ghg=30,glg=60,lgn=2),row(ghg=30,glg=60,lgn=10),row(ghg=30,glg=60,lgn=7,bofek=10)])
    assert derive_gt12_compat(d).gt2_sel.tolist()==[1,0,0]

def test_any_flag_sets_suspect_and_diagnostic_code():
    d=pd.DataFrame([row(ghg=-1)])
    x=derive_all_compat(d)
    assert x.is_suspect.iloc[0]
    assert x.isuit_code.iloc[0]>=1100000
