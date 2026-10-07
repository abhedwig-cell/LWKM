"""Population diagnostic for the modern seven-physical-system DRA pipeline.

This is a qualification/diagnostic runner, not yet a production DRA packager.

Inputs are deliberately explicit:
- current 5-column HRU membership CSV;
- SVAT raster used to map SVAT ids to model cells;
- representative-SVAT dqsat table or CSV;
- H1/MVG Q4 bundle;
- remaining-five Q4 bundle.

The runner reports:
- active physical-system count per HRU;
- HRUs requiring 7->5 compression;
- selected merge groups;
- exact conductance-conservation errors;
- H1/MVG missing-source intersections;
- bottom/level shifts caused by compression.

It fails closed on positive-conductance members with missing required hydraulic
attributes. No historical fallback is silently applied.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from zipfile import ZipFile
import argparse
import csv
import json
import math
import re
import tempfile

import numpy as np
import pandas as pd

from tools.dra_level_compression import (
    PhysicalDrainageSystem,
    compress_to_swap_levels,
    from_aggregate,
)
from tools.generate_dra import aggregate_physical_system
from tools.idf_reader import read_idf
from tools.lhm_postprocess import read_ascii_grid


SYSTEMS = (
    ("H1", "infiltration_capable_open", "open_channel"),
    ("P", "infiltration_capable_open", "open_channel"),
    ("S", "infiltration_capable_open", "open_channel"),
    ("T", "infiltration_capable_open", "open_channel"),
    ("MVG", "drain_only_open", "open_channel"),
    ("PIPE", "pipe", "drain_tube"),
    ("OLF", "drain_only_open", "open_channel"),
)


def _valid(values: np.ndarray, nodata: float) -> np.ndarray:
    a=np.asarray(values,dtype=float)
    return np.isfinite(a) & ~np.isclose(a,float(nodata))


def _load_idf_values(path: Path) -> tuple[np.ndarray,float]:
    g=read_idf(path)
    return np.asarray(g.values,dtype=float),float(g.nodata)


def _sample(values: np.ndarray,nodata: float,rows: np.ndarray,cols: np.ndarray) -> np.ndarray:
    out=values[rows,cols].astype(float,copy=True)
    valid=_valid(out,nodata)
    out[~valid]=np.nan
    return out


def _svat_locations(svat_grid: Path) -> pd.DataFrame:
    g=read_ascii_grid(svat_grid)
    vals=np.asarray(g.values)
    valid=np.isfinite(vals) & ~np.isclose(vals,g.nodata) & (vals>0)
    row,col=np.where(valid)
    svat=vals[row,col].astype(np.int64)
    if len(np.unique(svat)) != len(svat):
        raise ValueError("SVAT raster contains duplicate positive SVAT ids")
    return pd.DataFrame({"svat":svat,"row":row.astype(int),"col":col.astype(int)})


def _read_membership(path: Path) -> pd.DataFrame:
    # Current HRUlist2SWAP reads the first five fields as:
    # svat, HRU, NRU, NRUcode, svatdonor.
    df=pd.read_csv(path)
    if df.shape[1] < 5:
        df=pd.read_csv(path,header=None)
    if df.shape[1] < 5:
        raise ValueError("HRU membership must have at least five columns")
    df=df.iloc[:,:5].copy()
    df.columns=["svat","hru","nru","nrucode","svatdonor"]
    for c in ("svat","hru","nru","svatdonor"):
        df[c]=pd.to_numeric(df[c],errors="raise").astype(np.int64)
    if df["hru"].min()<1:
        raise ValueError("HRU ids must be positive")
    return df


def _read_dqsat(path: Path) -> dict[int,float]:
    df=pd.read_csv(path)
    lower={str(c).lower():c for c in df.columns}
    hru_col=next((lower[k] for k in lower if k in {"hru","hru_id","run","run_id"}),None)
    d_col=next((lower[k] for k in lower if "repr" in k and "dqsat" in k),None)
    if d_col is None:
        d_col=next((lower[k] for k in lower if k in {"dqsat","dqsat_repr","representative_dqsat"}),None)
    if hru_col is None or d_col is None:
        raise ValueError(f"cannot identify HRU/representative dqsat columns in {path}")
    hru=pd.to_numeric(df[hru_col],errors="raise").astype(int)
    d=pd.to_numeric(df[d_col],errors="raise").astype(float)
    if hru.duplicated().any():
        raise ValueError("duplicate HRU in representative dqsat authority")
    return dict(zip(hru,d))


def _extract_bundle(zip_path: Path,root: Path) -> Path:
    target=root/zip_path.stem
    target.mkdir(parents=True,exist_ok=False)
    with ZipFile(zip_path) as z:
        z.extractall(target)
    return target


def _find_one(root: Path,name: str) -> Path:
    m=list(root.rglob(name))
    if len(m)!=1:
        raise ValueError(f"expected exactly one {name} below {root}, got {len(m)}")
    return m[0]


def _h1_stage_files(root: Path) -> list[Path]:
    files=sorted(root.rglob("peilh_*.idf"))
    if not files:
        raise ValueError("no H1 peilh_*.idf in H1/MVG bundle")
    return files


def _month_key(path: Path) -> str:
    m=re.search(r"(?i)peilh_(\d{4})(\d{2})(\d{2})\.idf$",path.name)
    if not m:
        raise ValueError(path.name)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _prepare_static_members(
    membership: pd.DataFrame,
    svat_grid: Path,
    h1_bundle: Path,
    remaining_bundle: Path,
) -> tuple[pd.DataFrame,dict[str,list[Path]]]:
    loc=_svat_locations(svat_grid)
    mem=membership.merge(loc,on="svat",how="left",validate="many_to_one")
    if mem[["row","col"]].isna().any().any():
        missing=mem.loc[mem["row"].isna(),"svat"].head(10).tolist()
        raise ValueError(f"membership SVAT ids absent from SVAT raster: {missing}")
    mem["row"]=mem["row"].astype(int)
    mem["col"]=mem["col"].astype(int)
    rows=mem["row"].to_numpy()
    cols=mem["col"].to_numpy()

    paths={
        "H1_cdr":_find_one(h1_bundle,"COND_HL1_250.IDF"),
        "H1_bottom":_find_one(h1_bundle,"both.idf"),
        "H1_inf":_find_one(h1_bundle,"infmz_h_250_l1.idf"),
        "MVG_cdr":_find_one(h1_bundle,"COND_greppels.IDF"),
        "MVG_bottom":_find_one(h1_bundle,"BODH_BRP2012_MVGREP_250.IDF"),
        "P_cdr":_find_one(remaining_bundle,"COND_primair.IDF"),
        "S_cdr":_find_one(remaining_bundle,"COND_secundair.IDF"),
        "T_cdr":_find_one(remaining_bundle,"COND_tertiair.IDF"),
        "P_inf":_find_one(remaining_bundle,"inf_mz_primair.IDF"),
        "S_inf":_find_one(remaining_bundle,"inf_mz_secundair.IDF"),
        "T_inf":_find_one(remaining_bundle,"inf_mz_tertiair.IDF"),
        "P_bottom":_find_one(remaining_bundle,"BODH_P1J_250.IDF"),
        "S_bottom":_find_one(remaining_bundle,"BODH_S1J_250.IDF"),
        "T_bottom":_find_one(remaining_bundle,"BODH_T1J_250.IDF"),
        "P_sum":_find_one(remaining_bundle,"PEIL_P1Z_250.IDF"),
        "P_win":_find_one(remaining_bundle,"PEIL_P1W_250.IDF"),
        "S_sum":_find_one(remaining_bundle,"PEIL_S1Z_250.IDF"),
        "S_win":_find_one(remaining_bundle,"PEIL_S1W_250.IDF"),
        "T_sum":_find_one(remaining_bundle,"PEIL_T1Z_250.IDF"),
        "T_win":_find_one(remaining_bundle,"PEIL_T1W_250.IDF"),
        "PIPE_cdr":_find_one(remaining_bundle,"COND_buisdrainage.IDF"),
        "PIPE_bottom":_find_one(remaining_bundle,"BODH_B_250.IDF"),
        "OLF_cdr":_find_one(remaining_bundle,"COND_SOF_250.IDF"),
        "OLF_bottom":_find_one(remaining_bundle,"BODH_SOF_250.IDF"),
    }

    for key,path in paths.items():
        v,nd=_load_idf_values(path)
        mem[key]=_sample(v,nd,rows,cols)

    ground=_find_one(remaining_bundle,"ahn_f250_cm.asc")
    gg=read_ascii_grid(ground)
    mem["glk"]=_sample(gg.values,gg.nodata,rows,cols)/100.0

    # Drain-only level equals bottom/stage source.
    mem["MVG_sum"]=mem["MVG_bottom"]
    mem["MVG_win"]=mem["MVG_bottom"]
    mem["PIPE_sum"]=mem["PIPE_bottom"]
    mem["PIPE_win"]=mem["PIPE_bottom"]
    mem["OLF_sum"]=mem["OLF_bottom"]
    mem["OLF_win"]=mem["OLF_bottom"]

    return mem,{"H1_stage":_h1_stage_files(h1_bundle)}


def _aggregate_static(
    group: pd.DataFrame,
    name: str,
    representative_dqsat: float,
) -> dict:
    inf=f"{name}_inf" if name in {"H1","P","S","T"} else None
    return aggregate_physical_system(
        group,
        cdr_col=f"{name}_cdr",
        bottom_col=f"{name}_bottom",
        summer_level_col=f"{name}_sum",
        winter_level_col=f"{name}_win",
        infiltration_factor_col=inf,
        representative_dqsat=representative_dqsat,
    )


def _h1_series_for_hru(
    group: pd.DataFrame,
    stage_files: list[Path],
) -> tuple[tuple[str,float],...]:
    cdr=pd.to_numeric(group["H1_cdr"],errors="coerce").fillna(0).to_numpy(float)
    active=cdr>0
    if not active.any():
        return ()
    rows=group["row"].to_numpy(int)
    cols=group["col"].to_numpy(int)
    glk=group["glk"].to_numpy(float)
    total=float(cdr.sum())
    out=[]
    for path in stage_files:
        v,nd=_load_idf_values(path)
        stage=_sample(v,nd,rows,cols)
        if np.isnan(stage[active]).any():
            raise ValueError(f"missing H1 stage in active HRU member for {path.name}")
        depth=float(np.sum(cdr*(glk-stage))/total)
        out.append((_month_key(path),max(0.0,depth)))
    return tuple(out)


def diagnose(
    membership_csv: Path,
    svat_grid: Path,
    dqsat_csv: Path,
    h1_mvg_zip: Path,
    remaining_zip: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True,exist_ok=True)
    membership=_read_membership(membership_csv)
    dqsat=_read_dqsat(dqsat_csv)

    with tempfile.TemporaryDirectory(prefix="lwkm_dra_") as td:
        root=Path(td)
        h1root=_extract_bundle(h1_mvg_zip,root)
        remroot=_extract_bundle(remaining_zip,root)
        members,extra=_prepare_static_members(membership,svat_grid,h1root,remroot)

        if members["hru"].nunique()!=10242:
            raise ValueError(f"expected 10242 HRUs, got {members['hru'].nunique()}")

        summary=[]
        merges=[]
        failures=[]
        for hru,group in members.groupby("hru",sort=True):
            try:
                if int(hru) not in dqsat:
                    raise ValueError("missing representative dqsat")
                dq=float(dqsat[int(hru)])
                physical=[]
                for name,cls,medium in SYSTEMS:
                    agg=_aggregate_static(group,name,dq)
                    series=None
                    if name=="H1" and agg["cdr_sum"]>0:
                        series=_h1_series_for_hru(group,extra["H1_stage"])
                    physical.append(from_aggregate(
                        source_id=name,
                        hydraulic_class=cls,
                        medium=medium,
                        aggregate=agg,
                        level_series=series,
                    ))

                active=[p for p in physical if p.active]
                compressed=compress_to_swap_levels(physical,max_levels=5)
                gd0=sum(p.drainage_conductance for p in active)
                gd1=sum(p.drainage_conductance for p in compressed)
                gi0=sum(p.infiltration_conductance for p in active)
                gi1=sum(p.infiltration_conductance for p in compressed)
                summary.append({
                    "hru":int(hru),
                    "members":len(group),
                    "active_physical_systems":len(active),
                    "swap_levels":len(compressed),
                    "compression_required":len(active)>5,
                    "drainage_conductance_error":gd1-gd0,
                    "infiltration_conductance_error":gi1-gi0,
                    "groups":"|".join("+".join(p.source_ids) for p in compressed),
                })
                for p in compressed:
                    if len(p.source_ids)>1:
                        merges.append({
                            "hru":int(hru),
                            "sources":"+".join(p.source_ids),
                            "drnres":p.drnres,
                            "infres":p.infres,
                            "dep":p.dep,
                            "dd":p.dd,
                            "dynamic_dates":0 if p.level_series is None else len(p.level_series),
                        })
            except Exception as exc:
                failures.append({"hru":int(hru),"error":str(exc)})

    s=pd.DataFrame(summary)
    m=pd.DataFrame(merges)
    f=pd.DataFrame(failures)
    s.to_csv(output_dir/"hru_summary.csv",index=False)
    m.to_csv(output_dir/"merge_events.csv",index=False)
    f.to_csv(output_dir/"failures.csv",index=False)

    counts={str(int(k)):int(v) for k,v in s["active_physical_systems"].value_counts().sort_index().items()} if len(s) else {}
    result={
        "schema_version":1,
        "status":"DRA_10242_DIAGNOSTIC_PASS" if len(f)==0 and len(s)==10242 else "DRA_10242_DIAGNOSTIC_FAIL",
        "hru_expected":10242,
        "hru_completed":int(len(s)),
        "hru_failed":int(len(f)),
        "active_system_count_distribution":counts,
        "hru_requiring_compression":int(s["compression_required"].sum()) if len(s) else 0,
        "merge_event_count":int(len(m)),
        "max_abs_drainage_conductance_error":float(s["drainage_conductance_error"].abs().max()) if len(s) else None,
        "max_abs_infiltration_conductance_error":float(s["infiltration_conductance_error"].abs().max()) if len(s) else None,
        "outputs":{
            "hru_summary":"hru_summary.csv",
            "merge_events":"merge_events.csv",
            "failures":"failures.csv",
        },
    }
    (output_dir/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--membership",type=Path,required=True)
    p.add_argument("--svat-grid",type=Path,required=True)
    p.add_argument("--dqsat",type=Path,required=True)
    p.add_argument("--h1-mvg-zip",type=Path,required=True)
    p.add_argument("--remaining-zip",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    diagnose(a.membership,a.svat_grid,a.dqsat,a.h1_mvg_zip,a.remaining_zip,a.output_dir)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
