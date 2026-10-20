import gzip
import json
from pathlib import Path
import shutil
import pytest
from tools.bind_met_rasters import bind
from tools.met_grid_consumer import UNITS,run
from tests.test_d1_met_consumer import write_plan
from tools.dra_period import render_period

def test_explicit_unit_conversion_and_source_day_binding(tmp_path):
    plan=write_plan(tmp_path/'rasters');cfg=json.loads(plan.read_text());sources={}
    for k,meta in cfg['days']['2020-02-29'].items():
        p=Path(meta['path']);target=p.with_name(k+'_20200229.asc');shutil.copyfile(p,target)
        sources[k]=dict(directory=str(p.parent),pattern=k+'_{date}.asc',confirmed=True,input_unit='fixture_unit',output_unit=UNITS[k],
                        scale=2. if k=='wind_m_s' else 1.,offset=0.,evidence='synthetic explicit unit fixture')
    spec={k:cfg[k] for k in ['dataset_id','members','start','end','expected_members','expected_hrus']}
    spec.update(template=cfg['days']['2020-02-29']['rad_kj_m2_d'],sources=sources)
    sp=tmp_path/'spec.json';sp.write_text(json.dumps(spec));out=tmp_path/'bound.json'
    bind(sp,out);run(out,tmp_path/'met')
    import pandas as pd
    assert pd.read_csv(tmp_path/'met/2020-02-29.csv').wind_m_s.tolist()==[6.,6.]
    spec['sources']['wind_m_s']['confirmed']=False;sp.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='unconfirmed'):bind(sp,out)
    assert not out.exists()

def test_source_ambiguity_not_silently_selected(tmp_path):
    plan=write_plan(tmp_path/'rasters');cfg=json.loads(plan.read_text());sources={}
    for k,meta in cfg['days']['2020-02-29'].items():
        p=Path(meta['path']);target=p.with_name(k+'_20200229.asc');shutil.copyfile(p,target)
        sources[k]=dict(directory=str(p.parent),pattern=k+'_{date}*.asc',confirmed=True,input_unit=UNITS[k],output_unit=UNITS[k],scale=1.,offset=0.,evidence='fixture')
    key='wind_m_s';p=Path(cfg['days']['2020-02-29'][key]['path']);shutil.copyfile(p,p.with_name(key+'_20200229_duplicate.asc'))
    spec={k:cfg[k] for k in ['dataset_id','members','start','end','expected_members','expected_hrus']}
    spec.update(template=cfg['days']['2020-02-29']['rad_kj_m2_d'],sources=sources)
    sp=tmp_path/'spec.json';sp.write_text(json.dumps(spec))
    with pytest.raises(ValueError,match='expected one raster'):bind(sp,tmp_path/'out.json')

def test_closed_monthly_dra_cycle_repeated_without_new_hydraulics():
    with gzip.open('docs/evidence/2026-10-19-work-c2/drainage-checkpoints.jsonl.gz','rt') as f:
        record=next(r for r in map(json.loads,f) if r['hru']==3)
    before=json.dumps(record,sort_keys=True)
    text=render_period(record,4,'2020-02-28','2020-02-29')
    assert '01-feb-2020' in text and '01-mar-2020' in text
    assert json.dumps(record,sort_keys=True)==before
    record['levels'][0]['level_series']=[['1971-01-01',0.],['1971-04-01',1.]]
    with pytest.raises(ValueError,match='NONREPEATING'):render_period(record,4,'2020-01-01','2020-12-31')
