"""Qualification input adapter: derive flags or compare to historical reference."""
from __future__ import annotations
import pandas as pd
from tools.derive_suspect_flags import derive_all_compat

FLAGS=["ghg_sel","gt1_sel","gt2_sel","gt8_sel","kwel_sel","wegzijging_sel","runoff_sel","subinfil_sel"]

def derive_source_columns(df:pd.DataFrame)->pd.DataFrame:
    x=df.copy()
    rename={"ghg(cm-mv)":"ghg","glg(cm-mv)":"glg","gt(1-8)":"gt","landgebruik22":"lgn",
            "bofek79":"bofek","kwelwegzijging(mm/j)":"kwelwegz","runoff(mm/j)":"runoff"}
    for old,new in rename.items():
        if new not in x and old in x:x[new]=x[old]
    if "is_lwkm_domain" not in x:
        if "islwkm(0/1)" in x:x["is_lwkm_domain"]=pd.to_numeric(x["islwkm(0/1)"],errors="coerce").fillna(0)>0
        elif "lu2" in x:x["is_lwkm_domain"]=x["lu2"].isin([1,2])
    if "is_agriculture" not in x:
        if "lu2" in x:x["is_agriculture"]=x["lu2"].eq(1)
        else:raise ValueError("Need lu2 or is_agriculture")
    if "is_polder" not in x:raise ValueError("Raw derivation requires explicit is_polder source")
    if "ontw_netto" not in x:
        raise ValueError("Raw derivation requires ontw_netto in producer units; do not infer from postprocessed daily columns")
    return x

def derive_flags(df:pd.DataFrame)->pd.DataFrame:
    return derive_all_compat(derive_source_columns(df))

def compare_flags(df:pd.DataFrame,derived:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for flag in FLAGS:
        ref=pd.to_numeric(df[flag],errors="coerce").fillna(0).clip(lower=0).ne(0)
        got=derived[flag].ne(0)
        rows.append({"flag":flag,"reference_positive":int(ref.sum()),"derived_positive":int(got.sum()),
                     "false_positive":int((got&~ref).sum()),"false_negative":int((ref&~got).sum()),
                     "exact":bool(ref.equals(got))})
    ref_union=df[FLAGS].apply(pd.to_numeric,errors="coerce").fillna(0).clip(lower=0).ne(0).any(axis=1)
    got_union=derived[FLAGS].ne(0).any(axis=1)
    rows.append({"flag":"ANY","reference_positive":int(ref_union.sum()),"derived_positive":int(got_union.sum()),
                 "false_positive":int((got_union&~ref_union).sum()),"false_negative":int((ref_union&~got_union).sum()),
                 "exact":bool(ref_union.equals(got_union))})
    return pd.DataFrame(rows)
