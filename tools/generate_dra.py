"""Active v0.38 drainage aggregation and DRA serialization."""
from __future__ import annotations
from datetime import date
import numpy as np
import pandas as pd

from tools.p12_swallo import SUPPLIED_SOURCE_V038, swallo, swallo_modern_explicit

_SWAP_MONTH = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")

def conductance_weighted_depth(glk,bottom,cdr):
    g=pd.to_numeric(glk,errors="coerce").to_numpy(float)
    b=pd.to_numeric(bottom,errors="coerce").to_numpy(float)
    c=pd.to_numeric(cdr,errors="coerce").fillna(0).to_numpy(float)
    return float(np.sum(c*(g-b))/np.sum(c)) if np.sum(c)>0 else 0.0

def aggregate_system(members,sy:int,dqsat_maj:float):
    cdr=pd.to_numeric(members[f"cdr{sy}"],errors="coerce").fillna(0)
    inf=pd.to_numeric(members[f"inf{sy}"],errors="coerce").fillna(0)
    n=len(members);cs=float(cdr.sum());ins=float((cdr*inf).sum())
    leng=float(pd.to_numeric(members[f"leng{sy}"],errors="coerce").fillna(0).sum())
    dd=float(dqsat_maj)*4 if leng>0 else 100.0
    dra=min(100000.0,max(1.0,62500.0*n/cs if cs>0 else 100000.0))
    infres=min(100000.0,max(1.0,62500.0*n/ins if ins>0 else 100000.0))
    dep=conductance_weighted_depth(members["glk"],members[f"bodh{sy}"],cdr)
    glkavg=float(pd.to_numeric(members["glk"],errors="coerce").mean())
    ps=glkavg-conductance_weighted_depth(members["glk"],members[f"peil_sum{sy}"],cdr)
    pw=glkavg-conductance_weighted_depth(members["glk"],members[f"peil_win{sy}"],cdr)
    # Historical repair converts levels to positive depth below surface and caps by drainage depth.
    ps=min(max(0.0,-ps+glkavg),max(0.0,dep));pw=min(max(0.0,-pw+glkavg),max(0.0,dep));dep=max(0.0,dep)
    return {"drnres":dra,"infres":infres,"dd":dd,"dep":dep,"peil_sum":ps,"peil_win":pw}

def aggregate_physical_system(
    members,
    *,
    cdr_col: str,
    bottom_col: str,
    summer_level_col: str,
    winter_level_col: str,
    representative_dqsat: float,
    infiltration_factor_col: str | None = None,
    cell_area_m2: float = 62500.0,
) -> dict:
    """Modern all-member aggregation for one named physical drainage system.

    Unlike the historical five-index helper this function has no system-number
    semantics. Every HRU member retains full MODFLOW-cell support.

    Missing hydraulic attributes at a member with positive conductance fail
    closed. Drain-only systems pass infiltration_factor_col=None.

    Modern L/spacing authority is representative-SVAT dqsat:
    L = 4 * representative_dqsat for an active physical system.
    """
    glk = pd.to_numeric(members["glk"], errors="coerce")
    cdr = pd.to_numeric(members[cdr_col], errors="coerce")
    bottom = pd.to_numeric(members[bottom_col], errors="coerce")
    summer = pd.to_numeric(members[summer_level_col], errors="coerce")
    winter = pd.to_numeric(members[winter_level_col], errors="coerce")

    if glk.isna().any():
        raise ValueError("missing ground level in HRU membership")

    active_member = cdr.fillna(0.0) > 0.0
    if cdr[active_member].isna().any():
        raise ValueError(f"missing conductance in active {cdr_col} member")
    if bottom[active_member].isna().any():
        raise ValueError(f"missing bottom for positive-conductance {cdr_col} member")
    if summer[active_member].isna().any():
        raise ValueError(f"missing summer level for positive-conductance {cdr_col} member")
    if winter[active_member].isna().any():
        raise ValueError(f"missing winter level for positive-conductance {cdr_col} member")

    cdr = cdr.fillna(0.0).clip(lower=0.0)
    cdr_sum = float(cdr.sum())
    n = len(members)
    area = float(cell_area_m2) * n

    if infiltration_factor_col is None:
        infiltration_sum = 0.0
        infres = 100000.0
    else:
        inf = pd.to_numeric(members[infiltration_factor_col], errors="coerce")
        if inf[active_member].isna().any():
            raise ValueError(
                f"missing infiltration factor for positive-conductance {cdr_col} member"
            )
        inf = inf.fillna(0.0).clip(lower=0.0)
        infiltration_sum = float((cdr * inf).sum())
        infres = min(
            100000.0,
            max(1.0, area / infiltration_sum if infiltration_sum > 0.0 else 100000.0),
        )

    drnres = min(
        100000.0,
        max(1.0, area / cdr_sum if cdr_sum > 0.0 else 100000.0),
    )

    if cdr_sum > 0.0:
        dep = conductance_weighted_depth(glk, bottom, cdr)
        glkavg = float(glk.mean())
        ps = glkavg - conductance_weighted_depth(glk, summer, cdr)
        pw = glkavg - conductance_weighted_depth(glk, winter, cdr)
        ps = min(max(0.0, -ps + glkavg), max(0.0, dep))
        pw = min(max(0.0, -pw + glkavg), max(0.0, dep))
        dep = max(0.0, dep)
        dd = float(representative_dqsat) * 4.0
    else:
        dep = 0.0
        ps = 0.0
        pw = 0.0
        dd = 100.0

    return {
        "drnres": drnres,
        "infres": infres,
        "dd": dd,
        "dep": dep,
        "peil_sum": ps,
        "peil_win": pw,
        "cdr_sum": cdr_sum,
        "infiltration_conductance_sum": infiltration_sum,
        "member_count": n,
    }


def repair_system(s:dict,sy:int,isnatuur:bool)->dict:
    x=dict(s)
    if x["drnres"]>20000 or (sy==4 and isnatuur):
        x.update({"peil_sum":0.0,"peil_win":0.0,"dep":0.0,"drnres":100000.0,"infres":100000.0})
    return x

def render_dra(systems:list[dict],n_horizons:int,year_start:int,year_end:int,infil_avg:float,*,swallo_mode:str=SUPPLIED_SOURCE_V038)->str:
    lines=["DRAMET = 3","SWDIVD = 1","COFANI ="+" 1.0"*int(n_horizons),"SWDISLAY = 0","NRLEVS = 5","SWINTFL = 0","SWTOPNRSRF = 0",""]
    for sy,s in enumerate(systems,1):
        swallo_value=swallo(sy,s["infres"],infil_avg,mode=swallo_mode)
        lines += [f"DRARES{sy} = {s['drnres']:8.0f}",f"INFRES{sy} = {s['infres']:8.0f}",
                  f"SWALLO{sy} = {swallo_value}",f"L{sy} = {max(1.0,s['dd']):8.0f}",
                  f"ZBOTDR{sy} = {-s['dep']*100:8.2f}",f"SWDTYP{sy} = {1 if sy==4 else 2}"," ",
                  f"    DATOWL{sy}   LEVEL{sy}",f" 01-jan-{year_start} {-s['peil_win']*100:8.2f}"]
        for y in range(year_start,year_end+1):
            lines += [f" 01-apr-{y} {-s['peil_sum']*100:8.2f}",f" 01-oct-{y} {-s['peil_win']*100:8.2f}"]
        lines.append("* End of table")
    return "\n".join(lines)+"\n"



def repair_system_explicit(s: dict, *, medium: str, isnatuur: bool) -> dict:
    """Modern repair semantics with hydraulic type explicit, not index-coded."""
    if medium not in {"open_channel", "drain_tube"}:
        raise ValueError(f"unsupported drainage medium: {medium}")
    x = dict(s)
    if x["drnres"] > 20000 or (medium == "drain_tube" and isnatuur):
        x.update({
            "peil_sum": 0.0,
            "peil_win": 0.0,
            "dep": 0.0,
            "drnres": 100000.0,
            "infres": 100000.0,
        })
    return x


def render_dra_explicit(
    levels: list[dict],
    n_horizons: int,
    year_start: int,
    year_end: int,
    river_infiltration_indicator: float,
) -> str:
    """Render <=5 SWAP drainage levels using explicit hydraulic metadata.

    Each level must contain:
      drnres, infres, dd, dep, peil_sum, peil_win,
      medium = open_channel | drain_tube,
      allow_infiltration = bool,
      source_ids = iterable[str] (lineage only).

    This avoids the historical index assumptions sy==4 => pipe and sy>3 =>
    drain-only. Final L/spacing admission remains a separate gate.
    """
    if not 1 <= len(levels) <= 5:
        raise ValueError(f"SWAP supports 1..5 drainage levels, got {len(levels)}")

    lines = [
        "DRAMET = 3",
        "SWDIVD = 1",
        "COFANI =" + " 1.0" * int(n_horizons),
        "SWDISLAY = 0",
        f"NRLEVS = {len(levels)}",
        "SWINTFL = 0",
        "SWTOPNRSRF = 0",
        "",
    ]

    for sy, level in enumerate(levels, 1):
        medium = level["medium"]
        if medium not in {"open_channel", "drain_tube"}:
            raise ValueError(f"unsupported drainage medium: {medium}")
        swallo_value = swallo_modern_explicit(
            bool(level["allow_infiltration"]),
            float(level["infres"]),
            float(river_infiltration_indicator),
        )
        swdtyp = 1 if medium == "drain_tube" else 2

        lines += [
            f"DRARES{sy} = {level['drnres']:8.0f}",
            f"INFRES{sy} = {level['infres']:8.0f}",
            f"SWALLO{sy} = {swallo_value}",
            f"L{sy} = {max(1.0, level['dd']):8.0f}",
            f"ZBOTDR{sy} = {-level['dep'] * 100:8.2f}",
            f"SWDTYP{sy} = {swdtyp}",
            " ",
            f"    DATOWL{sy}   LEVEL{sy}",
        ]

        series = level.get("level_series")
        if series:
            previous = None
            for key, depth in series:
                current = date.fromisoformat(key)
                if previous is not None and current <= previous:
                    raise ValueError(f"level_series must be strictly increasing: {key}")
                previous = current
                mon = _SWAP_MONTH[current.month - 1]
                lines.append(
                    f" {current.day:02d}-{mon}-{current.year:04d} {-float(depth) * 100:8.2f}"
                )
        else:
            lines.append(f" 01-jan-{year_start} {-level['peil_win'] * 100:8.2f}")
            for y in range(year_start, year_end + 1):
                lines += [
                    f" 01-apr-{y} {-level['peil_sum'] * 100:8.2f}",
                    f" 01-oct-{y} {-level['peil_win'] * 100:8.2f}",
                ]
        lines.append("* End of table")
    return "\n".join(lines) + "\n"
