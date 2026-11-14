"""Receive an HRU21 export and diagnose real reference responses, never calibrate.

Signs are an explicit diagnostic hypothesis, not a SEMANTICS_REVIEWED gate.
Source rasters and original full-population decade CSVs are not rehashed here.
"""
import argparse
import csv
import gzip
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile
import numpy as np
import pandas as pd
from tools.execute_swap_candidate import digest
from tools.et_calibration import RAW, decade, write_json
from tools.receive_et_reference import calendar_ends, marker_output, receive, verify

SIGNS = {n:(1 if n in ('PSSW','PSGW') else -1) for n in RAW}
DERIVED = ['E_SOIL_POND','E_INTERCEPTION_SPRINKLING','T_ACTUAL','ET_ACTUAL','IRR_TOTAL','BDGETACT_MINUS_ET']
COLUMNS = ['hru_id','days','complete']+RAW+DERIVED+['coverage_'+n for n in RAW]


def require(condition, message):
    if not condition: raise ValueError(message)


def unpack(archive, destination):
    """Normalize Windows ZIP separators, reject aliases/traversal and symlinks."""
    destination=Path(destination)
    if destination.exists(): raise FileExistsError(destination)
    destination.mkdir(parents=True)
    seen=set();roots=set()
    with zipfile.ZipFile(archive) as z:
        require(sum(i.file_size for i in z.infolist())<200_000_000,'export exceeds 200 MB limit')
        for item in z.infolist():
            name=item.filename.replace('\\','/');parts=PurePosixPath(name)
            require(not parts.is_absolute() and '..' not in parts.parts and
                    not any(':' in s for s in parts.parts),'unsafe archive path')
            require(parts.parts and parts.as_posix() not in seen,'duplicate archive path')
            require((item.external_attr>>16)&0o170000!=0o120000,'archive symlink')
            seen.add(parts.as_posix());roots.add(parts.parts[0]);p=destination/parts
            if name.endswith('/'):p.mkdir(parents=True,exist_ok=True)
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(item))
    require(len(roots)==1,'expected one export root')
    return destination/roots.pop()


def keyvalues(path):
    result={}
    for line in Path(path).read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1);require(k not in result,'duplicate identity key');result[k]=v
    return result


def check_export(root, pilot_file, first='19700110', last='20241231'):
    """Verify every asset and the two serializations against frozen pilot IDs."""
    root=Path(root);expected={}
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        h,n=line.split('  ',1);p=PurePosixPath(n)
        require(re.fullmatch('[a-f0-9]{64}',h) and not p.is_absolute() and '..' not in p.parts and
                '\\' not in n and ':' not in n and n not in expected,'invalid manifest entry')
        expected[n]=h
        require(digest(root/n)==h,'asset hash mismatch: '+n)
    assets={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(assets==set(expected)|{'SHA256SUMS.txt','COMPLETE.txt'},'manifest is not closed')
    require(keyvalues(root/'COMPLETE.txt')=={'sha256_manifest':digest(root/'SHA256SUMS.txt')},'completion hash mismatch')
    require((root/'pilot-hrus.csv').read_text()==Path(pilot_file).read_text(),'pilot selection differs from frozen authority')
    pilot=pd.read_csv(pilot_file);ids=sorted(pilot.hru_id.astype(int));require(len(ids)==21 and len(set(ids))==21,'invalid pilot')
    start=pd.to_datetime(first,format='%Y%m%d').replace(day=1 if first[-2:]=='10' else 11 if first[-2:]=='20' else 21)
    end=pd.to_datetime(last,format='%Y%m%d');dates=calendar_ends(str(start.date()),str(end.date()))
    require(dates[0]==first and dates[-1]==last,'invalid expected calendar')
    status=keyvalues(root/'export_status.txt')
    require(status['first']==first and status['last']==last and int(status['decades'])==len(dates) and
            int(status['selected_hrus'])==21 and status['production_admitted']=='false','export scope mismatch')
    sf=pd.read_csv(root/'reference/hru_support.csv');full=pd.read_csv(root/'source_hru_support.csv')
    for f in (sf,full):
        require(not f.hru_id.duplicated().any() and (f.svats>0).all() and np.isfinite(f.area_m2).all() and (f.area_m2>0).all(),'invalid support')
    require(set(sf.hru_id)==set(ids) and len(full)==int(status['source_hrus']),'support population mismatch')
    require(sf.sort_values('hru_id').reset_index(drop=True).equals(full.loc[full.hru_id.isin(ids)].sort_values('hru_id').reset_index(drop=True)),'selected support differs')
    lineage=pd.read_csv(root/'source_manifest.csv',dtype=str)
    require(lineage.decade_end.tolist()==dates,'source lineage calendar mismatch')
    identity=(root/'source_run_identity.txt').read_text();identity_keys=keyvalues(root/'source_run_identity.txt')
    require(identity.startswith('LWKM-MSW-HRU-1.0.0\n'),'unsupported producer')
    require(identity_keys['units']=='m3/m2_per_decade;factor=1000;sign=source;missing=blank_strict_support','unsupported units contract')
    blocks=[]
    with (root/'HRU21_reference.csv').open(newline='') as combined:
        allrows=csv.DictReader(combined);require(allrows.fieldnames==['decade_end']+COLUMNS,'combined schema mismatch')
        for item in lineage.to_dict('records'):
            d=item['decade_end'];marker=root/'source_markers'/(d+'.sha256');qc=root/'source_markers'/(d+'_qc.csv');selected=root/'reference'/(d+'.csv')
            require(digest(marker)==item['source_marker_sha256'] and digest(qc)==item['source_qc_sha256'],'lineage hash mismatch')
            mk=keyvalues(marker);require(marker.read_text().startswith(identity) and mk['date']==d,'mixed producer identity')
            require(mk['output']==item['source_csv_sha256'] and mk['qc']==digest(qc),'original marker binding mismatch')
            require(marker_output(root/'reference'/(d+'.sha256'))==digest(selected)==item['selected_csv_sha256'],'selection hash mismatch')
            require(keyvalues(root/'reference'/(d+'.sha256'))['parent_output']==mk['output'],'selection parent mismatch')
            raster=list(csv.reader(io.StringIO(marker.read_text())));raster=[r for r in raster if len(r)==4 and r[0] in RAW]
            require(len(raster)==9 and {r[0] for r in raster}==set(RAW) and all(re.fullmatch('[a-f0-9]{64}',r[3]) for r in raster),'raster provenance incomplete')
            with selected.open(newline='') as f:
                rows=csv.DictReader(f);require(rows.fieldnames==COLUMNS,'native schema mismatch');rows=list(rows)
            require(len(rows)==21,'selected row count differs')
            for row in rows:
                require(next(allrows,None)=={'decade_end':d,**row},'combined/per-decade values differ')
            blocks.append(pd.DataFrame(rows).assign(decade_end=d))
        require(next(allrows,None) is None,'extra combined rows')
    frame=pd.concat(blocks,ignore_index=True)
    return frame,pilot,{'archive_manifest_assets':len(expected),'decades':len(dates),'rows':len(frame),
        'start':str(start.date()),'end':str(end.date()),'source_hrus':len(full),'selected_hrus':len(ids),
        'export_pilot_sha256':digest(root/'pilot-hrus.csv'),'frozen_pilot_sha256':digest(pilot_file),
        'pilot_csv_fields_identical_after_newline_normalization':True,
        'source_area_m2':float(full.area_m2.sum()),'selected_area_m2':float(sf.area_m2.sum()),
        'selected_area_fraction':float(sf.area_m2.sum()/full.area_m2.sum()),'producer_identity':identity_keys,
        'source_full_csv_rehashed_locally':False,'source_rasters_rehashed_locally':False}


def membership_audit(root, repo, native_inputs, output):
    """Bind recovered exact producer input bytes to Work B member labels."""
    root,repo,native_inputs,output=map(Path,(root,repo,native_inputs,output))
    identity=keyvalues(root/'source_run_identity.txt');area=native_inputs/'area_svat.inp';mapping=native_inputs/'svat_hru.csv'
    require(digest(area)==identity['area'] and digest(mapping)==identity['mapping'],'producer inputs differ')
    interface=repo/'docs/evidence/2026-10-19-work-b/interfaces'
    m=pd.read_csv(mapping,usecols=['svat_orig','HRU']).rename(columns={'svat_orig':'svat'})
    frozen=pd.read_csv(interface/'HRU_MEMBERSHIP.csv.gz',usecols=['svat','HRU'])
    require(not m.svat.duplicated().any() and m.sort_values('svat').reset_index(drop=True).equals(frozen.sort_values('svat').reset_index(drop=True)),'native mapping differs from Work B')
    areas={}
    for line in area.open():
        words=line.split()
        if words and not words[0].startswith(('!','*')):
            i=int(words[0]);require(i not in areas,'duplicate area SVAT');areas[i]=float(words[1])
    sv=pd.read_csv(interface/'SVAT_QUALIFIED.csv.gz',usecols=['svat','isberegen(0/1)','landgebruik22'])
    m=m.merge(sv,on='svat',how='left',validate='one_to_one');m['area']=m.svat.map(areas)
    require(m[['area','isberegen(0/1)']].notna().all().all() and (m.area>0).all(),'missing member support/irrigation label')
    require(set(m['isberegen(0/1)'])<={0,1},'invalid member irrigation label')
    m['irrigated_area']=m.area*m['isberegen(0/1)']
    a=m.groupby('HRU').agg(svats=('svat','size'),area_m2=('area','sum'),irrigated_member_area_m2=('irrigated_area','sum'))
    full=pd.read_csv(root/'source_hru_support.csv').set_index('hru_id').sort_index()
    require(set(a.index)==set(full.index) and np.array_equal(a.svats,full.svats) and np.allclose(a.area_m2,full.area_m2,rtol=0,atol=1e-6),'native support reconstruction differs')
    a['irrigated_member_area_fraction']=a.irrigated_member_area_m2/a.area_m2
    pilot=pd.read_csv(root/'pilot-hrus.csv');a=a.loc[pilot.hru_id].reset_index().rename(columns={'HRU':'hru_id'})
    a=a.merge(pilot[['hru_id','profile']],on='hru_id',validate='one_to_one');a.to_csv(output/'member-irrigation-support.csv',index=False)
    record={'native_members':len(m),'native_hrus':len(full),'membership_identical_to_work_b':True,
            'all_native_support_counts_and_areas_reproduced':True,'area_source_sha256':digest(area),
            'mapping_source_sha256':digest(mapping),'work_b_membership_sha256':digest(interface/'HRU_MEMBERSHIP.csv.gz'),
            'work_b_labels_sha256':digest(interface/'SVAT_QUALIFIED.csv.gz'),
            'qualification_scope':'existing member labels and native weights; static irrigation flag does not verify dynamic gift schedules',
            'production_admitted':False}
    write_json(output/'membership-audit.json',record);return a


def analyze(frame,pilot,support,output):
    """Summaries are conditional on declared signs, without opening semantic gates."""
    output=Path(output);f=frame.copy()
    for n in COLUMNS:f[n]=pd.to_numeric(f[n],errors='raise')
    require(np.isfinite(f[COLUMNS]).all().all() and (f.complete==1).all(),'incomplete/nonfinite reference cannot be diagnosed as complete')
    v=f[RAW];checks=pd.DataFrame({'E_SOIL_POND':v.MSW_EBS+v.MSW_EPD,'E_INTERCEPTION_SPRINKLING':v.MSW_EIC+v.MSW_ESP,
        'T_ACTUAL':v.MSW_TACT,'ET_ACTUAL':v.MSW_EBS+v.MSW_EPD+v.MSW_EIC+v.MSW_ESP+v.MSW_TACT,
        'IRR_TOTAL':v.PSSW+v.PSGW,'BDGETACT_MINUS_ET':v.BDGETACT-(v.MSW_EBS+v.MSW_EPD+v.MSW_EIC+v.MSW_ESP+v.MSW_TACT)})
    arithmetic=float((f[DERIVED]-checks).abs().max().max());require(arithmetic<1e-5,'native derived arithmetic differs')
    for n,sign in SIGNS.items():f['D_'+n]=sign*f[n]
    amounts=['D_'+n for n in RAW]
    require((f[amounts[:-1]]>=-1e-6).all().all(),'diagnostic signs leave negative losses/gifts')
    f['ET']=f.D_MSW_EBS+f.D_MSW_EIC+f.D_MSW_EPD+f.D_MSW_ESP+f.D_MSW_TACT
    f['E_SOIL']=f.D_MSW_EBS+f.D_MSW_EPD;f['E_IC']=f.D_MSW_EIC+f.D_MSW_ESP
    f['T']=f.D_MSW_TACT;f['TPOT']=f.D_MSW_TPOT;f['IRRIG']=f.D_PSSW+f.D_PSGW
    f['T_REDUCTION']=f.TPOT-f['T'];f['BDGETACT_RESIDUAL']=f.D_BDGETACT-f.ET
    f['end']=pd.to_datetime(f.decade_end,format='%Y%m%d');f['year']=f.end.dt.year;f['month']=f.end.dt.month
    f=f.merge(pilot[['hru_id','profile','bofek79','ghg_screening_bin']],on='hru_id',validate='many_to_one')
    f=f.merge(support[['hru_id','area_m2']],on='hru_id',validate='many_to_one')
    sums=amounts+['ET','T','E_SOIL','E_IC','TPOT','IRRIG','T_REDUCTION','BDGETACT_RESIDUAL']
    keys=['hru_id','profile','bofek79','ghg_screening_bin','year']
    annual=f.groupby(keys,sort=True)[sums].sum();annual['decades']=f.groupby(keys).size()
    annual['days']=f.groupby(keys).days.sum();annual=annual.reset_index()
    annual['full_calendar_year']=(annual.decades==36)&(annual.days==pd.to_datetime(annual.year.astype(str)+'-12-31').dt.dayofyear)
    annual['reduction_fraction']=annual.T_REDUCTION/annual.TPOT.where(annual.TPOT>1e-6)
    annual.to_csv(output/'annual-hru.csv',index=False)
    f['season']=np.select([f.month.isin([12,1,2]),f.month.isin([3,4,5]),f.month.isin([6,7,8])],['DJF','MAM','JJA'],default='SON')
    seasonal=f.groupby(keys+['season'])[sums].sum().reset_index();seasonal.to_csv(output/'seasonal-hru.csv',index=False)
    # Three HRUs per profile are a designed sample, never a national average.
    profile=annual.groupby('profile')[sums].mean().reset_index();profile.to_csv(output/'profile-mean-hru-year.csv',index=False)
    # Endpoint discontinuity screen; a flag is not a cause attribution.
    last_year=int(annual.year.max());prior=annual.loc[annual.year.between(last_year-10,last_year-1)]
    endpoint=annual.loc[annual.year==last_year,['hru_id','profile','year','ET','TPOT','T']].copy()
    if not prior.empty and prior.full_calendar_year.all() and prior.groupby('hru_id').year.nunique().eq(10).all():
        baseline=prior.groupby('hru_id')[['ET','TPOT','T']].mean().add_suffix('_previous_10_years')
        endpoint=endpoint.merge(baseline,on='hru_id',validate='one_to_one')
        endpoint['ET_ratio']=endpoint.ET/endpoint.ET_previous_10_years
        endpoint['TPOT_ratio']=endpoint.TPOT/endpoint.TPOT_previous_10_years
        endpoint['ET_below_60pct_previous_decade']=endpoint.ET_ratio<.6
    else:
        endpoint['ET_below_60pct_previous_decade']=False
    endpoint.to_csv(output/'endpoint-year-diagnostics.csv',index=False)
    quality=[]
    for name in RAW:
        q=f[name];quality.append(dict(variable=name,source_sign_hypothesis=SIGNS[name],raw_min=float(q.min()),raw_max=float(q.max()),negative_above_1e_6=int((q<-1e-6).sum()),positive_above_1e_6=int((q>1e-6).sum())))
    pd.DataFrame(quality).to_csv(output/'raw-sign-diagnostics.csv',index=False)
    management=annual.groupby(['hru_id','profile']).agg(mean_irrigation_mm_y=('IRRIG','mean'),max_irrigation_mm_y=('IRRIG','max'),years_over_1mm=('IRRIG',lambda x:int((x>1).sum())),PSGW_mm_y=('D_PSGW','mean'),PSSW_mm_y=('D_PSSW','mean')).reset_index()
    management['zero_gift_profile']=management.profile.str.endswith('_rainfed');management['zero_gift_model_guard_triggered']=management.zero_gift_profile&(management.years_over_1mm>0)
    management.to_csv(output/'management-diagnostics.csv',index=False)
    # April-September response ranking within unwatered nature sample only.
    # This is not meteorological drought classification or assignment of fit years.
    nature=f.loc[(f.profile=='nature_rainfed')&f.month.between(4,9)&f.year.between(1971,2021)].copy()
    for name in ['T_REDUCTION','TPOT','ET']:nature['w_'+name]=nature[name]*nature.area_m2
    screening=nature.groupby('year')[[f'w_{n}' for n in ['T_REDUCTION','TPOT','ET']]].sum()
    screening['nature_sample_reduction_fraction']=screening.w_T_REDUCTION/screening.w_TPOT
    screening=screening.reset_index();screening['response_rank_high_first']=screening.nature_sample_reduction_fraction.rank(method='min',ascending=False).astype(int)
    screening['weather_class']='UNCLASSIFIED';screening['fit_role']='UNASSIGNED';screening.to_csv(output/'reference-response-year-screening.csv',index=False)
    require((f.loc[f.profile=='nature_rainfed','IRRIG']<=1e-6).all(),'nature reference contains irrigation: review required')
    maxex=float((-f.T_REDUCTION).max())
    result={'status':'REAL_REFERENCE_DIAGNOSTICS_CONDITIONAL_ON_SIGN_HYPOTHESIS','semantic_review_status':'PENDING_SOURCE_FAMILY_PERIOD_AND_SIGN_REVIEW',
        'source_sign_hypothesis':SIGNS,'raw_values_unchanged':True,'native_derived_max_abs_arithmetic_error_mm':arithmetic,
        'max_abs_bdgetact_residual_mm_decade':float(f.BDGETACT_RESIDUAL.abs().max()),'bdgetact_residual_over_1e_4_rows':int((f.BDGETACT_RESIDUAL.abs()>1e-4).sum()),
        'max_abs_annual_bdgetact_residual_mm':float(annual.BDGETACT_RESIDUAL.abs().max()),
        'tact_over_tpot_rows_1e_6mm':int((f.T_REDUCTION<-1e-6).sum()),'tact_over_tpot_rows_1e_5mm':int((f.T_REDUCTION<-1e-5).sum()),
        'max_tact_over_tpot_mm_decade':maxex,'negative_reduction_not_clipped':True,'stress_fraction_only_where_tpot_gt_1e_6':True,
        'annual_et_min_mm':float(annual.ET.min()),'annual_et_max_mm':float(annual.ET.max()),'full_hru_years':int(annual.full_calendar_year.sum()),
        'nature_irrigation_rows':int((f.loc[f.profile=='nature_rainfed','IRRIG']>1e-6).sum()),
        'rainfed_agricultural_hrus_with_irrigation_guard':management.loc[management.zero_gift_model_guard_triggered,'hru_id'].astype(int).tolist(),
        'reference_response_highest_nature_deficit_years':screening.nsmallest(5,'response_rank_high_first')[['year','nature_sample_reduction_fraction']].to_dict('records'),
        'endpoint_year_screen':last_year,'endpoint_year_et_below_60pct_previous_10_years_hrus':endpoint.loc[endpoint.ET_below_60pct_previous_decade,'hru_id'].astype(int).tolist(),
        'endpoint_flag_is_diagnostic_not_cause_attribution':True,
        'no_weather_years_classified':True,'no_training_or_validation_years_assigned':True,
        'factual_calibrations':0,'production_admitted':False}
    write_json(output/'reference-diagnostics.json',result)
    return annual,management,result


def run(archive,output,repo,native_inputs=None,library_file_id=None):
    archive,output,repo=map(Path,(archive,output,repo))
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    frozen=repo/'docs/evidence/2026-10-20-et-reception/pilot-hrus.csv'
    root=unpack(archive,output/'unpacked');frame,pilot,integrity=check_export(root,frozen)
    receipt=receive(root/'reference',output/'received',sorted(pilot.hru_id.astype(int)),integrity['start'],integrity['end'],data_origin='real_unreviewed')
    verify(output/'received')
    # Fail closed if a received partial decade contradicts declared export count.
    require(receipt['incomplete_hru_decades']==int(keyvalues(root/'export_status.txt')['incomplete_selected']),'incomplete count mismatch')
    results=output/'results';results.mkdir()
    annual,management,diagnostics=analyze(frame,pilot,pd.read_csv(root/'reference/hru_support.csv'),results)
    members=None
    if native_inputs:members=membership_audit(root,repo,native_inputs,results)
    c2=json.loads((repo/'docs/evidence/2026-10-19-work-c2/research-input-catalogue.json').read_text())
    overlap=sorted(set(pilot.hru_id)&{int(i) for i in c2['runs']})
    readiness=pilot[['hru_id','profile','bofek79','ghg_screening_bin']].copy();readiness['real_reference_received']=True
    readiness['reference_start']=integrity['start'];readiness['reference_end']=integrity['end'];readiness['c2_same_hru_research_package']=readiness.hru_id.isin(overlap)
    readiness['full_multiyear_forcing_qualified']=False;readiness['source_semantics_reviewed']=False;readiness['crop_fit_authorized']=False
    readiness=readiness.merge(management[['hru_id','zero_gift_model_guard_triggered']],on='hru_id')
    if members is not None:readiness=readiness.merge(members[['hru_id','irrigated_member_area_fraction']],on='hru_id')
    readiness.to_csv(results/'pilot-readiness.csv',index=False)
    # Compact lossless evidence retains original combined CSV bytes and manifests.
    for name in ['HRU21_reference.csv','SHA256SUMS.txt','source_manifest.csv']:
        (results/(name+'.gz')).write_bytes(gzip.compress((root/name).read_bytes(),mtime=0))
    for name in ['pilot-hrus.csv','source_hru_support.csv','source_run_identity.txt']:(results/name).write_bytes((root/name).read_bytes())
    (results/'selected-hru-support.csv').write_bytes((root/'reference/hru_support.csv').read_bytes())
    record={'status':'REAL_PILOT_RECEIVED_NOT_CALIBRATION_READY','archive_name':archive.name,'archive_sha256':digest(archive),
        'library_file_id':library_file_id,'archive_bytes':archive.stat().st_size,
        **integrity,'receipt_sha256':digest(output/'received/receipt.json'),'incomplete_hru_decades':receipt['incomplete_hru_decades'],
        'existing_c2_same_hru_overlap':overlap,'new_swap_runs':0,'factual_calibrations':0,'production_admitted':False,
        'blocking_diagnostics':['source-family units/period/sign semantic review pending','no same-HRU complete multi-year MET/BBC/fixed-gift packages',
                                'reference mixtures conflict with some zero-gift representative profiles','no independent full-year SWAP validation'],
        'code_sha256':{n:digest(repo/'tools'/n) for n in ['analyze_et_pilot_reference.py','receive_et_reference.py','et_calibration.py']}}
    write_json(results/'reception.json',record)
    (results/'receipt.json').write_bytes((output/'received/receipt.json').read_bytes())
    sums={p.name:digest(p) for p in results.iterdir() if p.is_file()};write_json(results/'artifact-sha256.json',sums)
    print(json.dumps({'reception':record,'diagnostics':diagnostics},indent=2));return record

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['archive','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--native-inputs',type=Path)
    p.add_argument('--library-file-id');a=p.parse_args();run(a.archive,a.output,a.repo,a.native_inputs,a.library_file_id)
