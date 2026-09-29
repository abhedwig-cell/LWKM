"""Compare FLF normalization candidates without choosing a physical winner."""
from __future__ import annotations
import pandas as pd

CELL_AREA_M2=62500.0

def compare_flf_support(df:pd.DataFrame)->pd.DataFrame:
    """Input columns: hru, flf_native, uopp_m2, selected."""
    d=df.loc[df["selected"].astype(bool)].copy()
    g=d.groupby("hru",sort=True)
    out=g.agg(
      n_cells=("flf_native","size"),
      flf_native_sum=("flf_native","sum"),
      active_area_m2=("uopp_m2","sum"),
      mean_uopp_m2=("uopp_m2","mean"),
    )
    out["modflow_area_m2"]=out["n_cells"]*CELL_AREA_M2
    out["active_fraction"]=out["active_area_m2"]/out["modflow_area_m2"]
    out["flf_per_active_area"]=out["flf_native_sum"]/out["active_area_m2"]
    out["flf_per_modflow_area"]=out["flf_native_sum"]/out["modflow_area_m2"]
    out["amplification_active_vs_full"]=out["flf_per_active_area"]/out["flf_per_modflow_area"]
    return out.reset_index()
