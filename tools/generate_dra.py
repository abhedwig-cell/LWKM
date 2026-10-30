"""Active v0.38 drainage aggregation and DRA serialization."""
from __future__ import annotations
from datetime import date
import numpy as np

from tools.p12_swallo import SUPPLIED_SOURCE_V038, swallo, swallo_modern_explicit

_SWAP_MONTH = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")

def conductance_weighted_depth(glk,bottom,cdr):
    import pandas as pd
    g=pd.to_numeric(glk,errors="coerce").to_numpy(float)
    b=pd.to_numeric(bottom,errors="coerce").to_numpy(float)
    c=pd.to_numeric(cdr,errors="coerce").fillna(0).to_numpy(float)
    return float(np.sum(c*(g-b))/np.sum(c)) if np.sum(c)>0 else 0.0

def aggregate_system(members,sy:int,dqsat_maj:float):
    import pandas as pd
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
    summer_level_col: str | None,
    winter_level_col: str | None,
    representative_dqsat: float,
    infiltration_factor_col: str | None = None,
    missing_infiltration_factor_is_zero: bool = False,
    cell_area_m2: float = 62500.0,
) -> dict:
    """Modern all-member aggregation for one named physical drainage system.

    Unlike the historical five-index helper this function has no system-number
    semantics. Every HRU member retains full MODFLOW-cell support.

    Missing hydraulic attributes at a member with positive conductance fail
    closed, except infiltration factors when the explicitly confirmed LHM
    missing-is-zero policy is requested. Drain-only systems pass infiltration_factor_col=None.

    The supplied HRU dqsat follows the owner-selected positive-member median:
    L = 4 * representative_dqsat for an active physical system.
    """
    import pandas as pd
    convert=lambda key:pd.to_numeric(members[key],errors="coerce").to_numpy(float)
    return aggregate_physical_arrays(
        convert("glk"),convert(cdr_col),convert(bottom_col),
        summer=convert(summer_level_col) if summer_level_col else None,
        winter=convert(winter_level_col) if winter_level_col else None,
        dqsat=representative_dqsat,
        infiltration=convert(infiltration_factor_col) if infiltration_factor_col else None,
        missing_infiltration_factor_is_zero=missing_infiltration_factor_is_zero,
        cell_area_m2=cell_area_m2)


def aggregate_physical_arrays(glk,cdr,bottom,*,summer=None,winter=None,dqsat,
                              infiltration=None,missing_infiltration_factor_is_zero=False,
                              cell_area_m2=62500.):
    """Same modern aggregation for NumPy-only server and DataFrame consumers.

    All-member MODFLOW-cell support is retained; area_svat is a different
    MetaSWAP convention. Raw conductances remain available before parser caps.
    """
    glk,cdr,bottom=(np.asarray(v,dtype=float) for v in (glk,cdr,bottom))
    if not len(glk) or cdr.shape!=glk.shape or bottom.shape!=glk.shape:
        raise ValueError('inconsistent physical member arrays')
    if not np.isfinite(glk).all():raise ValueError('missing ground level in HRU membership')
    if np.isinf(cdr).any() or (cdr[np.isfinite(cdr)]<0).any():
        raise ValueError('invalid negative/nonfinite conductance')
    cdr=np.nan_to_num(cdr,nan=0.)
    active=cdr>0
    for name,values in [('bottom',bottom),('summer level',summer),('winter level',winter)]:
        if values is not None and not np.isfinite(np.asarray(values)[active]).all():
            raise ValueError(f'missing {name} for positive-conductance member')
    if (summer is None)!=(winter is None):raise ValueError('summer and winter level columns must both be set or both be None')
    cs=float(cdr.sum());area=float(cell_area_m2)*len(glk)
    if not np.isfinite(area) or area<=0:raise ValueError('invalid support area')
    if infiltration is None:ins=0.
    else:
        inf=np.asarray(infiltration,dtype=float)
        if np.isinf(inf[active]).any() or (inf[active]<0).any():raise ValueError('invalid infiltration factor')
        if np.isnan(inf[active]).any() and not missing_infiltration_factor_is_zero:
            raise ValueError('missing infiltration factor for positive-conductance member')
        ins=float(np.sum(cdr[active]*np.nan_to_num(inf[active],nan=0.)))
    dep=ps=pw=0.;dd=100.
    if cs>0:
        if not np.isfinite(dqsat) or dqsat<=0:raise ValueError('nonpositive/nonfinite dqsat')
        dep=max(0.,float(np.sum(cdr[active]*(glk[active]-bottom[active]))/cs))
        if summer is not None:
            ps=min(max(0.,float(np.sum(cdr[active]*(glk[active]-np.asarray(summer)[active]))/cs)),dep)
            pw=min(max(0.,float(np.sum(cdr[active]*(glk[active]-np.asarray(winter)[active]))/cs)),dep)
        dd=float(dqsat)*4
    return dict(drnres=min(100000.,max(1.,area/cs if cs>0 else 100000.)),
                infres=min(100000.,max(1.,area/ins if ins>0 else 100000.)),
                dd=dd,dep=dep,peil_sum=ps,peil_win=pw,cdr_sum=cs,
                infiltration_conductance_sum=ins,member_count=len(glk),support_area_m2=area)


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



def repair_system_explicit_legacy_v038(
    s: dict,
    *,
    medium: str,
    isnatuur: bool,
) -> dict:
    """Historical v0.38 repair without fixed system-number assumptions."""
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


def repair_system_explicit(
    s: dict,
    *,
    medium: str,
    isnatuur: bool = False,
) -> dict:
    """Modern corrected repair: preserve every physically active level.

    The historical 20000-day threshold and the old nature/pipe heuristic are
    compatibility policies, not modern physical-source authority. SWAP parser
    range checks remain a separate fail-closed production gate.
    """
    if medium not in {"open_channel", "drain_tube"}:
        raise ValueError(f"unsupported drainage medium: {medium}")
    return dict(s)


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

        drnres = float(level["drnres"])
        infres = float(level["infres"])
        spacing = float(level["dd"])
        depth = float(level["dep"])
        zbotdr = -depth * 100.0
        if not 1.0 <= drnres <= 100000.0:
            raise ValueError(
                f"DRARES outside SWAP method-3 range for level {sy}: {drnres}"
            )
        if not 0.0 <= infres <= 100000.0:
            raise ValueError(
                f"INFRES outside SWAP method-3 range for level {sy}: {infres}"
            )
        if not 1.0 <= spacing <= 100000.0:
            raise ValueError(
                f"L outside SWAP method-3 range for level {sy}: {spacing}"
            )
        if not -10000.0 <= zbotdr <= 0.0:
            raise ValueError(
                f"ZBOTDR outside SWAP method-3 range for level {sy}: {zbotdr}"
            )

        swallo_value = swallo_modern_explicit(
            bool(level["allow_infiltration"]),
            infres,
            float(river_infiltration_indicator),
        )
        swdtyp = 1 if medium == "drain_tube" else 2

        def real_token(value):
            token=format(float(value),'.10g')
            return token if any(c in token.lower() for c in '.ed') else token+'.0'
        lines += [
            f"DRARES{sy} = {real_token(drnres)}",
            f"INFRES{sy} = {real_token(infres)}",
            f"SWALLO{sy} = {swallo_value}",
            f"L{sy} = {real_token(spacing)}",
            f"ZBOTDR{sy} = {zbotdr:8.2f}",
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
                level_cm = -float(depth) * 100.0
                if not -10000.0 <= level_cm <= 200.0:
                    raise ValueError(
                        f"LEVEL outside SWAP method-3 range for level {sy}: {level_cm}"
                    )
                lines.append(
                    f" {current.day:02d}-{mon}-{current.year:04d} {level_cm:8.2f}"
                )
        else:
            summer_cm = -float(level["peil_sum"]) * 100.0
            winter_cm = -float(level["peil_win"]) * 100.0
            for value in (summer_cm, winter_cm):
                if not -10000.0 <= value <= 200.0:
                    raise ValueError(
                        f"LEVEL outside SWAP method-3 range for level {sy}: {value}"
                    )
            lines.append(f" 01-jan-{year_start} {winter_cm:8.2f}")
            for y in range(year_start, year_end + 1):
                lines += [
                    f" 01-apr-{y} {summer_cm:8.2f}",
                    f" 01-oct-{y} {winter_cm:8.2f}",
                ]
        lines.append("* End of table")
    return "\n".join(lines) + "\n"
