"""Execute national-population D1 integration with explicitly SYNTHETIC forcing.

Real support, contexts, crop sources and C2 DRA are retained. No synthetic
weather or flux value is represented as a measured/server production result.
"""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.met_grid_consumer import support,run as met_run,UNITS
from tools.prepare_d1_assets import prepare
from tools.work_d1 import run as workflow
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json

ROOT=Path(__file__).resolve().parents[1]
def binding(p):return dict(path=str(p.resolve()),sha256=sha256(p))

def qualify(workbook,templates,output):
    output.mkdir(parents=True,exist_ok=True)
    fixture=ROOT/'tools/metaswap_hru/tests/supplied_members.csv.gz'
    members=pd.read_csv(fixture).rename(columns={'svat_orig':'svat_id','HRU':'hru_id','x':'x_rd','y':'y_rd'})
    member_path=output/'members.csv';members.to_csv(member_path,index=False,float_format='%.15g')
    g=dict(ncols=300,nrows=325,xllcorner=0,yllcorner=300000,cellsize=1000,nodata_value=-9999)
    weights,m=support(members,g);wp=output/'weights.csv';weights.to_csv(wp,index=False,float_format='%.15g')
    if sha256(wp)!='6133a918a0a05bd4b1b384fc88a1d13df7bd49d26c1723b242b319a667712f7c':raise ValueError('owner weight regression changed')
    grid=output/'synthetic-grids';grid.mkdir(exist_ok=True);days=['1971-03-01','1971-03-02','1971-03-03']
    cfg=dict(dataset_id='D1_SYNTHETIC_ONLY_REAL_POPULATION',members=binding(member_path),expected_members=427656,expected_hrus=10242,
             geometry=g,units=UNITS,start=days[0],end=days[-1],days={})
    fields=dict(rad_kj_m2_d=10000.,tmin_c=8.,tmax_c=18.,vapour_pressure_kpa=1.,wind_m_s=3.,rain_mm_d=2.,etref_mm_d=1.,wet_raw_fraction=.5)
    for i,day in enumerate(days):
        cfg['days'][day]={}
        for key,v in fields.items():
            p=grid/(day+'-'+key+'.asc');a=np.full((325,300),v)
            if key=='rain_mm_d':a[:,::2]=0.;a[:,1::2]=2.+i
            if key=='wet_raw_fraction':a[::2,:]=0.
            with p.open('w') as f:
                for k,x in g.items():f.write(f'{k} {x}\n')
                np.savetxt(f,a,fmt='%.6g')
            cfg['days'][day][key]=binding(p)
    mp=output/'met-plan.json';atomic_json(mp,cfg);met_run(mp,output/'met')
    # Independent direct original-SVAT calculation, not the compressed consumer.
    rain=np.where(m.grid_id.to_numpy()%300%2==0,0.,2.)
    direct=pd.DataFrame(dict(hru_id=m.hru_id,part=rain*m.area_m2)).groupby('hru_id').part.sum()/members.groupby('hru_id').area_m2.sum()
    actual=pd.read_csv(output/'met'/('1971-03-01.csv')).set_index('hru_id').rain_mm_d
    max_error=float(abs(direct-actual).max())
    if max_error>1e-10:raise ValueError('independent national SVAT MET regression')
    gw=output/'bbc';gw.mkdir(exist_ok=True);files=[]
    for i,day in enumerate(days):
        f=pd.DataFrame(dict(hru_id=np.arange(1,10243),date=day,flf_mm_d=1.+i,frf_mm_d=.2,fff_mm_d=-.2,ghb_mm_d=.4,wel_mm_d=-.3,q_ext_mm_d=1.1+i))
        p=gw/(day+'.csv');f.to_csv(p,index=False);files.append(dict(date=day,path=p.name,sha256=sha256(p)))
    source=gw/'source.json';atomic_json(source,dict(status='SYNTHETIC_ONLY',components=['FLF','FRF','FFF','GHB','WEL']))
    transfer=dict(schema_version=1,product_kind='BBC',dataset_id='D1_SYNTHETIC_ONLY_REAL_POPULATION',population_sha256=sha256(member_path),
                  source_manifest_sha256=sha256(source),source_manifest_path=source.name,producer_sha256=sha256(Path(__file__)),units='mm/day_positive_into_L1',
                  start=days[0],end=days[-1],hru_ids=list(range(1,10243)),status='RESEARCH_CANDIDATE',files=files)
    atomic_json(gw/'transfer.json',transfer)
    b=ROOT/'docs/evidence/2026-10-19-work-b/interfaces';contexts=b/'HRU_CONTEXT_10242.jsonl.gz'
    assets=prepare(workbook,templates,contexts,b/'HRU_REPRESENTATIVE.csv.gz',b/'SVAT_QUALIFIED.csv.gz',output/'assets')
    import zipfile
    with zipfile.ZipFile(templates) as z:(output/'wwl.swp').write_bytes(z.read('Template/wwl.swp'))
    plan=dict(mode='RESEARCH_ONLY',met=dict(manifest=binding(output/'met/transfer.json'),source=str((output/'met').resolve())),
              bbc=dict(manifest=binding(gw/'transfer.json'),source=str(gw.resolve())),contexts=binding(contexts),template=binding(output/'wwl.swp'),
              dra_bundle=binding(ROOT/'docs/evidence/2026-10-19-work-c2/all-dra-files.jsonl.gz'),asset_catalogue=binding(output/'assets/catalogue.json'))
    p=output/'workflow-plan.json';atomic_json(p,plan)
    first=workflow(p,output/'chain');atomic_json(output/'initial-build.json',first)
    second=workflow(p,output/'chain')
    counts={}
    for r in first['runs']:
        if r['status']=='BLOCKED':counts[r['error']]=counts.get(r['error'],0)+1
    report=dict(status='SYNTHETIC_INTEGRATION_ONLY',production_admitted=False,population=10242,svats=427656,grid_links=len(weights),
                area_m2=float(members.area_m2.sum()),weights_sha256=sha256(wp),independent_max_MET_error=max_error,
                first_complete=first['complete_packages'],second_complete=second['complete_packages'],second_reused=second['reused_packages'],
                blockers=counts,asset_errors=assets['errors'],nature_overrides=assets['nature_irrigation_overrides'],days=days,
                sources={str(p.name):sha256(p) for p in [fixture,workbook,templates,contexts]},
                real_server_outputs_read=False,new_real_forcing_runs=0)
    atomic_json(output/'qualification.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['workbook','templates','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(qualify(a.workbook,a.templates,a.output),indent=2))
