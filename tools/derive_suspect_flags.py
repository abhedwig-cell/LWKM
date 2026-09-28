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


PEAT_BOFEK=set(range(1,19))
AG_LGN={0,1,2,3,4,5,6,7,9,10,21}
AG_NON_GRASS_LGN={0,2,3,4,5,6,7,9,10,21}

def derive_gt12_compat(df:pd.DataFrame)->pd.DataFrame:
    """Reconstruct intended binary GT1/GT2 masks from producer dependencies.
    Historical gridcalc precedence still requires raster regression for exact admission.
    """
    ag=df["lgn"].isin(AG_LGN)&df["is_lwkm_domain"].astype(bool)
    non_grass=df["lgn"].isin(AG_NON_GRASS_LGN)&df["is_lwkm_domain"].astype(bool)
    peat_grass=df["bofek"].isin(PEAT_BOFEK)&df["lgn"].eq(1)
    # gridcalc evaluates strictly left-to-right. Preserve numeric raster algebra,
    # then the consumer clips negatives with MAX(flag,0).
    gt1=((df["glg"]<50).astype(int)*ag.astype(int)-peat_grass.astype(int)).clip(lower=0)
    a=(df["ghg"]<40).astype(int)
    a=a*(df["glg"]<80).astype(int)
    a=a-(df["glg"]<50).astype(int)
    a=a*non_grass.astype(int)
    gt2_base_for_crop=((df["ghg"]<40)&(df["glg"]<80)).astype(int)-(df["glg"]<50).astype(int)
    bollen=gt2_base_for_crop*df["lgn"].eq(10).astype(int)
    boom=gt2_base_for_crop*df["lgn"].eq(7).astype(int)*df["bofek"].isin(PEAT_BOFEK).astype(int)
    gt2=(a-bollen-boom).clip(lower=0)
    return pd.DataFrame({"gt1_sel":gt1.astype(int),"gt2_sel":gt2.astype(int)},index=df.index)

def kwelwegz_gridcalc(kwel,wegzijging):
    """Historical gridcalc: operations are evaluated left-to-right."""
    return (pd.to_numeric(kwel,errors="coerce")+pd.to_numeric(wegzijging,errors="coerce"))/365.25

def derive_all_compat(df:pd.DataFrame)->pd.DataFrame:
    octf=derive_oct2025(df)
    gt=derive_gt12_compat(df)
    return combine_with_gt12(octf,gt.gt1_sel,gt.gt2_sel)
