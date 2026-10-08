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
from tools.dra_protected_compression import select_protected_candidate
from tools.derive_representative_dqsat import derive as derive_representative_dqsat
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


def _same_grid_geometry(a,b) -> bool:
    return (
        a.ncol == b.ncol
        and a.nrow == b.nrow
        and np.isclose(a.xmin,b.xmin)
        and np.isclose(a.xmax,b.xmax)
        and np.isclose(a.ymin,b.ymin)
        and np.isclose(a.ymax,b.ymax)
        and np.isclose(a.dx,b.dx)
        and np.isclose(a.dy,b.dy)
    )


def _assert_ascii_matches_idf(ascii_grid, idf_grid, *, label: str) -> None:
    if (
        ascii_grid.ncols != idf_grid.ncol
        or ascii_grid.nrows != idf_grid.nrow
        or not np.isclose(ascii_grid.xllcorner,idf_grid.xmin)
        or not np.isclose(ascii_grid.yllcorner,idf_grid.ymin)
        or not np.isclose(ascii_grid.cellsize,idf_grid.dx)
        or not np.isclose(idf_grid.dx,idf_grid.dy)
    ):
        raise ValueError(
            f"{label} geometry does not match drainage IDF geometry"
        )


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
    if len(out)==0:
        raise ValueError("empty representative dqsat snapshot")
    if out["hru"].duplicated().any():
        raise ValueError("duplicate HRU in STATIC04 snapshot")
    if (~np.isfinite(out["representative_dqsat"])).any():
        raise ValueError("non-finite representative dqsat in STATIC04 snapshot")
    if "discriminating" not in out.columns:
        out["discriminating"]=False
    elif out["discriminating"].dtype != bool:
        raw=out["discriminating"].astype(str).str.strip().str.lower()
        allowed={"true","false","1","0","yes","no","y","n"}
        bad=~raw.isin(allowed)
        if bad.any():
            raise ValueError(
                "invalid discriminating values in STATIC04 snapshot: "
                + ",".join(sorted(raw[bad].unique())[:10])
            )
        out["discriminating"]=raw.isin({"true","1","yes","y"})
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


def _find_optional_one(root: Path,name: str) -> Path | None:
    matches=list(root.rglob(name))
    if len(matches)>1:
        raise ValueError(f"expected at most one {name} below {root}, got {len(matches)}")
    return matches[0] if matches else None


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
    expected=[
        d.strftime("%Y-%m-%d")
        for d in pd.date_range(start=start,end=end,freq="MS")
    ]
    if keys!=expected:
        missing=sorted(set(expected)-set(keys))
        extra=sorted(set(keys)-set(expected))
        raise ValueError(
            f"H1 stage sequence is not gap-free monthly: "
            f"missing={missing[:10]}, extra={extra[:10]}"
        )
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
    """Map SVAT coordinates only when they are exact IDF cell centres."""
    g=read_idf(reference_idf)
    x=coords["x"].to_numpy(float)
    y=coords["y"].to_numpy(float)
    colf=(x-g.xmin)/g.dx-0.5
    rowf=g.nrow-(y-g.ymin)/g.dy-0.5
    col=np.rint(colf).astype(int)
    row=np.rint(rowf).astype(int)
    if not np.allclose(colf,col,atol=1e-8) or not np.allclose(rowf,row,atol=1e-8):
        raise ValueError("SVAT coordinates are not exact IDF-cell centres")
    if ((row<0)|(row>=g.nrow)|(col<0)|(col>=g.ncol)).any():
        raise ValueError("SVAT coordinates fall outside drainage-grid geometry")
    out=coords.copy()
    out["row"]=row
    out["col"]=col
    return out


def _derive_lhm_bottom_candidates(members: pd.DataFrame) -> pd.DataFrame:
    """Derive explicit static-bottom candidates from LHM seasonal package bottoms.

    P/S/T LHM package semantics expose summer and winter rbot values while SWAP
    method 3 accepts one static ZBOTDR per level. With equal six-month seasonal
    weighting, the arithmetic mean is the least-squares static candidate.
    Deepest and shallowest candidates are retained as a bounded sensitivity
    envelope; no candidate is production-admitted here.
    """
    out=members.copy()
    for system in ("P","S","T"):
        summer=pd.to_numeric(out[f"{system}_bottom_lhm_sum"],errors="coerce")
        winter=pd.to_numeric(out[f"{system}_bottom_lhm_win"],errors="coerce")
        both=summer.notna() & winter.notna()
        mean=pd.Series(np.nan,index=out.index,dtype=float)
        deep=pd.Series(np.nan,index=out.index,dtype=float)
        shallow=pd.Series(np.nan,index=out.index,dtype=float)
        mean.loc[both]=(summer.loc[both]+winter.loc[both])/2.0
        # Elevation: lower value is the deeper channel bottom.
        deep.loc[both]=np.minimum(summer.loc[both],winter.loc[both])
        shallow.loc[both]=np.maximum(summer.loc[both],winter.loc[both])
        out[f"{system}_bottom_lhm_mean"]=mean
        out[f"{system}_bottom_lhm_deepest"]=deep
        out[f"{system}_bottom_lhm_shallowest"]=shallow
        # Baseline diagnostic candidate, not production admission.
        out[f"{system}_bottom"]=mean
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
    historical_bottom_paths={
        "P_bottom_historical_j":_find_optional_one(remaining_bundle,"BODH_P1J_250.IDF"),
        "S_bottom_historical_j":_find_optional_one(remaining_bundle,"BODH_S1J_250.IDF"),
        "T_bottom_historical_j":_find_optional_one(remaining_bundle,"BODH_T1J_250.IDF"),
    }

    reference_grid=read_idf(paths["H1_cdr"])
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
        grid=read_idf(path)
        if not _same_grid_geometry(reference_grid,grid):
            raise ValueError(
                f"{key} geometry does not match H1 drainage reference: {path}"
            )
        mem[key]=_sample(
            np.asarray(grid.values,dtype=float),
            float(grid.nodata),
            rows,
            cols,
        )

    for key,path in historical_bottom_paths.items():
        if path is None:
            continue
        grid=read_idf(path)
        if not _same_grid_geometry(reference_grid,grid):
            raise ValueError(
                f"{key} geometry does not match H1 drainage reference: {path}"
            )
        mem[key]=_sample(
            np.asarray(grid.values,dtype=float),
            float(grid.nodata),
            rows,
            cols,
        )

    # Owner-approved missing seasonal stage -> corresponding package bottom.
    # Apply only on positive-conductance source cells, preserving all valid stages.
    # T's package bottom aliases the stage itself; unresolved T cells stay missing.
    for system in ("P","S","T"):
        active=pd.to_numeric(mem[f"{system}_cdr"],errors="coerce").fillna(0.0)>0.0
        for season,tag in (("sum","Z"),("win","W")):
            stage_col=f"{system}_{season}"
            bottom_col=f"{system}_bottom_lhm_{season}"
            missing=active & mem[stage_col].isna()
            recover=missing & mem[bottom_col].notna()
            mem.loc[recover,stage_col]=mem.loc[recover,bottom_col]
            mem[f"{system}_{season}_stage_bottom_fallback"]=recover
            mem[f"{system}_{season}_stage_unresolved"]=missing & ~recover

    # Owner-approved complete-record selection for P/S/T RIV sources.
    # After seasonal stage-to-bottom recovery, exclude source cells that still
    # lack any required stage/bottom. Preserve raw cdr for provenance.
    for system in ("P","S","T"):
        raw_cdr=pd.to_numeric(mem[f"{system}_cdr"],errors="coerce").fillna(0.0)
        active=raw_cdr>0.0
        required=[
            f"{system}_sum",f"{system}_win",
            f"{system}_bottom_lhm_sum",f"{system}_bottom_lhm_win",
        ]
        complete=mem[required].notna().all(axis=1)
        excluded=active & ~complete
        mem[f"{system}_cdr_raw"]=raw_cdr
        mem[f"{system}_riv_incomplete_excluded"]=excluded
        mem[f"{system}_riv_excluded_conductance"]=raw_cdr.where(excluded,0.0)
        mem.loc[excluded,f"{system}_cdr"]=0.0

    mem=_derive_lhm_bottom_candidates(mem)

    ground=_find_one(remaining_bundle,"ahn_f250_cm.asc")
    gg=read_ascii_grid(ground)
    _assert_ascii_matches_idf(gg,reference_grid,label="AHN ground grid")
    mem["glk"]=_sample(gg.values,gg.nodata,rows,cols)/100.0

    for name in ("MVG","PIPE","OLF"):
        mem[f"{name}_sum"]=mem[f"{name}_bottom"]
        mem[f"{name}_win"]=mem[f"{name}_bottom"]
    return mem


def _aggregate_static(
    group: pd.DataFrame,
    name: str,
    dq: float,
    *,
    bottom_policy: str = "lhm_mean",
) -> dict:
    inf=f"{name}_inf" if name in {"H1","P","S","T"} else None
    if name=="H1":
        summer=winter=None
    else:
        summer=f"{name}_sum"
        winter=f"{name}_win"

    if name in {"P","S","T"}:
        bottom_columns={
            "lhm_mean":f"{name}_bottom_lhm_mean",
            "lhm_deepest":f"{name}_bottom_lhm_deepest",
            "lhm_shallowest":f"{name}_bottom_lhm_shallowest",
            "historical_j":f"{name}_bottom_historical_j",
        }
        if bottom_policy not in bottom_columns:
            raise ValueError(f"unsupported P/S/T bottom policy: {bottom_policy}")
        bottom_col=bottom_columns[bottom_policy]
        if bottom_col not in group.columns:
            raise ValueError(f"bottom policy {bottom_policy} unavailable for {name}")
    else:
        bottom_col=f"{name}_bottom"

    return aggregate_physical_system(
        group,
        cdr_col=f"{name}_cdr",
        bottom_col=bottom_col,
        summer_level_col=summer,
        winter_level_col=winter,
        infiltration_factor_col=inf,
        missing_infiltration_factor_is_zero=(name in {"P","S","T"}),
        representative_dqsat=dq,
    )


def _build_h1_level_matrix(
    members: pd.DataFrame,
    stage_files: list[Path],
    *,
    reference_idf: Path | None = None,
) -> tuple[list[str],np.ndarray,dict[int,str]]:
    """Stream H1 stages once and aggregate monthly level depth per HRU."""
    hru=members["hru"].to_numpy(int)
    max_hru=int(hru.max())
    reference_grid=read_idf(reference_idf) if reference_idf is not None else None
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
        grid=read_idf(path)
        if reference_grid is not None and not _same_grid_geometry(reference_grid,grid):
            raise ValueError(
                f"H1 stage geometry does not match drainage reference: {path}"
            )
        stage=_sample(
            np.asarray(grid.values,dtype=float),
            float(grid.nodata),
            rows,
            cols,
        )
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
        summer=members[f"{system}_bottom_lhm_sum"].to_numpy(float)
        winter=members[f"{system}_bottom_lhm_win"].to_numpy(float)
        valid=np.isfinite(summer)&np.isfinite(winter)
        spread=np.abs(summer[valid]-winter[valid])
        item={
            "seasonal_bottom_spread":{
                "valid_member_rows":int(valid.sum()),
                "different_gt_1e_6":int((spread>1e-6).sum()),
                "mean_abs_difference_m":float(spread.mean()) if len(spread) else None,
                "max_abs_difference_m":float(spread.max()) if len(spread) else None,
            },
            "baseline_static_candidate":"equal_season_mean",
        }
        hist_col=f"{system}_bottom_historical_j"
        if hist_col in members.columns:
            hist=members[hist_col].to_numpy(float)
            comparisons={}
            for label,alt in (
                ("summer",summer),
                ("winter",winter),
                ("mean",members[f"{system}_bottom_lhm_mean"].to_numpy(float)),
            ):
                ok=np.isfinite(hist)&np.isfinite(alt)
                diff=np.abs(hist[ok]-alt[ok])
                comparisons[label]={
                    "valid_member_rows":int(ok.sum()),
                    "different_gt_1e_6":int((diff>1e-6).sum()),
                    "mean_abs_difference_m":float(diff.mean()) if len(diff) else None,
                    "max_abs_difference_m":float(diff.max()) if len(diff) else None,
                }
            item["historical_j"]={"available":True,"comparison":comparisons}
        else:
            item["historical_j"]={"available":False}
        out[system]=item
    return out

def _numeric_quantiles(values: np.ndarray) -> dict:
    if len(values)==0:
        return {"p50":None,"p90":None,"p95":None,"p99":None,"max":None}
    return {
        "p50":float(np.quantile(values,0.50)),
        "p90":float(np.quantile(values,0.90)),
        "p95":float(np.quantile(values,0.95)),
        "p99":float(np.quantile(values,0.99)),
        "max":float(np.max(values)),
    }


def _merge_review_metrics(s: pd.DataFrame,m: pd.DataFrame) -> dict:
    """Review metrics for the bounded seven-to-five population gate."""
    if len(s):
        zero_active=int((s["active_physical_systems"]==0).sum())
        six_active=int((s["active_physical_systems"]==6).sum())
        seven_active=int((s["active_physical_systems"]==7).sum())
    else:
        zero_active=six_active=seven_active=0

    if len(m):
        costs=pd.to_numeric(m["cost"],errors="raise").to_numpy(float)
        quantiles=_numeric_quantiles(costs)
        gaps=pd.to_numeric(
            m["max_drainage_infiltration_level_gap_m"],errors="raise"
        ).to_numpy(float)
        gap_quantiles=_numeric_quantiles(gaps)
        level_spans=pd.to_numeric(
            m["max_source_level_separation_m"],errors="raise"
        ).to_numpy(float)
        level_span_quantiles=_numeric_quantiles(level_spans)
        bottom_spans=pd.to_numeric(
            m["bottom_depth_separation_m"],errors="raise"
        ).to_numpy(float)
        bottom_span_quantiles=_numeric_quantiles(bottom_spans)
        pair_counts={}
        h1_events=0
        h1_gaps=[]
        h1_level_spans=[]
        for row in m.itertuples(index=False):
            left=str(row.left)
            right=str(row.right)
            pair=" | ".join(sorted((left,right)))
            pair_counts[pair]=pair_counts.get(pair,0)+1
            if "H1" in set(left.split("+")) or "H1" in set(right.split("+")):
                h1_events+=1
                h1_gaps.append(float(row.max_drainage_infiltration_level_gap_m))
                h1_level_spans.append(float(row.max_source_level_separation_m))
        top_pairs=[
            {"pair":pair,"count":count}
            for pair,count in sorted(
                pair_counts.items(),key=lambda kv:(-kv[1],kv[0])
            )[:20]
        ]
        positive_gap_events=int((gaps>0.0).sum())
        positive_level_span_events=int((level_spans>0.0).sum())
        h1_gap_quantiles=_numeric_quantiles(np.asarray(h1_gaps,dtype=float))
        h1_level_span_quantiles=_numeric_quantiles(
            np.asarray(h1_level_spans,dtype=float)
        )
    else:
        quantiles=_numeric_quantiles(np.asarray([],dtype=float))
        gap_quantiles=_numeric_quantiles(np.asarray([],dtype=float))
        h1_gap_quantiles=_numeric_quantiles(np.asarray([],dtype=float))
        level_span_quantiles=_numeric_quantiles(np.asarray([],dtype=float))
        bottom_span_quantiles=_numeric_quantiles(np.asarray([],dtype=float))
        h1_level_span_quantiles=_numeric_quantiles(np.asarray([],dtype=float))
        top_pairs=[]
        h1_events=0
        positive_gap_events=0
        positive_level_span_events=0

    return {
        "zero_active_hru":zero_active,
        "six_active_hru":six_active,
        "seven_active_hru":seven_active,
        "h1_merge_event_count":h1_events,
        "merge_cost_quantiles":quantiles,
        "merge_level_representation_tension":{
            "drainage_infiltration_centroid_gap":{
                "metric":"max absolute difference between drainage-equivalent and infiltration-equivalent merged level",
                "unit":"m",
                "acceptance_threshold":None,
                "events_with_positive_gap":positive_gap_events,
                "all_merge_quantiles":gap_quantiles,
                "h1_merge_quantiles":h1_gap_quantiles,
            },
            "source_activation_level_span":{
                "metric":"max separation between the two physical prescribed levels collapsed into one SWAP level",
                "unit":"m",
                "acceptance_threshold":None,
                "events_with_positive_span":positive_level_span_events,
                "all_merge_quantiles":level_span_quantiles,
                "h1_merge_quantiles":h1_level_span_quantiles,
            },
            "bottom_depth_span":{
                "metric":"absolute drainage-bottom depth separation of the merged source pair",
                "unit":"m",
                "acceptance_threshold":None,
                "all_merge_quantiles":bottom_span_quantiles,
            },
        },
        "top_merge_pairs":top_pairs,
    }


def _build_physical_policy(
    group: pd.DataFrame,
    dq: float,
    *,
    bottom_policy: str,
    stage_dates: list[str],
    h1_depths: np.ndarray,
) -> list:
    physical=[]
    for name,cls,medium in SYSTEMS:
        agg=_aggregate_static(group,name,dq,bottom_policy=bottom_policy)
        series=None
        if name=="H1" and agg["cdr_sum"]>0.0:
            if np.isnan(h1_depths).any():
                raise ValueError("incomplete H1 monthly level series")
            series=tuple(
                (key,min(float(depth),float(agg["dep"])))
                for key,depth in zip(stage_dates,h1_depths)
            )
        physical.append(from_aggregate(
            source_id=name,
            hydraulic_class=cls,
            medium=medium,
            aggregate=agg,
            level_series=series,
        ))
    return physical


def _groups_signature(levels) -> str:
    return "|".join("+".join(p.source_ids) for p in levels)


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
    expected_h1_mvg_sha256: str = "3c27cb509dd6d60f5ae8b434fd1ba0f4aca10d81a1b1815b077c5b52a818abfa",
    expected_remaining_sha256: str | None = None,
) -> None:
    output_dir.mkdir(parents=True,exist_ok=True)
    actual_h1=_sha256(h1_mvg_zip)
    actual_remaining=_sha256(remaining_zip)
    if actual_h1.lower()!=expected_h1_mvg_sha256.lower():
        raise ValueError(
            f"H1/MVG bundle SHA mismatch: expected={expected_h1_mvg_sha256} actual={actual_h1}"
        )
    if expected_remaining_sha256 is not None and actual_remaining.lower()!=expected_remaining_sha256.lower():
        raise ValueError(
            "remaining-source bundle SHA mismatch: "
            f"expected={expected_remaining_sha256} actual={actual_remaining}"
        )

    membership,coordinates,relation=_read_relation_context(relation_csv)
    if membership.empty:
        raise ValueError("empty HRU membership")

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
        dqsat_table=derive_representative_dqsat(
            schema,relation,read_dqsat_ascii_grid(dqsat_grid)
        )
        dqsat_table["discriminating"]=False
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
        if hru_count==0:
            raise ValueError("no HRUs in prepared membership")
        membership_hrus=set(int(x) for x in members["hru"].unique())
        dqsat_hrus=set(int(x) for x in dqsat)
        if membership_hrus!=dqsat_hrus:
            missing=sorted(membership_hrus-dqsat_hrus)[:20]
            extra=sorted(dqsat_hrus-membership_hrus)[:20]
            raise ValueError(
                f"representative-dqsat HRU domain mismatch: missing={missing}, extra={extra}"
            )

        stage_files=_h1_stage_files(h1root,stage_start,stage_end)
        stage_dates,h1_matrix,h1_failures=_build_h1_level_matrix(
            members,
            stage_files,
            reference_idf=_find_one(h1root,"COND_HL1_250.IDF"),
        )
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
                h1_depths=h1_matrix[hid]
                physical=_build_physical_policy(
                    group,dq,
                    bottom_policy="lhm_mean",
                    stage_dates=stage_dates,
                    h1_depths=h1_depths,
                )
                active=[p for p in physical if p.active]
                compressed=compress_to_swap_levels(physical,max_levels=5)
                # Parallel qualification route only. Keep historical/generic
                # outputs unchanged until protected policy is admitted.
                try:
                    protected_levels,protected_audit=select_protected_candidate(
                        physical,max_levels=5,
                    )
                    protected_status=protected_audit["status"]
                    protected_groups=_groups_signature(protected_levels)
                    protected_error=protected_audit["max_error_m"]
                except ValueError as protected_exc:
                    protected_status="FAIL_CLOSED"
                    protected_groups=None
                    protected_error=None


                deep=compress_to_swap_levels(
                    _build_physical_policy(
                        group,dq,
                        bottom_policy="lhm_deepest",
                        stage_dates=stage_dates,
                        h1_depths=h1_depths,
                    ),
                    max_levels=5,
                )
                shallow=compress_to_swap_levels(
                    _build_physical_policy(
                        group,dq,
                        bottom_policy="lhm_shallowest",
                        stage_dates=stage_dates,
                        h1_depths=h1_depths,
                    ),
                    max_levels=5,
                )
                mean_groups=_groups_signature(compressed)
                deep_groups=_groups_signature(deep)
                shallow_groups=_groups_signature(shallow)

                historical_groups=None
                historical_available=all(
                    f"{name}_bottom_historical_j" in group.columns
                    for name in ("P","S","T")
                )
                if historical_available:
                    historical=compress_to_swap_levels(
                        _build_physical_policy(
                            group,dq,
                            bottom_policy="historical_j",
                            stage_dates=stage_dates,
                            h1_depths=h1_depths,
                        ),
                        max_levels=5,
                    )
                    historical_groups=_groups_signature(historical)
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
                            "max_drainage_infiltration_level_gap_m":float(
                                event.get("max_drainage_infiltration_level_gap_m",0.0)
                            ),
                            "max_source_level_separation_m":float(
                                event.get("max_source_level_separation_m",0.0)
                            ),
                            "bottom_depth_separation_m":float(
                                event.get("bottom_depth_separation_m",0.0)
                            ),
                            "final_group":"+".join(p.source_ids),
                            "dynamic_dates":0 if p.level_series is None else len(p.level_series),
                        })
                level_dd=[float(p.dd) for p in compressed if p.dd is not None]
                all_levels_same_l=(
                    len(level_dd)<=1
                    or (max(level_dd)-min(level_dd))<=1e-9
                )
                summary.append({
                    "hru":hid,
                    "protected_candidate_status":protected_status,
                    "protected_candidate_groups":protected_groups,
                    "protected_candidate_max_error_m":protected_error,
                    "members":len(group),
                    "active_physical_systems":len(active),
                    "swap_levels":len(compressed),
                    "multiple_swap_levels":len(compressed)>1,
                    "compression_required":len(active)>5,
                    "merge_count":len(costs),
                    "max_merge_cost":max(costs) if costs else 0.0,
                    "drainage_conductance_error":gd1-gd0,
                    "infiltration_conductance_error":gi1-gi0,
                    "legacy_high_resistance_level_count":sum(
                        1 for p in compressed if p.drnres > 20000.0
                    ),
                    "swap_drares_underflow_level_count":sum(
                        1 for p in compressed if p.drnres < 1.0
                    ),
                    "swap_drares_overflow_level_count":sum(
                        1 for p in compressed if p.drnres > 100000.0
                    ),
                    "swap_infres_overflow_level_count":sum(
                        1 for p in compressed if p.infres > 100000.0
                    ),
                    "swap_l_underflow_level_count":sum(
                        1 for p in compressed if p.dd is not None and p.dd < 1.0
                    ),
                    "swap_l_overflow_level_count":sum(
                        1 for p in compressed if p.dd is not None and p.dd > 100000.0
                    ),
                    "swap_zbotdr_range_level_count":sum(
                        1 for p in compressed if not 0.0 <= p.dep <= 100.0
                    ),
                    "max_compressed_drares":max(
                        (float(p.drnres) for p in compressed),
                        default=0.0,
                    ),
                    "max_compressed_infres":max(
                        (float(p.infres) for p in compressed),
                        default=0.0,
                    ),
                    "all_levels_same_L":all_levels_same_l,
                    "level_order":"|".join(
                        f"{'+'.join(p.source_ids)}@dep={p.dep:.9g}@L={float(p.dd):.9g}"
                        for p in compressed
                    ),
                    "groups":mean_groups,
                    "groups_lhm_deepest":deep_groups,
                    "groups_lhm_shallowest":shallow_groups,
                    "bottom_policy_grouping_sensitive":(
                        mean_groups!=deep_groups or mean_groups!=shallow_groups
                    ),
                    "historical_j_bottom_available":historical_available,
                    "groups_historical_j":historical_groups,
                    "historical_j_grouping_differs_from_lhm_mean":(
                        historical_groups is not None and historical_groups!=mean_groups
                    ),
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
    review_metrics=_merge_review_metrics(s,m)
    result={
        "schema_version":2,
        "status":"DRA_POPULATION_DIAGNOSTIC_PASS" if len(f)==0 and len(s)==hru_count else "DRA_POPULATION_DIAGNOSTIC_FAIL",
        "source_identity":{
            "relation_sha256":_sha256(relation_csv),
            "schema_sha256":None if schema_csv is None else _sha256(schema_csv),
            "dqsat_grid_sha256":None if dqsat_grid is None else _sha256(dqsat_grid),
            "dqsat_snapshot_sha256":None if dqsat_snapshot is None else _sha256(dqsat_snapshot),
            "h1_mvg_zip_sha256":actual_h1,
            "remaining_zip_sha256":actual_remaining,
            "remaining_zip_expected_sha256":expected_remaining_sha256,
        },
        "representative_dqsat":{
            "authority":dqsat_authority,
            "hru_count":int(len(dqsat_table)),
            "discriminating_from_legacy_majority_bfe":int(dqsat_table["discriminating"].sum()),
        },
        "hru_expected":hru_count,
        "hru_completed":int(len(s)),
        "hru_failed":int(len(f)),
        "membership_rows":int(len(membership)),
        "h1_stage_date_start":stage_dates[0],
        "h1_stage_date_end":stage_dates[-1],
        "h1_stage_date_count":len(stage_dates),
        "active_system_count_distribution":counts,
        **review_metrics,
        "hru_with_multiple_swap_levels":int(s["multiple_swap_levels"].sum()) if len(s) else 0,
        "hru_with_equal_L_ordering_tie":int(
            (s["multiple_swap_levels"] & s["all_levels_same_L"]).sum()
        ) if len(s) else 0,
        "hru_requiring_compression":int(s["compression_required"].sum()) if len(s) else 0,
        "legacy_v038_high_resistance_deactivation":{
            "threshold_days":20000.0,
            "hru_affected":int((s["legacy_high_resistance_level_count"]>0).sum()) if len(s) else 0,
            "level_count":int(s["legacy_high_resistance_level_count"].sum()) if len(s) else 0,
            "modern_action":"REPORT_ONLY_DO_NOT_DEACTIVATE",
        },
        "swap_method3_interface_range_gate":{
            "DRARES_days":[1.0,100000.0],
            "INFRES_days":[0.0,100000.0],
            "L_m":[1.0,100000.0],
            "ZBOTDR_cm":[-10000.0,0.0],
            "drares_underflow":{
                "hru_count":int((s["swap_drares_underflow_level_count"]>0).sum()) if len(s) else 0,
                "level_count":int(s["swap_drares_underflow_level_count"].sum()) if len(s) else 0,
            },
            "drares_overflow":{
                "hru_count":int((s["swap_drares_overflow_level_count"]>0).sum()) if len(s) else 0,
                "level_count":int(s["swap_drares_overflow_level_count"].sum()) if len(s) else 0,
                "maximum_days":float(s["max_compressed_drares"].max()) if len(s) else None,
            },
            "infres_overflow":{
                "hru_count":int((s["swap_infres_overflow_level_count"]>0).sum()) if len(s) else 0,
                "level_count":int(s["swap_infres_overflow_level_count"].sum()) if len(s) else 0,
                "maximum_days":float(s["max_compressed_infres"].max()) if len(s) else None,
            },
            "L_underflow":{
                "hru_count":int((s["swap_l_underflow_level_count"]>0).sum()) if len(s) else 0,
                "level_count":int(s["swap_l_underflow_level_count"].sum()) if len(s) else 0,
            },
            "L_overflow":{
                "hru_count":int((s["swap_l_overflow_level_count"]>0).sum()) if len(s) else 0,
                "level_count":int(s["swap_l_overflow_level_count"].sum()) if len(s) else 0,
            },
            "ZBOTDR_out_of_range":{
                "hru_count":int((s["swap_zbotdr_range_level_count"]>0).sum()) if len(s) else 0,
                "level_count":int(s["swap_zbotdr_range_level_count"].sum()) if len(s) else 0,
            },
            "required_for_production":"ZERO_INTERFACE_RANGE_VIOLATIONS",
            "rule":"physical values are never silently clamped to SWAP parser ranges",
        },
        "ordering_candidate":"DEEPEST_FIRST_THEN_MEDIUM_THEN_LINEAGE",
        "ordering_admission":"W07_DIAGNOSTIC_ORDERING_QUALIFIED_PRODUCTION_SENSITIVITY_OPEN",
        "ordering_conditions":[
            "DRAMET=3",
            "SWINTFL=0",
            "deterministic deepest-first/medium/lineage serialization is admitted for W07 diagnostic use",
            "bounded SWDIVD ordering sensitivity remains required before production admission",
            "indexed rapid macropore drainage must be absent or explicitly rebound after compression",
        ],
        "merge_event_count":int(len(m)),
        "max_merge_cost":float(s["max_merge_cost"].max()) if len(s) else None,
        "max_abs_drainage_conductance_error":float(s["drainage_conductance_error"].abs().max()) if len(s) else None,
        "max_abs_infiltration_conductance_error":float(s["infiltration_conductance_error"].abs().max()) if len(s) else None,
        "bottom_authority":{
            "baseline_candidate":"LHM_EQUAL_SEASON_MEAN",
            "reason":"equal six-month winter/summer weighting gives the least-squares static ZBOTDR candidate",
            "production_admission":"NOT_GRANTED_PENDING_SENSITIVITY_AND_SWAP_RESPONSE",
            "sensitivity_candidates":["LHM_DEEPEST","LHM_SHALLOWEST"],
            "hru_grouping_sensitive":int(s["bottom_policy_grouping_sensitive"].sum()) if len(s) else 0,
            "historical_j_available_for_all_completed_hrus":bool(
                len(s) and s["historical_j_bottom_available"].all()
            ),
            "historical_j_grouping_differs_from_lhm_mean":int(
                s["historical_j_grouping_differs_from_lhm_mean"].sum()
            ) if len(s) else 0,
        },
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
    p.add_argument("--expected-remaining-sha256")
    p.add_argument("--stage-start",default="1971-01-01")
    p.add_argument("--stage-end",default="2022-01-01")
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
        expected_remaining_sha256=a.expected_remaining_sha256,
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
