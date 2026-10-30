"""Actual MetaSWAP area_svat.inp areas, joined by original SVAT ID and XY.

Uses the same 14-column layout as the existing native MetaSWAP HRU producer.
The comparison membership area is never used as a fallback.
"""
from collections import defaultdict
from datetime import date
import hashlib
import math
from pathlib import Path

OWNER_AREA_SHA256='352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc'
PERIODS=[(1970,1979),(1980,1989),(1990,1999),(2000,2009),(2010,2019),(2020,2022)]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def read_area_svat(path,members):
    selected={int(r['svat']):r for r in members}
    if len(selected)!=len(members):raise ValueError('duplicate SVAT membership')
    areas={};seen=set();before=path.stat()
    with path.open(encoding='utf-8-sig') as f:
        for line_number,line in enumerate(f,1):
            if not line.strip() or line.lstrip().startswith(('*','!','#')):continue
            v=line.split()
            if len(v)!=14:raise ValueError(f'{path}:{line_number}: area_svat requires 14 fields')
            svat=int(v[0])
            if svat<=0 or svat in seen:raise ValueError(f'{path}:{line_number}: invalid/duplicate SVAT {svat}')
            seen.add(svat)
            area,x,y=(float(v[i].replace('D','E').replace('d','e')) for i in (1,9,10))
            if not all(math.isfinite(a) for a in (area,x,y)) or area<=0:raise ValueError(f'invalid area/XY for SVAT {svat}')
            if svat not in selected:continue
            m=selected[svat]
            if abs(float(m['x'])-x)>.001 or abs(float(m['y'])-y)>.001:
                raise ValueError(f'area_svat coordinate mismatch for SVAT {svat}')
            areas[svat]=area
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('area_svat changed during read')
    missing=set(selected)-set(areas)
    if missing:raise ValueError(f'area_svat missing {len(missing)} original SVAT IDs; examples {sorted(missing)[:10]}')
    return areas


def comparison(areas,members):
    by_hru=defaultdict(lambda:[0.,0.]);different=0;max_abs=0.;max_ratio=0.
    for m in members:
        actual=areas[int(m['svat'])];old=float(m['svat_area_m2'])
        delta=abs(actual-old);different+=delta>1e-6;max_abs=max(max_abs,delta)
        if old>0:max_ratio=max(max_ratio,delta/old)
        a=by_hru[int(m['HRU'])];a[0]+=actual;a[1]+=old
    return dict(svats=len(areas),hrus=len(by_hru),different_svat_areas=different,
                different_hru_totals=sum(abs(a-b)>1e-6 for a,b in by_hru.values()),
                max_abs_difference_m2=max_abs,max_relative_difference=max_ratio,
                actual_total_m2=math.fsum(areas.values()),comparison_total_m2=math.fsum(float(m['svat_area_m2']) for m in members),
                comparison_only='Existing membership areas never replace area_svat values')


def locate_area_files(runs_root,start,end,explicit=None):
    start,end=date.fromisoformat(start),date.fromisoformat(end)
    entries=[]
    for lo,hi in PERIODS:
        if hi<start.year or lo>end.year:continue
        root=runs_root/f'run_{lo}_{hi}'/'metaswap'
        candidates=[root/'area_svat.inp',root/'inp/area_svat.inp']
        found=[p for p in candidates if p.is_file()]
        entries.append(dict(period=f'{lo}_{hi}',candidates=[str(p) for p in candidates],existing=[str(p) for p in found]))
    paths=sorted({Path(p) for entry in entries for p in entry['existing']})
    scope='PERIOD_RUN_FILES'
    rejected_fallbacks=[]
    if not paths:
        fallback=[]
        for base in (runs_root/'LWKM_run_resultaten_totaal/metaswap',runs_root/'LWKM_tools'):
            if not base.is_dir():continue
            # Bounded scan: known MetaSWAP packages, never the output raster tree.
            candidates=[base/'area_svat.inp',base/'data/area_svat.inp']
            candidates.extend(base.glob('area_svat*.inp'))
            if base.name=='LWKM_tools':
                for directory in base.iterdir():
                    if directory.is_dir() and 'metaswap' in directory.name.lower():
                        candidates.extend((directory/'data/area_svat.inp',directory/'area_svat.inp'))
                        for child in directory.iterdir():
                            if child.is_dir():candidates.extend((child/'data/area_svat.inp',child/'area_svat.inp'))
            for candidate in candidates:
                if candidate.is_file():
                    digest=sha(candidate)
                    if digest==OWNER_AREA_SHA256:fallback.append(candidate)
                    else:rejected_fallbacks.append(dict(path=str(candidate),sha256=digest,reason='not the hash-bound owner area file'))
        paths=sorted(set(fallback));scope='MATCHED_PROJECT_OWNER_AREA_FILE_PERIODS_NOT_RECHECKED'
    if explicit is not None:
        paths=[explicit];scope='EXPLICIT_AREA_SVAT_FILE_PERIODS_NOT_RECHECKED'
    return paths,dict(periods=entries,scope=scope,missing_periods=[r['period'] for r in entries if not r['existing']],unmatched_existing_fallbacks=rejected_fallbacks)


def bind_area_files(paths,members,discovery):
    if not paths:raise FileNotFoundError('No actual run area_svat.inp or hash-matched owner area file found; no area fallback permitted')
    manifest=dict(discovery,files=[],period_area_differences=[])
    reference=None;known_hashes={}
    for path in paths:
        print(f'AREA_SVAT {path}',flush=True)
        digest=sha(path)
        manifest['files'].append(dict(path=str(path),sha256=digest))
        if digest in known_hashes:continue
        current=read_area_svat(path,members);known_hashes[digest]=True
        if reference is None:reference=current
        else:
            changed=sum(current[k]!=reference[k] for k in reference)
            if changed:manifest['period_area_differences'].append(dict(path=str(path),changed_selected_svats=changed))
    manifest['comparison_with_membership']=comparison(reference,members)
    manifest['status']='SELECTED_SVAT_AREAS_DIFFER_BETWEEN_FILES' if manifest['period_area_differences'] else 'AREA_SVAT_JOIN_VERIFIED_PERIOD_STABILITY_ONLY_FOR_FOUND_FILES'
    return reference,manifest
