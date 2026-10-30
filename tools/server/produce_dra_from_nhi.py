"""Restartable DRA from existing NHI sources, NumPy and stdlib only."""
import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import date
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile
import numpy as np
from tools.swp_hru_authority import rows, number, unique
from tools.server.check_swp_source_values import grid, sample, sha
from tools.server.dqsat_source import locate as locate_dqsat, DQSAT_SHA256
from tools.dqsat_policy import summarize
from tools.generate_dra import aggregate_physical_arrays, render_dra_explicit
from tools.dra_level_compression import from_aggregate, to_render_level
from tools.dra_owner_policy import apply_owner_policy, POLICY_ID
from tools.w07_autofive_full_records import solve
from tools.run_dra_protected_population import atomic_json, canonical

ROOT=Path(__file__).resolve().parents[2]
RUNS=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
SYSTEMS=(('H1','infiltration_capable_open','open_channel'),
         ('P','infiltration_capable_open','open_channel'),
         ('S','infiltration_capable_open','open_channel'),
         ('T','infiltration_capable_open','open_channel'),
         ('MVG','drain_only_open','open_channel'),('PIPE','pipe','drain_tube'),
         ('OLF','drain_only_open','open_channel'))


def months(start,end):
    first,last=date.fromisoformat(start),date.fromisoformat(end)
    if last<first:raise ValueError('end before start')
    current=first.replace(day=1)
    # One endpoint beyond the last simulated day, for SWAP interpolation.
    stop=date(last.year+1,1,1) if last.month==12 else date(last.year,last.month+1,1)
    result=[]
    while current<=stop:
        result.append(current.isoformat())
        current=date(current.year+1,1,1) if current.month==12 else date(current.year,current.month+1,1)
    return result


def read_samples(spec,xy):
    path=Path(spec['path']);before=path.stat()
    values,g=grid(path);raw,coverage=sample(values,g,xy)
    digest=sha(path);after=path.stat()
    if digest!=spec['sha256'] or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError(f'source identity changed: {path}')
    if coverage['outside'] or coverage['off_center']:
        raise ValueError(f'coordinate mismatch: {path}: {coverage}')
    return raw,g


def prepare_static(specs,xy):
    required={'glk'}
    for name,_,_ in SYSTEMS:
        required.update((name+'_cdr',name+'_bottom') if name not in ('P','S','T') else
                        (name+'_cdr',name+'_sum',name+'_win'))
    required.update(name+'_inf' for name in ('H1','P','S','T'))
    required.update(name+'_bottom_'+season for name in ('P','S') for season in ('sum','win'))
    if set(specs)!=required:raise ValueError(f'incomplete drainage source registry: missing={sorted(required-set(specs))}, extra={sorted(set(specs)-required)}')
    data={};events=[]
    for role,spec in specs.items():
        print(f'LEES {role}: {spec["path"]}',flush=True)
        data[role],_=read_samples(spec,xy)
    data['glk']/=100.
    if not np.isfinite(data['glk']).all():raise ValueError('missing member ground level')
    for name in ('P','S','T'):
        if name=='T':
            data['T_bottom_sum']=data['T_sum'].copy();data['T_bottom_win']=data['T_win'].copy()
        active=np.nan_to_num(data[name+'_cdr'],nan=0)>0
        for season in ('sum','win'):
            missing=active & np.isnan(data[name+'_'+season])
            recover=missing & np.isfinite(data[name+'_bottom_'+season])
            data[name+'_'+season][recover]=data[name+'_bottom_'+season][recover]
            for index in np.flatnonzero(recover):
                events.append(dict(member_index=int(index),system=name,action='STAGE_FROM_CORRESPONDING_BOTTOM',season=season))
        complete=np.ones(len(xy),dtype=bool)
        for suffix in ('sum','win','bottom_sum','bottom_win'):
            complete &= np.isfinite(data[name+'_'+suffix])
        excluded=active & ~complete
        for index in np.flatnonzero(excluded):
            events.append(dict(member_index=int(index),system=name,action='EXCLUDE_INCOMPLETE_RIV_RECORD',
                               conductance_m2_d=float(data[name+'_cdr'][index])))
        data[name+'_cdr'][excluded]=0.
        data[name+'_bottom']=(data[name+'_bottom_sum']+data[name+'_bottom_win'])/2.
    for name in ('H1','P','S','T'):
        missing=(data[name+'_cdr']>0)&np.isnan(data[name+'_inf'])
        for index in np.flatnonzero(missing):
            events.append(dict(member_index=int(index),system=name,action='MISSING_FACTOR_NO_CELL_INFILTRATION'))
        data[name+'_inf'][missing]=0.
    for name in ('MVG','PIPE','OLF'):
        data[name+'_sum']=data[name+'_bottom'];data[name+'_win']=data[name+'_bottom']
    return data,events


def physical_systems(data,indices,dqsat,dates,h1_depths):
    physical=[]
    for name,cls,medium in SYSTEMS:
        get=lambda suffix:data[name+'_'+suffix][indices]
        agg=aggregate_physical_arrays(data['glk'][indices],get('cdr'),get('bottom'),
            summer=get('sum') if name!='H1' else None,winter=get('win') if name!='H1' else None,
            dqsat=dqsat,infiltration=get('inf') if name in ('H1','P','S','T') else None,
            missing_infiltration_factor_is_zero=True)
        series=None
        if name=='H1' and agg['cdr_sum']>0:
            if not np.isfinite(h1_depths).all():raise ValueError('missing H1 stage in active member')
            series=tuple((day,min(float(v),agg['dep'])) for day,v in zip(dates,h1_depths))
        physical.append(from_aggregate(source_id=name,hydraulic_class=cls,medium=medium,aggregate=agg,level_series=series))
    return physical


def soil_horizons(catalog):
    with gzip.open(catalog,'rt') as f:tables=json.load(f)['tables']
    result=defaultdict(set)
    for row in tables['eigenschappen']:result[int(row['bodem_id'])].add(int(row['ISOILLAY']))
    return {key:len(value) for key,value in result.items()}


def write_gzip(path,record):
    temp=path.with_suffix('.tmp')
    with temp.open('wb') as stream:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as zipped:
            zipped.write((canonical(record)+'\n').encode())
    temp.replace(path)


def generate(binding,hru,membership,catalog,output,start,end,expected_hrus=10242,runs=RUNS):
    begin=time.monotonic();output.mkdir(parents=True,exist_ok=True)
    atomic_json(output/'production_manifest.json',dict(status='RUNNING',production_admitted=False))
    source=json.loads(binding.read_text());dates=months(start,end)
    missing=[day for day in dates if day not in source['stages']]
    if missing:raise ValueError('missing H1 source months: '+','.join(missing))
    members=list(rows(membership));hrus=unique(rows(hru),lambda r:number(r,'HRU'))
    if len(hrus)!=expected_hrus:raise ValueError('HRU count mismatch')
    if len({number(m,'svat') for m in members})!=len(members):raise ValueError('duplicate SVAT membership')
    grouped=defaultdict(list)
    for index,member in enumerate(members):grouped[number(member,'HRU')].append(index)
    if set(grouped)!=set(hrus):raise ValueError('HRU membership domain mismatch')
    xy=np.array([(float(m['x']),float(m['y'])) for m in members])
    specs={'glk':source['sources']['glk']}
    if 'dqsat_grid' in source:specs['dqsat_grid']=source['dqsat_grid']
    dq_path=locate_dqsat(specs,runs,output/'dqsat_source_manifest.json')
    values,g=grid(dq_path);_,coverage=sample(values,g,xy)
    if coverage['outside'] or coverage['off_center']:raise ValueError('dqsat geometry mismatch')
    cols=np.floor((xy[:,0]-g['xmin'])/g['dx']).astype(int)
    row=np.floor((g['ymin']+g['nrows']*g['dy']-xy[:,1])/g['dy']).astype(int)
    dq=values[row,cols]
    if sha(dq_path)!=DQSAT_SHA256:raise ValueError('dqsat source changed')
    used={**source['sources'],**{'H1_'+day:source['stages'][day] for day in dates}}
    # Rehash existing sources to detect changed bytes even on a resumed run.
    for count,(role,spec) in enumerate(used.items(),1):
        if sha(Path(spec['path']))!=spec['sha256']:raise ValueError('changed source: '+spec['path'])
        if count%12==0:print(f'BRONCONTROLE {count}/{len(used)}',flush=True)
    code={p.name:sha(p) for p in (Path(__file__),*(ROOT/'tools'/n for n in
        ('generate_dra.py','dqsat_policy.py','dra_level_compression.py','dra_owner_policy.py',
         'dra_protected_compression.py','w07_autofive_full_records.py','idf_reader.py',
         'p12_swallo.py','run_dra_protected_population.py','swp_hru_authority.py',
         'server/check_swp_source_values.py','server/dqsat_source.py')))}
    identity=dict(start=start,end=end,inputs={str(p):sha(p) for p in (binding,hru,membership,catalog)},
                  dqsat_sha256=sha(dq_path),code=code,policy=POLICY_ID,
                  area_policy='ALL_MEMBER_MODFLOW_CELL_62500_M2_NOT_AREA_SVAT',
                  h1_policy='ACTUAL_MONTHLY_SOURCE_SERIES_NO_REPEATING_C2_YEAR')
    fingerprint=hashlib.sha256(canonical(identity).encode()).hexdigest()
    atomic_json(output/'source_manifest.json',dict(identity=identity,fingerprint=fingerprint,sources=used))
    cache=output/'cache'/fingerprint;cache.mkdir(parents=True,exist_ok=True)
    static=cache/'static.npz';decisions=cache/'cell_decisions.json'
    static_hash=cache/'static_hashes.json'
    if static.is_file() and decisions.is_file() and static_hash.is_file():
        hashes=json.loads(static_hash.read_text())
        if any(sha(cache/name)!=digest for name,digest in hashes.items()):raise ValueError('prepared static cache changed')
        with np.load(static,allow_pickle=False) as archive:data={key:archive[key] for key in archive.files}
        events=json.loads(decisions.read_text())
    else:
        data,events=prepare_static(source['sources'],xy)
        for event in events:
            m=members[event['member_index']]
            event.update(svat=number(m,'svat'),hru=number(m,'HRU'),x=float(m['x']),y=float(m['y']))
        temp=static.with_suffix('.tmp.npz');np.savez_compressed(temp,**data);temp.replace(static)
        atomic_json(decisions,events)
        atomic_json(static_hash,{p.name:sha(p) for p in (static,decisions)})
    atomic_json(output/'cell_decisions.json',events)
    hids=sorted(hrus);position={hid:i for i,hid in enumerate(hids)}
    group_codes=np.array([position[number(m,'HRU')] for m in members])
    cdr=np.nan_to_num(data['H1_cdr'],nan=0.);active=cdr>0
    denominator=np.bincount(group_codes,weights=cdr,minlength=len(hids))
    stages=np.full((len(hids),len(dates)),np.nan)
    reused_months=0
    for j,day in enumerate(dates):
        checkpoint=cache/(day+'.json')
        if checkpoint.exists():
            rec=json.loads(checkpoint.read_text());reused_months+=1
            digest=rec.pop('content_sha256')
            if hashlib.sha256(canonical(rec).encode()).hexdigest()!=digest:
                raise ValueError('H1 month cache changed: '+day)
        else:
            raw,_=read_samples(source['stages'][day],xy)
            invalid=active & ~np.isfinite(raw)
            numerator=np.bincount(group_codes,weights=np.where(active & ~invalid,cdr*(data['glk']-raw),0.),minlength=len(hids))
            depth=np.maximum(0.,np.divide(numerator,denominator,out=np.zeros_like(numerator),where=denominator>0))
            bad=np.unique(group_codes[invalid])
            rec=dict(fingerprint=fingerprint,day=day,depths=depth.tolist(),invalid_hru_positions=bad.tolist())
            rec['content_sha256']=hashlib.sha256(canonical(rec).encode()).hexdigest()
            atomic_json(checkpoint,rec)
        if rec['fingerprint']!=fingerprint or rec['day']!=day:raise ValueError('stale H1 month cache')
        stages[:,j]=rec['depths'];stages[rec['invalid_hru_positions'],j]=np.nan
        if j%12==0:print(f'H1 {j+1}/{len(dates)} {day}',flush=True)
    horizons=soil_horizons(catalog)
    checkpoints=output/'hrus';checkpoints.mkdir(exist_ok=True)
    targets=output/'dra';targets.mkdir(exist_ok=True)
    outcomes=[];reused=0
    for count,hid in enumerate(hids,1):
        path=checkpoints/f'{hid}.json.gz';target=targets/f'{hid}.dra'
        existing=None
        if path.exists():
            with gzip.open(path,'rt') as stream:existing=json.load(stream)
        if existing and existing.get('fingerprint')==fingerprint and existing.get('sha256') and target.is_file() and sha(target)==existing['sha256']:
            rec=existing;reused+=1
        else:
            rec=dict(hru=hid,fingerprint=fingerprint,production_admitted=False)
            try:
                indices=np.array(grouped[hid]);representative=number(hrus[hid],'svat_repr')
                selected=[index for index in indices if number(members[index],'svat')==representative]
                if len(selected)!=1:raise ValueError('representative SVAT not in its own HRU')
                summary=summarize(dq[indices],dq[selected[0]],g['nodata']);rec['dqsat']=summary
                physical=physical_systems(data,indices,summary['positive_median'],dates,stages[position[hid]])
                rec['physical']=[asdict(s) for s in physical]
                retained,decision=apply_owner_policy(physical)
                rec.update(retained_physical=[asdict(s) for s in retained],owner_decision=decision)
                if not retained:raise ValueError('NO_ACTIVE_DRAINAGE: SWP requires explicit SWDRA=0; no fictitious level written')
                levels,audit=solve(retained);rec['audit']=audit
                rendered=[to_render_level(s) for s in levels];rec['levels']=rendered
                text=render_dra_explicit(rendered,horizons[number(hrus[hid],'bodem370')],date.fromisoformat(start).year,date.fromisoformat(end).year+1,0.)
                blob=text.encode();digest=hashlib.sha256(blob).hexdigest()
                if not target.is_file() or sha(target)!=digest:
                    temp=target.with_suffix('.tmp');temp.write_bytes(blob);temp.replace(target)
                rec.update(status=audit['method'],sha256=digest,soil_horizons=horizons[number(hrus[hid],'bodem370')])
            except (ValueError,KeyError,AssertionError) as error:
                rec.update(status='SOURCE_OR_INTERFACE_ERROR',error=str(error));target.unlink(missing_ok=True)
            write_gzip(path,rec)
        outcomes.append({key:rec.get(key) for key in ('hru','status','sha256','soil_horizons','error')})
        if count%100==0:print(f'DRA {count}/{len(hids)}',flush=True)
    failed=sum(r['status']=='SOURCE_OR_INTERFACE_ERROR' for r in outcomes)
    report=dict(status='DRA_SOURCE_CANDIDATES_NOT_SWAP_VALIDATED' if not failed else 'PARTIAL_DRA_GENERATION',
        hrus=len(hids),generated=len(hids)-failed,failed=failed,
        approximated=sum(r['status']=='AUTO_APPROXIMATED_FIVE_LEVEL' for r in outcomes),
        reused_hrus=reused,reused_h1_months=reused_months,h1_months=len(dates),start=start,end=end,
        production_admitted=False,fingerprint=fingerprint,elapsed_seconds=time.monotonic()-begin,
        limitations=['No new SWAP execution or hydrological validation.',
                     'Best-fit error diagnostics use prescribed groundwater-depth scenarios, not simulated groundwater.',
                     'Existing C2 historical-period files are not overwritten.'],outcomes=outcomes)
    atomic_json(output/'production_manifest.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('dra_server_productie'))
    p.add_argument('--start',default='1970-01-01');p.add_argument('--end',default='2022-12-31')
    p.add_argument('--expected-hrus',type=int,default=10242)
    a=p.parse_args()
    try:
        r=generate(ROOT/'config/dra/server_sources_20261030.json',ROOT/'source_data/hrus.csv',
                   ROOT/'source_data/membership.csv.gz',ROOT/'config/swp/lookup_catalog.json.gz',
                   a.output,a.start,a.end,a.expected_hrus)
        result=bool(r['failed'])
        print(json.dumps({k:v for k,v in r.items() if k!='outcomes'}))
    except Exception as error:
        a.output.mkdir(parents=True,exist_ok=True)
        atomic_json(a.output/'production_manifest.json',dict(status='FAILED',error=str(error),production_admitted=False))
        print(f'DRA STOP: {error}',file=sys.stderr);result=True
    with zipfile.ZipFile(a.output/'controle.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in ('production_manifest.json','source_manifest.json','dqsat_source_manifest.json','cell_decisions.json'):
            if (a.output/name).exists():archive.write(a.output/name,name)
        for path in sorted((a.output/'hrus').glob('*.json.gz')):
            with gzip.open(path,'rt') as stream:rec=json.load(stream)
            if rec.get('status') in ('AUTO_APPROXIMATED_FIVE_LEVEL','SOURCE_OR_INTERFACE_ERROR'):
                archive.write(path,'hrus/'+path.name)
    return result


if __name__=='__main__':raise SystemExit(main())
