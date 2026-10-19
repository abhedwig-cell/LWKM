import json,struct
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from tools.process_daily_budget_plan import process
from tools.assemble_swap_package import sha256


def fixture(tmp_path,missing=False):
    def binding(path):return dict(path=str(path),sha256=sha256(path))
    def raster(name,values):
        p=tmp_path/(name+'.idf');a=np.array([values],dtype='<f4');p.write_bytes(struct.pack('<3i10f',1271,2,1,0,500,0,250,float(a.min()),float(a.max()),-9999,0,250,250)+a.tobytes());return binding(p)
    grid=raster('grid',[1,1]);e=tmp_path/'evidence.txt';e.write_text('Synthetic numerical fixture, not source semantics qualification')
    m=tmp_path/'members.csv';pd.DataFrame(dict(hru_id=[7,7],cell_id=[1,2],area_m2=[62500,62500],row=[0,0],col=[0,1])).to_csv(m,index=False)
    components={}
    for role,values in dict(flf=[1,2],right=[7,0],front=[0,0],ghb=[3,0],wel=[-1,0]).items():
        if role=='wel' and missing:values=[-9999,0]
        components[role]=[dict(layer=1,positive_multiplier=1,partitions=[raster(role,values)])]
    cfg=dict(grid=grid,model_activity_mask=grid,membership=binding(m),layer=1,units='m3/day_rate',wel_provenance='ORIGINAL_BUDGET',ghb_provenance='ORIGINAL_BUDGET',start='2020-07-01',end='2020-07-02',intervals=[dict(start='2020-07-01',end='2020-07-03',components=components)])
    cfg.update({k:binding(e) for k in ['signs_evidence','units_evidence','time_evidence','package_coverage_evidence']})
    p=tmp_path/'plan.json';p.write_text(json.dumps(cfg));return p


def test_complete_daily_pipeline_internal_cancellation_and_reuse(tmp_path):
    plan=fixture(tmp_path);r=process(plan,tmp_path/'out')
    for day in r['days']:
        f=pd.read_csv(day['files']['hrus']['path']);assert f.q_ext_m3_d.iloc[0]==5.;assert f.q_ext_mm_d.iloc[0]==pytest.approx(.04)
    r=process(plan,tmp_path/'out');assert all(f['reused'] for d in r['days'] for f in d['files'].values())
    assert r['production_admitted'] is False


def test_unknown_active_values_are_not_zero_filled(tmp_path):
    p=fixture(tmp_path,missing=True)
    with pytest.raises(ValueError,match='nonfinite'):process(p,tmp_path/'out')


def test_estimated_wel_not_accepted_without_optin(tmp_path):
    p=fixture(tmp_path);c=json.loads(p.read_text());c['wel_provenance']='ESTIMATED';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='estimated WEL'):process(p,tmp_path/'out')
