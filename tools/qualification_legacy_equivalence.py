"""Legacy B->C qualification equivalence checks."""
from __future__ import annotations
import pandas as pd

def compare_legacy_donor_marker(df:pd.DataFrame, suspect:pd.Series)->dict:
    if not {"svat","svat_donor"}.issubset(df.columns):
        raise ValueError("Need svat and svat_donor for legacy equivalence")
    legacy=pd.to_numeric(df["svat_donor"],errors="coerce").ne(pd.to_numeric(df["svat"],errors="coerce"))
    modern=pd.Series(suspect,index=df.index).astype(bool)
    fp=modern&~legacy;fn=legacy&~modern
    return {"rows":len(df),"legacy_notok":int(legacy.sum()),"modern_suspect":int(modern.sum()),
            "modern_only":int(fp.sum()),"legacy_only":int(fn.sum()),"exact":bool(legacy.equals(modern))}

def mismatch_rows(df:pd.DataFrame,suspect:pd.Series)->pd.DataFrame:
    legacy=pd.to_numeric(df["svat_donor"],errors="coerce").ne(pd.to_numeric(df["svat"],errors="coerce"))
    modern=pd.Series(suspect,index=df.index).astype(bool)
    x=df.loc[legacy.ne(modern),["svat","svat_donor"]].copy()
    x["legacy_notok"]=legacy.loc[x.index];x["modern_suspect"]=modern.loc[x.index]
    return x
