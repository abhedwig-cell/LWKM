"""Population review of physically motivated seven-to-five DRA merge candidates.

This diagnostic is deliberately independent of representative dqsat and H1
monthly stage values. It reviews the two proposed static merge families:

* MVG + OLF: drain-only open-channel pair.
* S + T: infiltration-capable regional open-channel pair.

H1 and PIPE are treated as protected semantic levels. The tool does not admit a
production compression policy; it quantifies whether fixed candidate merges are
hydraulically defensible in the HRUs where both sources are active.
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import tempfile

import numpy as np
import pandas as pd

from tools.idf_reader import read_idf

EXPECTED_ROWS=427656
EXPECTED_HRUS=10242
CELL_AREA=62500.0

FILES={
    "S_cdr":("remaining","COND_secundair.IDF"),
    "S_inf":("remaining","inf_mz_secundair.IDF"),
    "S_sum":("remaining","PEIL_S1Z_250.IDF"),
    "S_win":("remaining","PEIL_S1W_250.IDF"),
    "S_bot_sum":("remaining","BODH_S1Z_250.IDF"),
    "S_bot_win":("remaining","BODH_S1W_250.IDF"),
    "T_cdr":("remaining","COND_tertiair.IDF"),
    "T_inf":("remaining","inf_mz_tertiair.IDF"),
    "T_sum":("remaining","PEIL_T1Z_250.IDF"),
    "T_win":("remaining","PEIL_T1W_250.IDF"),
    # LHM433 INI binds tertiary rbot to its stage grids.
    "T_bot_sum":("remaining","PEIL_T1Z_250.IDF"),
    "T_bot_win":("remaining","PEIL_T1W_250.IDF"),
    "MVG_cdr":("h1","COND_greppels.IDF"),
    "MVG_bot":("h1","BODH_BRP2012_MVGREP_250.IDF"),
    "OLF_cdr":("remaining","COND_SOF_250.IDF"),
    "OLF_bot":("remaining","BODH_SOF_250.IDF"),
    "AHN_cm":("remaining","ahn_f250_cm.asc"),
}

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def find_one(root:Path,name:str)->Path:
    m=list(root.rglob(name))
    if len(m)!=1: raise ValueError(f"expected one {name}, got {len(m)}")
    return m[0]

def valid(v,nodata):
    return np.isfinite(v) & ~np.isclose(v,float(nodata))

def quant(v):
    a=np.asarray(v,float)
    a=a[np.isfinite(a)]
    if not len(a): return {k:None for k in ("p50","p90","p95","p99","max")}
    return {"p50":float(np.quantile(a,.5)),"p90":float(np.quantile(a,.9)),
            "p95":float(np.quantile(a,.95)),"p99":float(np.quantile(a,.99)),
            "max":float(np.max(a))}

def read_ascii(path:Path):
    with path.open("r",encoding="utf-8",errors="strict") as f:
        hdr={}
        for _ in range(6):
            k,v=f.readline().split()[:2]; hdr[k.lower()]=float(v)
        a=np.loadtxt(f,dtype=float)
    return hdr,a

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--relation",type=Path,required=True)
    ap.add_argument("--h1-mvg-zip",type=Path,required=True)
    ap.add_argument("--remaining-zip",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True)

    rel=pd.read_csv(a.relation,low_memory=False)
    lower={str(c).strip().lower():c for c in rel.columns}
    if len(rel)!=EXPECTED_ROWS or rel[lower["hru"]].nunique()!=EXPECTED_HRUS:
        raise ValueError("relation population gate failed")
    hru=pd.to_numeric(rel[lower["hru"]],errors="raise").to_numpy(int)
    x=pd.to_numeric(rel[lower["x"]],errors="raise").to_numpy(float)
    y=pd.to_numeric(rel[lower["y"]],errors="raise").to_numpy(float)

    with tempfile.TemporaryDirectory(prefix="dra_merge_policy_") as td:
        roots={}
        for key,z in (("h1",a.h1_mvg_zip),("remaining",a.remaining_zip)):
            p=Path(td)/key; p.mkdir()
            with ZipFile(z) as zz: zz.extractall(p)
            roots[key]=p
        ref=read_idf(find_one(roots["remaining"],"COND_secundair.IDF"))
        colf=(x-ref.xmin)/ref.dx-.5
        rowf=ref.nrow-(y-ref.ymin)/ref.dy-.5
        cols=np.rint(colf).astype(int); rows=np.rint(rowf).astype(int)
        if not np.allclose(colf,cols,atol=1e-8) or not np.allclose(rowf,rows,atol=1e-8):
            raise ValueError("relation coordinates are not cell centres")

        vals={}
        for key,(root,name) in FILES.items():
            if key=="AHN_cm":
                hdr,g=read_ascii(find_one(roots[root],name))
                vals[key]=g[rows,cols]/100.0
            else:
                g=read_idf(find_one(roots[root],name))
                v=np.asarray(g.values,float)[rows,cols].copy()
                v[~valid(v,g.nodata)]=np.nan
                vals[key]=v

    d=pd.DataFrame({"hru":hru,**vals})
    rows_out=[]
    for hid,g in d.groupby("hru",sort=True):
        rec={"hru":int(hid)}
        for s in ("S","T"):
            c=np.nan_to_num(g[f"{s}_cdr"].to_numpy(float),nan=0.0)
            mask=c>0
            cs=float(c.sum()); rec[f"{s}_G"]=cs
            inf=np.nan_to_num(g[f"{s}_inf"].to_numpy(float),nan=0.0)
            rec[f"{s}_Gi"]=float((c*inf).sum())
            for season in ("sum","win"):
                lev=g[f"{s}_{season}"].to_numpy(float)
                rec[f"{s}_{season}"]=float(np.sum(c[mask]*lev[mask])/cs) if cs else np.nan
                bot=g[f"{s}_bot_{season}"].to_numpy(float)
                rec[f"{s}_bot_{season}"]=float(np.sum(c[mask]*bot[mask])/cs) if cs else np.nan
        for s in ("MVG","OLF"):
            c=np.nan_to_num(g[f"{s}_cdr"].to_numpy(float),nan=0.0)
            mask=c>0; cs=float(c.sum()); rec[f"{s}_G"]=cs
            bot=g[f"{s}_bot"].to_numpy(float)
            rec[f"{s}_level"]=float(np.sum(c[mask]*bot[mask])/cs) if cs else np.nan
        rows_out.append(rec)
    q=pd.DataFrame(rows_out)

    both_st=(q.S_G>0)&(q.T_G>0)
    st=q.loc[both_st].copy()
    st["S_fraction"]=st.S_G/(st.S_G+st.T_G)
    st["summer_span_m"]=(st.S_sum-st.T_sum).abs()
    st["winter_span_m"]=(st.S_win-st.T_win).abs()
    st["bottom_mean_span_m"]=(
        ((st.S_bot_sum+st.S_bot_win)/2)-((st.T_bot_sum+st.T_bot_win)/2)
    ).abs()
    for season in ("sum","win"):
        ld=(st.S_G*st[f"S_{season}"]+st.T_G*st[f"T_{season}"])/(st.S_G+st.T_G)
        gi=st.S_Gi+st.T_Gi
        li=np.where(gi>0,(st.S_Gi*st[f"S_{season}"]+st.T_Gi*st[f"T_{season}"])/gi,ld)
        st[f"{season}_drain_inf_centroid_gap_m"]=np.abs(ld-li)
    st["max_drain_inf_centroid_gap_m"]=st[[
        "sum_drain_inf_centroid_gap_m","win_drain_inf_centroid_gap_m"]].max(axis=1)
    st["max_level_span_m"]=st[["summer_span_m","winter_span_m"]].max(axis=1)

    both_mo=(q.MVG_G>0)&(q.OLF_G>0)
    mo=q.loc[both_mo].copy()
    mo["MVG_fraction"]=mo.MVG_G/(mo.MVG_G+mo.OLF_G)
    mo["level_span_m"]=(mo.MVG_level-mo.OLF_level).abs()
    # Maximum threshold-collapse flux error normalized by total conductance:
    # for two parallel drains this equals f*(1-f)*|z1-z2|.
    mo["normalized_max_flux_error_head_m"]=(
        mo.MVG_fraction*(1-mo.MVG_fraction)*mo.level_span_m
    )

    st.to_csv(a.output_dir/"st_candidate.csv",index=False)
    mo.to_csv(a.output_dir/"mvg_olf_candidate.csv",index=False)
    result={
      "schema_version":1,
      "status":"DRA_MERGE_POLICY_POPULATION_DIAGNOSTIC_NOT_ADMISSION",
      "source_identity":{"relation_sha256":sha256(a.relation),
        "h1_mvg_zip_sha256":sha256(a.h1_mvg_zip),
        "remaining_zip_sha256":sha256(a.remaining_zip)},
      "protected_levels":["H1","PIPE"],
      "S_T":{"both_active_hru":int(len(st)),
        "S_conductance_fraction":quant(st.S_fraction),
        "max_source_level_span_m":quant(st.max_level_span_m),
        "bottom_mean_span_m":quant(st.bottom_mean_span_m),
        "drainage_infiltration_centroid_gap_m":quant(st.max_drain_inf_centroid_gap_m)},
      "MVG_OLF":{"both_active_hru":int(len(mo)),
        "MVG_conductance_fraction":quant(mo.MVG_fraction),
        "source_level_span_m":quant(mo.level_span_m),
        "normalized_max_flux_error_head_m":quant(mo.normalized_max_flux_error_head_m)},
      "interpretation":"Candidate-family evidence only. No fixed merge is admitted by this output."
    }
    (a.output_dir/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return 0

if __name__=="__main__": raise SystemExit(main())
