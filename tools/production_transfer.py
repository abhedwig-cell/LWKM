"""Content-addressed, restartable reception of compact HRU daily products.

No raster transfer, scientific admission, or implicit forcing substitution.
Version 1 deliberately requires one complete population-day per daily shard.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import pandas as pd
import numpy as np
from tools.assemble_swap_package import sha256
from tools.daily_forcing import MET_COLUMNS
from tools.run_dra_protected_population import atomic_json

KINDS = {'MET': MET_COLUMNS, 'BBC': ['flf_mm_d','frf_mm_d','fff_mm_d','ghb_mm_d','wel_mm_d','q_ext_mm_d']}

def relative(root, name):
    p=Path(name)
    if not name or p.is_absolute() or ':' in name or '\\' in name or '..' in p.parts:
        raise ValueError('unsafe relative product path')
    target=(root/p).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError('product path escapes root')
    return target

def receive(manifest, source, destination):
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'accepted-manifest.json').unlink(missing_ok=True)
    cfg=json.loads(manifest.read_text())
    if cfg.get('schema_version')!=1 or cfg.get('product_kind') not in KINDS:
        raise ValueError('unsupported transfer contract')
    for key in ['dataset_id','population_sha256','source_manifest_sha256','producer_sha256','units','start','end','files','hru_ids']:
        if not cfg.get(key):raise ValueError('missing transfer identity: '+key)
    for key in ['population_sha256','source_manifest_sha256','producer_sha256']:
        if len(cfg[key])!=64 or any(x not in '0123456789abcdef' for x in cfg[key]):raise ValueError('invalid SHA256 identity: '+key)
    units={'MET':'canonical_MET_units_v1','BBC':'mm/day_positive_into_L1'}
    if cfg['units']!=units[cfg['product_kind']]:raise ValueError('unbound units')
    if sha256(relative(source,cfg['source_manifest_path']))!=cfg['source_manifest_sha256']:
        raise ValueError('producer source manifest SHA256 mismatch')
    ids=cfg['hru_ids']
    if ids!=sorted(set(ids)) or any(type(i)!=int or i<=0 for i in ids):raise ValueError('invalid HRU population')
    days=pd.date_range(cfg['start'],cfg['end']).strftime('%Y-%m-%d').tolist()
    if not days or sorted(x['date'] for x in cfg['files'])!=days:raise ValueError('missing/duplicate/extra shard days')
    if len({x['path'] for x in cfg['files']})!=len(days):raise ValueError('duplicate shard paths')
    if cfg.get('status') not in ['RESEARCH_CANDIDATE','PRODUCTION_ADMITTED']:raise ValueError('explicit product status required')
    # Admission is inherited only from a separately supplied authority record,
    # never created by transport integrity checks.
    if cfg['status']=='PRODUCTION_ADMITTED':raise ValueError('transport v1 receives candidates; admission requires independent file gate')
    destination.mkdir(parents=True,exist_ok=True)
    report={'dataset_id':cfg['dataset_id'],'manifest_sha256':sha256(manifest),'production_admitted':False,'files':[],'errors':[]}
    code=sha256(Path(__file__))
    for item in cfg['files']:
        try:
            src=relative(source,item['path'])
            digest=sha256(src)
            if digest!=item['sha256']:raise ValueError('source SHA256 mismatch')
            identity={'sha256':digest,'date':item['date'],'kind':cfg['product_kind'],'ids':ids,'code':code,
                      'population_sha256':cfg['population_sha256'],'producer_sha256':cfg['producer_sha256'],
                      'source_manifest_sha256':cfg['source_manifest_sha256']}
            key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
            obj=destination/'objects'/key
            data=obj/'data.csv';metadata=obj/'verified.json'
            reuse=data.is_file() and metadata.is_file() and sha256(data)==digest and json.loads(metadata.read_text())==identity
            if not reuse:
                f=pd.read_csv(src)
                if not {'hru_id','date',*KINDS[cfg['product_kind']]}<=set(f):raise ValueError('missing consumer columns')
                if f.hru_id.tolist()!=ids or set(f.date)!={item['date']}:raise ValueError('shard population/day identity mismatch')
                if not np.isfinite(f[KINDS[cfg['product_kind']]].to_numpy(float)).all():raise ValueError('missing/nonfinite consumer values')
                if cfg['product_kind']=='BBC':
                    total=sum(f[c+'_mm_d'] for c in ['flf','frf','fff','ghb','wel'])
                    if not np.allclose(total,f.q_ext_mm_d,rtol=1e-10,atol=1e-9):raise ValueError('five-component sum mismatch')
                else:
                    a=f[MET_COLUMNS]
                    if a[['rad_kj_m2_d','wind_m_s','rain_mm_d','etref_mm_d']].lt(0).any().any():raise ValueError('negative MET')
                    if not a.vapour_pressure_kpa.between(0,10).all() or not a.wet_fraction.between(0,1).all():raise ValueError('MET HUM/WET range')
                    if (a.tmin_c>a.tmax_c).any():raise ValueError('MET Tmin>Tmax')
                    if ((a.rain_mm_d==0)&(a.wet_fraction!=0)).any() or ((a.rain_mm_d>0)&(a.wet_fraction<=0)).any():raise ValueError('MET rain duration inconsistency')
                obj.mkdir(parents=True,exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=obj,delete=False) as tmp:
                    temporary=Path(tmp.name)
                try:
                    shutil.copyfile(src,temporary)
                    if sha256(temporary)!=digest:raise ValueError('source changed during import')
                    os.replace(temporary,data)
                finally:temporary.unlink(missing_ok=True)
                atomic_json(metadata,identity)
            report['files'].append({'path':str(data.resolve()),'sha256':digest,'date':item['date'],'reused':reuse})
        except (ValueError,KeyError,OSError) as exc:
            report['errors'].append({'path':item.get('path'),'date':item.get('date'),'error':str(exc)})
    report['status']='IMPORT_VERIFIED_CANDIDATE' if not report['errors'] else 'IMPORT_BLOCKED'
    atomic_json(destination/'import-report.json',report)
    if not report['errors']:
        atomic_json(destination/'accepted-manifest.json',{**cfg,'files':report['files'],'production_admitted':False})
    else:
        # A previous success must never masquerade as the latest import.
        (destination/'accepted-manifest.json').unlink(missing_ok=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['manifest','source','destination']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();r=receive(a.manifest,a.source,a.destination)
    print(json.dumps({k:v for k,v in r.items() if k not in ['files']}))
    raise SystemExit(bool(r['errors']))
