"""Qualification sequencing around the Flevoland kwel correction."""
from __future__ import annotations
import pandas as pd
from tools.flevoland_correction import apply_correction
from tools.derive_suspect_flags import derive_all_compat

def historical_compat_flags(base:pd.DataFrame,correction:pd.DataFrame)->pd.DataFrame:
    """Reproduce evidenced historical asymmetry.

    Six filter-route flags, including gt8, are derived from the pre-correction
    state. kwel_sel and wegzijging_sel are then replaced by values derived from
    the corrected kwel route.
    """
    pre=derive_all_compat(base)
    corrected=apply_correction(base,correction,kwel="kwel(mm/j)")
    if "wegzijging(mm/j)" not in corrected:
        raise ValueError("Need historical wegzijging to recompute corrected kwelwegz")
    # Table values are daily outputs. Corrected kwel and wegzijging combine directly here;
    # producer-period compatibility must be regression checked before HISTORICAL_EXACT.
    corrected=corrected.copy()
    corrected["kwelwegz"]=pd.to_numeric(corrected["kwel(mm/j)"],errors="coerce")+pd.to_numeric(corrected["wegzijging(mm/j)"],errors="coerce")
    post=derive_all_compat(corrected)
    out=pre.copy()
    out["kwel_sel"]=post["kwel_sel"]
    out["wegzijging_sel"]=post["wegzijging_sel"]
    flags=["ghg_sel","gt1_sel","gt2_sel","gt8_sel","kwel_sel","wegzijging_sel","runoff_sel","subinfil_sel"]
    out["is_suspect"]=out[flags].ne(0).any(axis=1)
    return out

def modern_consistent_flags(corrected:pd.DataFrame)->pd.DataFrame:
    """Candidate policy: all kwel-dependent criteria see one corrected state."""
    return derive_all_compat(corrected)
