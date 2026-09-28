import pandas as pd
from tools.build_canonical_svat import prepare, FLAG_COLUMNS

def base():
    rows=[]
    for i,lu2 in enumerate([1,2,3],start=1):
        r={"svat":i,"lu2":lu2,"kwel(mm/j)":10.0,"kwel_org(mm/j)":10.0}
        r.update({c:0 for c in FLAG_COLUMNS}); rows.append(r)
    return pd.DataFrame(rows)

def test_domain_is_lu2_1_or_2():
    lbn,_,_=prepare(base())
    assert lbn["svat"].tolist()==[1,2]

def test_flevoland_relation_is_non_destructive():
    df=base(); df.loc[df.svat==1,"kwel(mm/j)"]=7.0
    lbn,corr,_=prepare(df)
    assert len(corr)==1
    assert corr.iloc[0]["kwel_raw_mm_y"]==10.0
    assert corr.iloc[0]["kwel_corrected_mm_y"]==7.0
    assert lbn.loc[lbn.svat==1,"kwel_org(mm/j)"].item()==10.0

def test_any_flag_excludes_from_cluster_building():
    df=base(); df.loc[df.svat==2,"runoff_sel"]=1
    _,_,q=prepare(df)
    assert q.loc[q.svat==1,"is_valid_for_hru_cluster_building"].item()
    assert not q.loc[q.svat==2,"is_valid_for_hru_cluster_building"].item()
    assert q.loc[q.svat==2,"qualification_reason_ids"].item()=="runoff_sel"
