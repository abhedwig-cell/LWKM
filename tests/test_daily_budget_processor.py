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
    with pytest.raises(ValueError,match='unqualified wel'):process(p,tmp_path/'out')


def reconstructed_plan(tmp_path):
    p=fixture(tmp_path);c=json.loads(p.read_text())
    for role in ['wel','ghb']:
        c[role+'_provenance']='RECONSTRUCTED_OPERATIONAL'
        c.setdefault('reconstructed_products',{})[role]=dict(method='existing reconstruction',limitations=['Synthetic fixture; not original MODFLOW budget'],evidence=c['signs_evidence'])
    # Already aggregated cell LAT: -7,+7 cancel within this HRU.
    parts=c['intervals'][0]['components'];parts['lat']=parts.pop('right');parts.pop('front')
    path=Path(parts['lat'][0]['partitions'][0]['path'])
    data=bytearray(path.read_bytes());data[-8:]=struct.pack('<2f',-7,7);path.write_bytes(data)
    parts['lat'][0]['partitions'][0]['sha256']=sha256(path)
    p.write_text(json.dumps(c));return p


def test_owner_accepted_reconstructed_direct_lat_and_identity(tmp_path):
    p=reconstructed_plan(tmp_path);r=process(p,tmp_path/'out')
    assert r['wel_provenance']=='RECONSTRUCTED_OPERATIONAL'
    f=pd.read_csv(r['days'][0]['files']['hrus']['path'])
    assert f.q_ext_m3_d.iloc[0]==5.
    assert f.q_ext_mm_d.iloc[0]==pytest.approx(.04)
    r=process(p,tmp_path/'out');assert all(f['reused'] for d in r['days'] for f in d['files'].values())
    c=json.loads(p.read_text());Path(c['intervals'][0]['components']['wel'][0]['partitions'][0]['path']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash mismatch'):process(p,tmp_path/'out')


def test_reconstructed_contract_and_no_double_lat(tmp_path):
    p=reconstructed_plan(tmp_path);c=json.loads(p.read_text());saved=c['reconstructed_products'].pop('ghb');p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='method and limitations'):process(p,tmp_path/'out')
    c['reconstructed_products']['ghb']=saved
    c['intervals'][0]['components']['right']=c['intervals'][0]['components']['lat'];p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='mix net LAT'):process(p,tmp_path/'out')


def test_existing_series_binding_and_missing_day(tmp_path):
    from tools.server.bind_reconstructed_daily import bind
    import shutil
    p=reconstructed_plan(tmp_path);base=json.loads(p.read_text());sources={}
    for role,terms in base.pop('intervals')[0]['components'].items():
        root=tmp_path/role;root.mkdir()
        for day in ['20200701','20200702']:
            shutil.copyfile(terms[0]['partitions'][0]['path'],root/f'bdg{role}_{day}_l1.IDF')
        sources[role]=dict(directory=str(root),pattern='*_{date}_l1.IDF',positive_multiplier=1,provenance='RECONSTRUCTED_OPERATIONAL',semantics_evidence='fixture only')
    cfg=tmp_path/'bindings.json';cfg.write_text(json.dumps(dict(processing_contract=base,sources=sources,controls=[base['signs_evidence']])))
    out=tmp_path/'bindings';r=bind(cfg,out);assert r['complete'] and r['files']==8
    result=process(out/'processing-plan.json',tmp_path/'results');assert len(result['days'])==2
    # Existing collection is fully reused; no reconstruction occurs.
    from tools.server.collect_daily_consumers import collect
    first=collect(out/'collection-plan.json',tmp_path/'collected')
    second=collect(out/'collection-plan.json',tmp_path/'collected')
    assert all(x['reused'] for x in second['files'])
    (tmp_path/'ghb'/'bdgghb_20200702_l1.IDF').unlink()
    r=bind(cfg,out);assert not r['complete'] and not (out/'processing-plan.json').exists()
