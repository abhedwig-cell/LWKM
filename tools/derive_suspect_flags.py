"""Derive LWKM suspicious-cell flags from tabular source values.

Compatibility expressions follow the reconstructed producer batch. GT1/GT2
remain guarded because original gridcalc arithmetic/subtraction precedence must
still be regression-tested on source grids.
"""
from __future__ import annotations
import pandas as pd

def derive_oct2025(df:pd.DataFrame)->pd.DataFrame:
    x=pd.DataFrame(index=df.index)
    ag=df["is_agriculture"].astype(bool); nature=~ag
    polder=df["is_polder"].astype(bool); domain=df["is_lwkm_domain"].astype(bool)
    x["ghg_sel"]=((df["ghg"]<0)&ag).astype(int)
    x["gt8_sel"]=((df["kwelwegz"]>1)&(df["gt"]>7)).astype(int)
    x["kwel_sel"]=(((df["kwelwegz"]>1826)&nature&~polder)|((df["kwelwegz"]>730)&ag&~polder)).astype(int)
    x["wegzijging_sel"]=((df["kwelwegz"]<-548)&domain&~polder).astype(int)
    x["runoff_sel"]=(((df["runoff"]<-548)&nature)|((df["runoff"]<-183)&ag)).astype(int)
    x["subinfil_sel"]=((df["ontw_netto"]>365)&domain&~polder).astype(int)
    return x

def combine_with_gt12(oct_flags:pd.DataFrame,gt1:pd.Series,gt2:pd.Series)->pd.DataFrame:
    x=oct_flags.copy();x["gt1_sel"]=pd.to_numeric(gt1,errors="coerce").fillna(0).clip(lower=0).astype(int)
    x["gt2_sel"]=pd.to_numeric(gt2,errors="coerce").fillna(0).clip(lower=0).astype(int)
    order=["ghg_sel","gt1_sel","gt2_sel","gt8_sel","kwel_sel","wegzijging_sel","runoff_sel","subinfil_sel"]
    x=x[order];x["is_suspect"]=x.ne(0).any(axis=1)
    x["isuit_code"]=1000000*x[order].sum(axis=1)+100000*x.ghg_sel+10000*(x.gt1_sel+x.gt2_sel)+1000*x.gt8_sel+100*(x.kwel_sel+x.wegzijging_sel)+10*x.runoff_sel+x.subinfil_sel
    return x
