"""Compare historical filter_lwkm and filter_lwkm2 without assuming their relation."""
from __future__ import annotations
import pandas as pd

CONTEXT=["svat","xc(m)","yc(m)","landgebruik22","lu7","lu4","lu2","bodem370"]

def compare_filters(df:pd.DataFrame,base_col="filter_lwkm",final_col="islwkm(0/1)")->tuple[dict,pd.DataFrame]:
    if base_col not in df or final_col not in df:
        raise ValueError(f"Need {base_col} and {final_col}")
    base=pd.to_numeric(df[base_col],errors="coerce").fillna(0).gt(0)
    final=pd.to_numeric(df[final_col],errors="coerce").fillna(0).gt(0)
    changed=base.ne(final)
    cols=[c for c in CONTEXT if c in df.columns]
    out=df.loc[changed,cols].copy()
    out["filter_lwkm"]=base.loc[changed].to_numpy()
    out["filter_lwkm2"]=final.loc[changed].to_numpy()
    out["change"]=out.apply(lambda r:"added" if r.filter_lwkm2 else "removed",axis=1)
    summary={
      "rows":len(df),"filter_lwkm_positive":int(base.sum()),"filter_lwkm2_positive":int(final.sum()),
      "changed":int(changed.sum()),"added":int((~base&final).sum()),"removed":int((base&~final).sum()),
      "changed_lgn0":int((changed & pd.to_numeric(df.get("landgebruik22"),errors="coerce").eq(0)).sum()) if "landgebruik22" in df else None
    }
    return summary,out
