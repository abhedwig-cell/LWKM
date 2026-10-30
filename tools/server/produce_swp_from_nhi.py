"""Generate candidate SWP directly from confirmed NHI sources and HRU identities.

No XLS/SQLite, local Fortran control or source relocation. Physical acceptance
remains separate from successful input generation.
"""
import argparse
from collections import defaultdict
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import numpy as np
from tools.swp_hru_authority import rows,number,unique
from tools.swp_run_parameters import derive,FIELDS,allocate_irrigation
from tools.svat_areas import locate_area_files,bind_area_files
from tools.server.dqsat_source import locate as locate_dqsat, DQSAT_SHA256
from tools.server.check_swp_source_values import grid,sample,sha

ROOT=Path(__file__).resolve().parents[2]


def read_svat_values(path,ids):
    """Exact whitespace SVAT/value table, not a land-use parameter table."""
    values={}
    with path.open() as f:
        for line_number,line in enumerate(f,1):
            if not line.strip() or line.lstrip().startswith(('#','!','*')):continue
            fields=line.split()
            if len(fields)!=2:raise ValueError(f'{path}:{line_number}: expected SVAT and value')
            svat=int(fields[0]);value=float(fields[1])
            if svat in ids:
                if svat in values:raise ValueError(f'duplicate SVAT {svat} in {path}')
                if not np.isfinite(value):raise ValueError(f'nonfinite SVAT value {svat}')
                values[svat]=value
    if set(values)!=ids:raise ValueError(f'{path}: {len(ids-set(values))} selected SVATs missing')
    return values


def generate(sources,qualified_report,hru,membership,soil,crop,output,start,end,expected_hrus=10242):
    if date.fromisoformat(end)<date.fromisoformat(start):raise ValueError('reversed dates')
    output.mkdir(parents=True,exist_ok=True)
    manifest_path=output/'production_manifest.json'
    previous=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    specs=json.loads(sources.read_text())['sources']
    members=list(rows(membership))
    explicit=Path(specs['area_svat']['path']) if 'area_svat' in specs else None
    runs_root=Path(specs['head']['path']).parents[3]
    area_paths,area_discovery=locate_area_files(runs_root,start,end,explicit=explicit)
    (output/'area_source_manifest.json').write_text(json.dumps(area_discovery,indent=2)+'\n')
    input_hashes={k:sha(v) for k,v in dict(sources=sources,qualified_report=qualified_report,hru=hru,membership=membership,soil=soil,crop=crop).items()}
    input_hashes['area_files']={str(p):sha(p) for p in area_paths}
    tools_dir=Path(__file__).resolve().parents[1]
    code_paths=[Path(__file__),tools_dir/'swp_run_parameters.py',tools_dir/'dqsat_policy.py',tools_dir/'server/dqsat_source.py',tools_dir/'svat_areas.py',tools_dir/'idf_reader.py',tools_dir/'server/check_swp_source_values.py']
    code_hash=hashlib.sha256(''.join(sha(path) for path in code_paths).encode()).hexdigest()
    if previous.get('status')=='SWP_INPUTS_GENERATED_NOT_SWAP_VALIDATED' and start=='1970-01-01' and previous.get('start')==start and previous.get('end')==end and previous.get('input_hashes')==input_hashes and previous.get('producer_sha256')==code_hash and previous.get('hrus')==expected_hrus:
        unchanged=all(Path(spec['path']).is_file() and sha(Path(spec['path']))==spec['sha256'] for spec in previous['sources'].values())
        table=output/'runs_candidate.csv'
        allocation_file=output/'irrigation_allocation.json'
        unchanged=unchanged and allocation_file.is_file() and sha(allocation_file)==previous.get('irrigation_allocation_sha256')
        if unchanged and table.is_file() and sha(table)==previous.get('parameters_sha256') and (output/'dqsat_hru.csv').is_file() and sha(output/'dqsat_hru.csv')==previous.get('dqsat_table_sha256'):
            (output/'area_source_manifest.json').write_text(json.dumps(previous['area_sources'],indent=2)+'\n')
            previous['reused_parameter_phase']=True
            print('PARAMETERS REUSED',flush=True)
            return previous
    manifest=dict(status='RUNNING',start=start,end=end,production_admitted=False)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    specs=json.loads(sources.read_text())['sources']
    report=json.loads(qualified_report.read_text())
    if sha(sources)!=report['source_binding_sha256'] or sha(membership)!=report['membership_sha256']:
        raise ValueError('returned server report does not bind these sources/membership')
    hrus=unique(rows(hru),lambda r:number(r,'HRU','hru'))
    ids={number(m,'svat') for m in members}
    if len(ids)!=len(members):raise ValueError('duplicate SVAT membership')
    groups=defaultdict(list)
    for m in members:groups[number(m,'HRU')].append(m)
    if set(groups)!=set(hrus) or len(hrus)!=expected_hrus:raise ValueError('HRU population mismatch')
    xy=np.array([(float(m['x']),float(m['y'])) for m in members])
    actual_areas,area_manifest=bind_area_files(area_paths,members,area_discovery)
    (output/'area_source_manifest.json').write_text(json.dumps(area_manifest,indent=2)+'\n')
    if area_manifest['period_area_differences']:
        raise ValueError('Selected SVAT areas differ between actual area_svat files; see area_source_manifest.json')
    dqsat_path=locate_dqsat(specs,runs_root,output/'dqsat_source_manifest.json')
    provenance={};source_roles=('glk','rds','lgn','bfe','meteo','irr_switch','head')
    for role in source_roles:
        path=Path(specs[role]['path'])
        expected_hash=report['sources'][role]['sha256']
        if role=='head' and start!='1970-01-01':
            stamp=start.replace('-','')
            candidates=[path.parent/(f'head_{stamp}'+suffix) for suffix in ('_l1.idf','000000_l1.idf')]
            found=[p for p in candidates if p.is_file()]
            if len(found)!=1:raise ValueError('no unique exact start-date head')
            path=found[0];expected_hash=None
        print(f'LEES {role}: {path}',flush=True)
        before=path.stat();values,geometry=grid(path);raw,coverage=sample(values,geometry,xy)
        digest=sha(path);after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('source changed during reading')
        if expected_hash and expected_hash!=digest:raise ValueError(f'source changed since server check: {role}')
        if coverage['finite']!=len(members):raise ValueError(f'{role}: incomplete coordinate coverage {coverage}')
        scale=.01 if role=='glk' else 1.
        for m,v in zip(members,raw):
            if role in ('lgn','bfe','meteo','irr_switch'):
                if not float(v).is_integer():raise ValueError(f'noninteger {role}')
                m[role]=str(int(v))
            else:m[role]=str(float(v)*scale)
        if role=='head':
            col=np.floor((xy[:,0]-geometry['xmin'])/geometry['dx']).astype(int)+1
            row=np.floor((geometry['ymin']+geometry['nrows']*geometry['dy']-xy[:,1])/geometry['dy']).astype(int)+1
            for m,c,r in zip(members,col,row):m['col'],m['row']=str(c),str(r)
        provenance[role]=dict(path=str(path),sha256=digest,scale_to_parameter_units=scale)
    # Actual MetaSWAP area_svat values only; frozen membership is QA, never fallback.
    for m in members:
        area=actual_areas[number(m,'svat')]
        if not np.isfinite(area) or area<=0:raise ValueError('invalid area_svat value')
        m['area']=str(area)
        m['bbc']='2' # Effective Q_ext from BBC09, explicit project bottom policy.
    print(f'LEES dqsat: {dqsat_path}',flush=True)
    before=dqsat_path.stat();values,dq_geometry=grid(dqsat_path)
    _,coverage=sample(values,dq_geometry,xy)
    # sample() checks exact centres but masks NoData; retain raw source values
    # here so NoData can be distinguished from invalid NaN/Inf by shared policy.
    if coverage['outside'] or coverage['off_center']:
        raise ValueError(f'dqsat: invalid coordinate coverage {coverage}')
    col=np.floor((xy[:,0]-dq_geometry['xmin'])/dq_geometry['dx']).astype(int)
    row=np.floor((dq_geometry['ymin']+dq_geometry['nrows']*dq_geometry['dy']-xy[:,1])/dq_geometry['dy']).astype(int)
    raw=values[row,col]
    digest=sha(dqsat_path);after=dqsat_path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or digest!=DQSAT_SHA256:
        raise ValueError('dqsat source changed while reading or is not the identified raster')
    provenance['dqsat_grid']=dict(path=str(dqsat_path),sha256=digest,
        use='OWNER_20261009_POSITIVE_MEMBER_MEDIAN_SHARED_WITH_DRA',units='m',samples=coverage)
    for m,value in zip(members,raw):m['dqsat']=str(float(value))
    soils=unique(rows(soil),lambda r:number(r,'bodem370'))
    crops=unique(rows(crop),lambda r:(number(r,'soil2_id'),number(r,'lu4')))
    parameters=[];diagnostics=[];errors=[]
    config=dict(start=start,end=end,climate_id='__',MaxPondDepth=.002,crunoff_par=.25,tempCbotk=12,
                dqsat_policy='positive_member_median',dqsat_nodata=dq_geometry['nodata'])
    for count,(hid,h) in enumerate(sorted(hrus.items()),1):
        try:
            representative=next(m for m in groups[hid] if number(m,'svat')==number(h,'svat_repr','hru_representative_svat'))
            # Explicit server-source root policy: raw rootzone.asc interpreted cm.
            # Retain existing representative root if supplied; never override it.
            selected=dict(h)
            root_source='HRU_rz_repr_cm'
            if selected.get('rz_repr','')=='':
                selected['rz_repr']=representative['rds'];root_source='REPRESENTATIVE_SERVER_ROOTZONE_RAW_CM_CANDIDATE'
            run,diag=derive(selected,groups[hid],soils,crops,config)
            diag['root_source']=root_source
            diag['initial_water_below_profile']=run['GWLI'] < -2000
            diag['area_source']='ACTUAL_AREA_SVAT_INP_JOINED_ON_SVAT_ID_AND_XY'
            parameters.append(run);diagnostics.append(diag)
        except (KeyError,ValueError,StopIteration) as exc:errors.append(dict(HRU=hid,error=str(exc)))
        if count%1000==0:print(f'PARAMETERS {count}/{len(hrus)}; fouten {len(errors)}',flush=True)
    if errors:
        (output/'parameter_errors.json').write_text(json.dumps(errors,indent=2)+'\n')
        raise ValueError(f'Incomplete population: {len(errors)} HRU errors; national irrigation allocation not performed: {errors[:5]}')
    allocation=allocate_irrigation(parameters,diagnostics)
    (output/'irrigation_allocation.json').write_text(json.dumps(allocation,indent=2)+'\n')
    with (output/'runs_candidate.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(parameters)
    with (output/'dqsat_hru.csv').open('w',newline='') as f:
        records=[dict(hru=d['HRU'],representative_svat=number(hrus[d['HRU']],'svat_repr','hru_representative_svat'),
                      representative_dqsat=d['dqsat']['positive_median'],**d['dqsat']) for d in diagnostics]
        fields=['hru','representative_svat','representative_dqsat','source_representative_dqsat','representative_is_nodata',
                'positive_median','positive_mean','member_count','positive_count','zero_count','nodata_count',
                'candidate_spacing_m','dqsat_method','discriminating']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
    (output/'diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
    (output/'parameter_errors.json').write_text(json.dumps(errors,indent=2)+'\n')
    manifest.update(status='PARTIAL_PARAMETERS' if errors else 'RUN_PARAMETERS_SOURCE_CANDIDATE',hrus=len(parameters),failed_hrus=len(errors),
                    sources=provenance,root_policy='REPRESENTATIVE_SERVER_ROOTZONE_CM_CANDIDATE',
                    area_policy='ACTUAL_AREA_SVAT_INP_NOT_MEMBERSHIP_NOT_UOPP_NOT_MODFLOW_CELL_AREA',area_sources=area_manifest,bottom_policy='BBC09_EFFECTIVE_FLUX_SWBOTB2',
                    remaining=['Candidate four-class crop mapping; management assets must be assembled separately.',
                               'Rootzone raw-cm interpretation is explicit candidate policy, not recovered five-column root schema.',
                               'No claim of hydrological validation or national SWAP execution.'])
    manifest['irrigation_allocation']=allocation
    manifest['irrigation_allocation_sha256']=sha(output/'irrigation_allocation.json')
    manifest['input_hashes']=input_hashes
    manifest['dqsat_table_sha256']=sha(output/'dqsat_hru.csv')
    manifest['dqsat_policy']='OWNER_20261009_POSITIVE_MEMBER_MEDIAN_SHARED_WITH_DRA'
    manifest['parameters_sha256']=sha(output/'runs_candidate.csv')
    manifest['producer_sha256']=code_hash
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('swp_server_productie'))
    p.add_argument('--expected-hrus',type=int,default=10242)
    p.add_argument('--start',default='1970-01-01');p.add_argument('--end',default='2022-12-31')
    a=p.parse_args()
    try:
        r=generate(ROOT/'config/swp/server_locations_20261029.json',ROOT/'source_data/source_values.json',
                   ROOT/'source_data/hrus.csv',ROOT/'source_data/membership.csv.gz',
                   ROOT/'config/swp/soil_classification_and_profile.csv',ROOT/'config/swp/four_landuse_crop_candidate.csv',
                   a.output,a.start,a.end,a.expected_hrus)
        from tools.swp_direct_render import main as render_main
        produced_ids={str(int(row['run_id'])) for row in rows(a.output/'runs_candidate.csv')}
        for stale in (a.output/'swp').glob('*.swp'):
            if stale.stem.isdigit() and stale.stem not in produced_ids:stale.unlink()
        argv=['render','--parameters',str(a.output/'runs_candidate.csv'),'--catalog',str(ROOT/'config/swp/lookup_catalog.json.gz'),
              '--template',str(ROOT/'tests/fixtures/d1/wwl.swp'),'--output',str(a.output/'swp'),'--expected-hrus',str(r['hrus'])]
        if not r['hrus']:raise ValueError('no HRUs successfully prepared')
        render_failed=render_main(argv[1:])
        r['status']='PARTIAL_GENERATION' if r['failed_hrus'] or render_failed else 'SWP_INPUTS_GENERATED_NOT_SWAP_VALIDATED'
        (a.output/'production_manifest.json').write_text(json.dumps(r,indent=2)+'\n')
        with zipfile.ZipFile(a.output/'controle.zip','w',zipfile.ZIP_DEFLATED) as z:
            for name in ('production_manifest.json','parameter_errors.json','diagnostics.json','swp/manifest.json','area_source_manifest.json','dqsat_source_manifest.json','dqsat_hru.csv','irrigation_allocation.json'):z.write(a.output/name,name)
        print(json.dumps(dict(status=r['status'],hrus=r['hrus'],failed_hrus=r['failed_hrus'])))
        return bool(r['failed_hrus'] or render_failed)
    except Exception as exc:
        a.output.mkdir(parents=True,exist_ok=True)
        (a.output/'production_manifest.json').write_text(json.dumps(dict(status='FAILED',error=str(exc)),indent=2)+'\n')
        with zipfile.ZipFile(a.output/'controle.zip','w',zipfile.ZIP_DEFLATED) as z:
            for name in ('production_manifest.json','area_source_manifest.json','dqsat_source_manifest.json'):
                if (a.output/name).is_file():z.write(a.output/name,name)
        print(f'SWP STOP: {exc}',file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
