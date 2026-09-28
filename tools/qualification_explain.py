"""Explainable suspicious-SVAT qualification products."""
from __future__ import annotations
import pandas as pd
FLAGS=["ghg_sel","gt1_sel","gt2_sel","gt8_sel","kwel_sel","wegzijging_sel","runoff_sel","subinfil_sel"]

PROVENANCE={
"ghg_sel":{"stage":"pre_flevoland","rule":"ghg < 0 and agriculture"},
"gt1_sel":{"stage":"pre_flevoland","rule":"historical left-to-right GT1 raster algebra"},
"gt2_sel":{"stage":"pre_flevoland","rule":"historical left-to-right GT2 raster algebra"},
"gt8_sel":{"stage":"pre_flevoland_filter","rule":"kwelwegz > 1 and GT > 7"},
"kwel_sel":{"stage":"post_flevoland_kwel_corr","rule":"kwel threshold by land use, excluding polders"},
"wegzijging_sel":{"stage":"post_flevoland_kwel_corr","rule":"wegzijging threshold, excluding polders"},
"runoff_sel":{"stage":"pre_flevoland","rule":"runoff threshold by land use"},
"subinfil_sel":{"stage":"pre_flevoland","rule":"ontw_netto threshold, excluding polders"},
}

def explain_rows(df:pd.DataFrame,svat="svat")->pd.DataFrame:
    rows=[]
    for _,r in df.iterrows():
        active=[f for f in FLAGS if int(r.get(f,0))>0]
        rows.append({svat:r[svat],"is_suspect":bool(active),"n_reasons":len(active),
                     "reason_code":"|".join(active) if active else "NONE",
                     "flevoland_sensitive":any(f in ("kwel_sel","wegzijging_sel") for f in active)})
    return pd.DataFrame(rows)

def overlap_summary(df:pd.DataFrame)->pd.DataFrame:
    e=explain_rows(df)
    return (e.groupby(["reason_code","n_reasons","flevoland_sensitive"],dropna=False)
             .size().rename("svats").reset_index().sort_values(["svats","reason_code"],ascending=[False,True]))

def flag_summary(df:pd.DataFrame)->pd.DataFrame:
    total=len(df);rows=[]
    for f in FLAGS:
        n=int(pd.to_numeric(df[f],errors="coerce").fillna(0).gt(0).sum())
        rows.append({"flag":f,"svats":n,"fraction":n/total if total else 0,**PROVENANCE[f]})
    return pd.DataFrame(rows)
