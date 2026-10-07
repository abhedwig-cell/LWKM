"""Population diagnostic for the modern seven-physical-system DRA pipeline.

Qualification runner only; it does not write production DRA files.

The expensive H1 monthly source is streamed exactly once. Monthly HRU level
series are accumulated with numpy bincount, so the runner is O(number of H1
months) raster reads rather than O(HRUs * months).
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import re
import tempfile

import numpy as np
import pandas as pd

from tools.compare_dqsat_authority import (
    compare_dqsat_authority,
    read_ascii_grid as read_dqsat_ascii_grid,
)
from tools.dra_level_compression import compress_to_swap_levels, from_aggregate
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


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def _valid(values: np.ndarray, nodata: float) -> np.ndarray:
    a=np.asarray(values,dtype=float)
    return np.isfinite(a) & ~np.isclose(a,float(nodata))


def _load_idf_values(path: Path) -> tuple[np.ndarray,float]:
    g=read_idf(path)
    return np.asarray(g.values,dtype=float),float(g.nodata)


def _sample(values: np.ndarray,nodata: float,rows: np.ndarray,cols: np.ndarray) -> np.ndarray:
    out=values[rows,cols].astype(float,copy=True)
    out[~_valid(out,nodata)]=np.nan
    return out


def _read_membership(path: Path) -> pd.DataFrame:
    """Read current export_svat_HRU_NRU_* membership.

    HRUlist2SWAP consumes the first five fields as
    svat, HRU, NRU, NRUcode, svatdonor.
    """
    df=pd.read_csv(path)
    norm={str(c).strip().lower():c for c in df.columns}
    wanted=[
        next((norm[k] for k in norm if k=="svat"),None),
        next((norm[k] for k in norm if k in {"hru","hrunr","hru_nr"}),None),
        next((norm[k] for k in norm if k in {"nru","nrunr","nru_nr"}),None),
        next((norm[k] for k in norm if k in {"nrucode","nru_code"}),None),
        next((norm[k] for k in norm if k in {"svat_donor","svatdonor","donor"}),None),
    ]
    if any(c is None for c in wanted):
        if df.shape[1] < 5:
            raise ValueError("HRU membership must have at least five columns")
        out=df.iloc[:,:5].copy()
    else:
        out=df[wanted].copy()
    out.columns=["svat","hru","nru","nrucode","svatdonor"]
    for col in ("svat","hru","nru","svatdonor"):
        out[col]=pd.to_numeric(out[col],errors="raise").astype(np.int64)
    if out["hru"].min()<1:
        raise ValueError("HRU ids must be positive")
    if out.duplicated(subset=["svat"]).any():
        raise ValueError("membership contains duplicate SVAT ids")
    return out


def _read_relation_context(path: Path) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    """Read the authoritative 10242 SVAT->HRU relation once.

    The same source carries the HRU membership used by HRUlist2SWAP and the
    x/y + original-soil fields required by the already qualified STATIC04
    representative-dqsat derivation.
    """
    full=pd.read_csv(path,low_memory=False)
    membership=_read_membership(path)
    sc=_find_column(full.columns,exact=("svat_orig","svat"))
    xc=_find_column(full.columns,exact=("x","xc(m)","xc"))
    yc=_find_column(full.columns,exact=("y","yc(m)","yc"))
    if sc is None or xc is None or yc is None:
        raise ValueError(
            "authoritative relation must expose svat_orig/svat and x/y coordinates"
        )
    coords=full[[sc,xc,yc]].copy()
    coords.columns=["svat","x","y"]
    coords["svat"]=pd.to_numeric(coords["svat"],errors="raise").astype(np.int64)
    coords["x"]=pd.to_numeric(coords["x"],errors="raise").astype(float)
    coords["y"]=pd.to_numeric(coords["y"],errors="raise").astype(float)
    if coords["svat"].duplicated().any():
        raise ValueError("authoritative relation contains duplicate SVAT ids")
    return membership,coords,full


def _find_column(columns,*,exact=(),contains_all=()):
    norm={str(c).strip().lower():c for c in columns}
    for name in exact:
        if name.lower() in norm:
            return norm[name.lower()]
    for key,c in norm.items():
        if all(token.lower() in key for token in contains_all):
            return c
    return None


def _read_dqsat(
    path: Path,
    *,
    hru_column: str | None = None,
    dqsat_column: str | None = None,
) -> dict[int,float]:
    """Read representative-SVAT dqsat authority for all HRUs."""
    df=pd.read_csv(path)
    hc=hru_column or _find_column(
        df.columns,
        exact=("hru","hru_id","run","run_id"),
        contains_all=("hru",),
    )
    dc=dqsat_column or _find_column(
        df.columns,
        exact=("representative_dqsat","dqsat_repr","repr_dqsat","dqsat"),
        contains_all=("repr","dqsat"),
    )
    if hc is None or dc is None:
        raise ValueError(
            f"cannot identify HRU/representative-dqsat columns in {path}; "
            "supply --dqsat-hru-column and --dqsat-value-column"
        )
    hru=pd.to_numeric(df[hc],errors="raise").astype(int)
    d=pd.to_numeric(df[dc],errors="raise").astype(float)
    if hru.duplicated().any():
        raise ValueError("duplicate HRU in representative dqsat authority")
    if (~np.isfinite(d)).any():
        raise ValueError("non-finite representative dqsat")
    return dict(zip(hru,d))


def _read_static04_snapshot(path: Path) -> pd.DataFrame:
    """Read the persisted qualified STATIC04 representative-dqsat snapshot."""
    df=pd.read_csv(path,low_memory=False)
    required={"hru","representative_dqsat"}
    missing=required.difference(df.columns)
    if missing:
        raise ValueError(f"STATIC04 snapshot missing columns {sorted(missing)}")
    out=df.copy()
    out["hru"]=pd.to_numeric(out["hru"],errors="raise").astype(int)
    out["representative_dqsat"]=pd.to_numeric(
        out["representative_dqsat"],errors="raise"
    ).astype(float)
    if len(out)!=10242:
        raise ValueError(f"expected 10242 STATIC04 rows, got {len(out)}")
    if out["hru"].duplicated().any():
        raise ValueError("duplicate HRU in STATIC04 snapshot")
    if (~np.isfinite(out["representative_dqsat"])).any():
        raise ValueError("non-finite representative dqsat in STATIC04 snapshot")
    if "discriminating" not in out.columns:
        out["discriminating"]=False
    return out.sort_values("hru").reset_index(drop=True)


def _extract_bundle(zip_path: Path,root: Path) -> Path:
    target=root/zip_path.stem
    target.mkdir(parents=True,exist_ok=False)
    with ZipFile(zip_path) as z:
        z.extractall(target)
    return target


def _find_one(root: Path,name: str) -> Path:
    matches=list(root.rglob(name))
    if len(matches)!=1:
        raise ValueError(f"expected exactly one {name} below {root}, got {len(matches)}")
    return matches[0]


def _month_key(path: Path) -> str:
    m=re.search(r"(?i)peilh_(\d{4})(\d{2})(\d{2})\.idf$",path.name)
    if not m:
        raise ValueError(path.name)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def _h1_stage_files(root: Path,start: str,end: str) -> list[Path]:
    pairs=[]
    for p in root.rglob("peilh_*.idf"):
        key=_month_key(p)
        if start<=key<=end:
            pairs.append((key,p))
    pairs.sort()
    if not pairs:
        raise ValueError(f"no H1 stage files in requested period {start}..{end}")
    keys=[k for k,_ in pairs]
    if len(keys)!=len(set(keys)):
        raise ValueError("duplicate H1 stage month")
    return [p for _,p in pairs]


def _read_svat_coordinates(path: Path) -> pd.DataFrame:
    """Read SVAT id and coordinates from SVAT_INFO-style CSV."""
    df=pd.read_csv(path)
    sc=_find_column(df.columns,exact=("svat",))
    xc=_find_column(df.columns,exact=("xc(m)","x","xc"))
    yc=_find_column(df.columns,exact=("yc(m)","y","yc"))
    if sc is None or xc is None or yc is None:
        raise ValueError("SVAT_INFO must expose svat and x/y or xc/yc columns")
    out=df[[sc,xc,yc]].copy()
    out.columns=["svat","x","y"]
    out["svat"]=pd.to_numeric(out["svat"],errors="raise").astype(np.int64)
    out["x"]=pd.to_numeric(out["x"],errors="raise").astype(float)
    out["y"]=pd.to_numeric(out["y"],errors="raise").astype(float)
    if out["svat"].duplicated().any():
        raise ValueError("SVAT_INFO contains duplicate svat ids")
    return out


def _coordinates_to_row_col(coords: pd.DataFrame,reference_idf: Path) -> pd.DataFrame:
    g=read_idf(reference_idf)
    col=np.floor((coords["x"].to_numpy(float)-g.xmin)/g.dx).astype(int)
    row=np.floor((g.ymax-coords["y"].to_numpy(float))/g.dy).astype(int)
    if ((row<0)|(row>=g.nrow)|(col<0)|(col>=g.ncol)).any():
        raise ValueError("SVAT coordinates fall outside drainage-grid geometry")
    out=coords.copy()
    out["row"]=row
    out["col"]=col
    return out


def _prepare_static_members(
    membership: pd.DataFrame,
    coordinates: pd.DataFrame,
    h1_bundle: Path,
    remaining_bundle: Path,
) -> pd.DataFrame:
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
        # In the LHM package INI, tertiary rbot is intentionally bound to
        # the same PEIL_T1Z/W grids rather than a separate BODH_T* source.
        "T_bottom_lhm_sum":_find_one(remaining_bundle,"PEIL_T1Z_250.IDF"),
        "T_bottom_lhm_win":_find_one(remaining_bundle,"PEIL_T1W_250.IDF"),
        "PIPE_cdr":_find_one(remaining_bundle,"COND_buisdrainage.IDF"),
        "PIPE_bottom":_find_one(remaining_bundle,"BODH_B_250.IDF"),
        "OLF_cdr":_find_one(remaining_bundle,"COND_SOF_250.IDF"),
        "OLF_bottom":_find_one(remaining_bundle,"BODH_SOF_250.IDF"),
        "P_bottom_lhm_sum":_find_one(remaining_bundle,"BODH_P1Z_250.IDF"),
        "P_bottom_lhm_win":_find_one(remaining_bundle,"BODH_P1W_250.IDF"),
        "S_bottom_lhm_sum":_find_one(remaining_bundle,"BODH_S1Z_250.IDF"),
        "S_bottom_lhm_win":_find_one(remaining_bundle,"BODH_S1W_250.IDF"),
    }

    coords=_coordinates_to_row_col(coordinates,paths["H1_cdr"])
    mem=membership.merge(coords,on="svat",how="left",validate="many_to_one")
    if mem[["row","col"]].isna().any().any():
        missing=mem.loc[mem["row"].isna(),"svat"].head(10).tolist()
        raise ValueError(f"membership SVAT ids absent from SVAT_INFO: {missing}")
    mem["row"]=mem["row"].astype(int)
    mem["col"]=mem["col"].astype(int)
    rows=mem["row"].to_numpy()
    cols=mem["col"].to_numpy()

    for key,path in paths.items():
        v,nd=_load_idf_values(path)
        mem[key]=_sample(v,nd,rows,cols)

    ground=_find_one(remaining_bundle,"ahn_f250_cm.asc")
    gg=read_ascii_grid(ground)
    mem["glk"]=_sample(gg.values,gg.nodata,rows,cols)/100.0

    for name in ("MVG","PIPE","OLF"):
        mem[f"{name}_sum"]=mem[f"{name}_bottom"]
        mem[f"{name}_win"]=mem[f"{name}_bottom"]
    return mem


def _aggregate_static(group: pd.DataFrame,name: str,dq: float) -> dict:
    inf=f"{name}_inf" if name in {"H1","P","S","T"} else None
    if name=="H1":
        summer=winter=None
    else:
        summer=f"{name}_sum"
        winter=f"{name}_win"
    return aggregate_physical_system(
        group,
        cdr_col=f"{name}_cdr",
        bottom_col=f"{name}_bottom",
        summer_level_col=summer,
        winter_level_col=winter,
        infiltration_factor_col=inf,
        representative_dqsat=dq,
    )


def _build_h1_level_matrix(
    members: pd.DataFrame,
    stage_files: list[Path],
) -> tuple[list[str],np.ndarray,dict[int,str]]:
    """Stream H1 stages once and aggregate monthly level depth per HRU."""
    hru=members["hru"].to_numpy(int)
    max_hru=int(hru.max())
    rows=members["row"].to_numpy(int)
    cols=members["col"].to_numpy(int)
    glk=members["glk"].to_numpy(float)
    cdr=pd.to_numeric(members["H1_cdr"],errors="coerce").fillna(0.0).to_numpy(float)
    active=cdr>0.0
    denominator=np.bincount(hru,weights=cdr,minlength=max_hru+1)
    dates=[_month_key(p) for p in stage_files]
    matrix=np.full((max_hru+1,len(stage_files)),np.nan,dtype=np.float32)
    failures={}

    for j,path in enumerate(stage_files):
        v,nd=_load_idf_values(path)
        stage=_sample(v,nd,rows,cols)
        missing=active & np.isnan(stage)
        if missing.any():
            for hid in np.unique(hru[missing]):
                failures.setdefault(int(hid),f"missing H1 stage in active member at {path.name}")
        safe=np.where(active & ~np.isnan(stage),cdr*(glk-stage),0.0)
        numerator=np.bincount(hru,weights=safe,minlength=max_hru+1)
        ok=denominator>0.0
        matrix[ok,j]=np.maximum(0.0,numerator[ok]/denominator[ok]).astype(np.float32)
    return dates,matrix,failures


def _comparison_stats(members: pd.DataFrame) -> dict:
    out={}
    for system in ("P","S","T"):
        base=members[f"{system}_bottom"].to_numpy(float)
        for season in ("sum","win"):
            alt=members[f"{system}_bottom_lhm_{season}"].to_numpy(float)
            valid=np.isfinite(base)&np.isfinite(alt)
            diff=np.abs(base[valid]-alt[valid])
            out[f"{system}_{season}"]={
                "valid_member_rows":int(valid.sum()),
                "different_gt_1e_6":int((diff>1e-6).sum()),
                "mean_abs_difference_m":float(diff.mean()) if len(diff) else None,
                "max_abs_difference_m":float(diff.max()) if len(diff) else None,
            }
    return out


def diagnose(
    relation_csv: Path,
    h1_mvg_zip: Path,
    remaining_zip: Path,
    output_dir: Path,
    *,
    stage_start: str,
    stage_end: str,
    schema_csv: Path | None = None,
    dqsat_grid: Path | None = None,
    dqsat_snapshot: Path | None = None,
) -> None:
    output_dir.mkdir(parents=True,exist_ok=True)
    membership,coordinates,relation=_read_relation_context(relation_csv)
    if len(membership)!=427656:
        raise ValueError(f"expected 427656 membership rows, got {len(membership)}")

    using_snapshot=dqsat_snapshot is not None
    using_recompute=schema_csv is not None or dqsat_grid is not None
    if using_snapshot == using_recompute:
        raise ValueError(
            "choose exactly one representative-dqsat route: "
            "--dqsat-snapshot OR both --schema and --dqsat-grid"
        )
    if using_snapshot:
        dqsat_table=_read_static04_snapshot(dqsat_snapshot)
        dqsat_authority="STATIC04_PERSISTED_QUALIFIED_SNAPSHOT"
    else:
        if schema_csv is None or dqsat_grid is None:
            raise ValueError("--schema and --dqsat-grid must be supplied together")
        schema=pd.read_csv(schema_csv,low_memory=False)
        dqsat_table=compare_dqsat_authority(
            schema,
            relation,
            read_dqsat_ascii_grid(dqsat_grid),
        )
        if len(dqsat_table)!=10242:
            raise ValueError(
                f"expected 10242 recomputed STATIC04 rows, got {len(dqsat_table)}"
            )
        dqsat_authority="STATIC04_RECOMPUTED_FROM_REPRESENTATIVE_SVAT"
    dqsat=dict(
        zip(
            dqsat_table["hru"].astype(int),
            dqsat_table["representative_dqsat"].astype(float),
        )
    )

    with tempfile.TemporaryDirectory(prefix="lwkm_dra_") as td:
        root=Path(td)
        h1root=_extract_bundle(h1_mvg_zip,root)
        remroot=_extract_bundle(remaining_zip,root)
        members=_prepare_static_members(membership,coordinates,h1root,remroot)

        hru_count=int(members["hru"].nunique())
        if hru_count!=10242:
            raise ValueError(f"expected 10242 HRUs, got {hru_count}")
        membership_hrus=set(int(x) for x in members["hru"].unique())
        dqsat_hrus=set(int(x) for x in dqsat)
        if membership_hrus!=dqsat_hrus:
            missing=sorted(membership_hrus-dqsat_hrus)[:20]
            extra=sorted(dqsat_hrus-membership_hrus)[:20]
            raise ValueError(
                f"representative-dqsat HRU domain mismatch: missing={missing}, extra={extra}"
            )

        stage_files=_h1_stage_files(h1root,stage_start,stage_end)
        stage_dates,h1_matrix,h1_failures=_build_h1_level_matrix(members,stage_files)
        comparison=_comparison_stats(members)

        summary=[]
        merge_events=[]
        failures=[]
        for hru,group in members.groupby("hru",sort=True):
            hid=int(hru)
            try:
                if hid in h1_failures:
                    raise ValueError(h1_failures[hid])
                if hid not in dqsat:
                    raise ValueError("missing representative dqsat")
                dq=float(dqsat[hid])
                physical=[]
                for name,cls,medium in SYSTEMS:
                    agg=_aggregate_static(group,name,dq)
                    series=None
                    if name=="H1" and agg["cdr_sum"]>0.0:
                        row=h1_matrix[hid]
                        if np.isnan(row).any():
                            raise ValueError("incomplete H1 monthly level series")
                        series=tuple(
                            (key,min(float(depth),float(agg["dep"])))
                            for key,depth in zip(stage_dates,row)
                        )
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
                costs=[]
                for p in compressed:
                    for event in p.merge_history:
                        costs.append(float(event["cost"]))
                        merge_events.append({
                            "hru":hid,
                            "left":"+".join(event["left"]),
                            "right":"+".join(event["right"]),
                            "cost":float(event["cost"]),
                            "final_group":"+".join(p.source_ids),
                            "dynamic_dates":0 if p.level_series is None else len(p.level_series),
                        })
                summary.append({
                    "hru":hid,
                    "members":len(group),
                    "active_physical_systems":len(active),
                    "swap_levels":len(compressed),
                    "compression_required":len(active)>5,
                    "merge_count":len(costs),
                    "max_merge_cost":max(costs) if costs else 0.0,
                    "drainage_conductance_error":gd1-gd0,
                    "infiltration_conductance_error":gi1-gi0,
                    "groups":"|".join("+".join(p.source_ids) for p in compressed),
                })
            except Exception as exc:
                failures.append({"hru":hid,"error":str(exc)})

    s=pd.DataFrame(summary)
    m=pd.DataFrame(merge_events)
    f=pd.DataFrame(failures)
    s.to_csv(output_dir/"hru_summary.csv",index=False)
    m.to_csv(output_dir/"merge_events.csv",index=False)
    f.to_csv(output_dir/"failures.csv",index=False)

    counts=(
        {str(int(k)):int(v) for k,v in s["active_physical_systems"].value_counts().sort_index().items()}
        if len(s) else {}
    )
    result={
        "schema_version":2,
        "status":"DRA_10242_DIAGNOSTIC_PASS" if len(f)==0 and len(s)==10242 else "DRA_10242_DIAGNOSTIC_FAIL",
        "source_identity":{
            "relation_sha256":_sha256(relation_csv),
            "schema_sha256":None if schema_csv is None else _sha256(schema_csv),
            "dqsat_grid_sha256":None if dqsat_grid is None else _sha256(dqsat_grid),
            "dqsat_snapshot_sha256":None if dqsat_snapshot is None else _sha256(dqsat_snapshot),
            "h1_mvg_zip_sha256":_sha256(h1_mvg_zip),
            "remaining_zip_sha256":_sha256(remaining_zip),
        },
        "representative_dqsat":{
            "authority":dqsat_authority,
            "hru_count":int(len(dqsat_table)),
            "discriminating_from_legacy_majority_bfe":int(dqsat_table["discriminating"].sum()),
        },
        "hru_expected":10242,
        "hru_completed":int(len(s)),
        "hru_failed":int(len(f)),
        "membership_rows":int(len(membership)),
        "h1_stage_date_start":stage_dates[0],
        "h1_stage_date_end":stage_dates[-1],
        "h1_stage_date_count":len(stage_dates),
        "active_system_count_distribution":counts,
        "hru_requiring_compression":int(s["compression_required"].sum()) if len(s) else 0,
        "merge_event_count":int(len(m)),
        "max_merge_cost":float(s["max_merge_cost"].max()) if len(s) else None,
        "max_abs_drainage_conductance_error":float(s["drainage_conductance_error"].abs().max()) if len(s) else None,
        "max_abs_infiltration_conductance_error":float(s["infiltration_conductance_error"].abs().max()) if len(s) else None,
        "bottom_authority_comparison":comparison,
        "outputs":{
            "hru_summary":"hru_summary.csv",
            "merge_events":"merge_events.csv",
            "failures":"failures.csv",
        },
    }
    (output_dir/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--relation",type=Path,required=True,
                   help="authoritative export_svat_HRU_NRU_10242.csv")
    p.add_argument("--schema",type=Path,
                   help="authoritative export_HRUschema_10242_copy.csv; use with --dqsat-grid")
    p.add_argument("--dqsat-grid",type=Path,
                   help="qualified grensvlak_NHIWQ_v2_fill.asc; use with --schema")
    p.add_argument("--dqsat-snapshot",type=Path,
                   help="qualified static04_dqsat_full_10242.csv replay snapshot")
    p.add_argument("--h1-mvg-zip",type=Path,required=True)
    p.add_argument("--remaining-zip",type=Path,required=True)
    p.add_argument("--stage-start",default="1971-01-01")
    p.add_argument("--stage-end",default="2021-12-01")
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    diagnose(
        a.relation,
        a.h1_mvg_zip,
        a.remaining_zip,
        a.output_dir,
        stage_start=a.stage_start,
        stage_end=a.stage_end,
        schema_csv=a.schema,
        dqsat_grid=a.dqsat_grid,
        dqsat_snapshot=a.dqsat_snapshot,
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
