import json
import os
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
import pytest
from tools.met_grid_consumer import day,support,run,UNITS,FIELDS,nearest
from tools.assemble_swap_package import sha256

def inputs():
    g=dict(ncols=2,nrows=2,xllcorner=0,yllcorner=0,cellsize=1000,nodata_value=-9999)
    members=pd.DataFrame(dict(hru_id=[1,1,2],svat_id=[10,11,12],x_rd=[125.,875.,1500.],y_rd=[1125.,1875.,500.],area_m2=[1.,3.,2.]))
    w,m=support(members,g)
    values=dict(rad_kj_m2_d=10000.,tmin_c=10.,tmax_c=20.,vapour_pressure_kpa=1.,wind_m_s=3.,rain_mm_d=2.,etref_mm_d=1.,wet_raw_fraction=.5)
    arrays={k:np.full((2,2),v) for k,v in values.items()}
    return g,members,w,m,arrays

def test_wet_before_averaging_and_zero_duration_fallback():
    g,_,w,m,a=inputs();a['rain_mm_d'][0,0]=0;a['wet_raw_fraction'][1,1]=0
    f,audit,qa=day(w,m,a,g,'2020-02-29')
    assert f.wet_fraction.tolist()==[0.,.1] and f.wind_m_s.tolist()==[3.,3.]
    assert qa['fallback_svat_count']==1 and qa['fallback_area_m2']==2.

def test_missing_cells_keep_original_member_distances_and_weights():
    g,_,w,m,a=inputs()
    # Both HRU1 SVATs share a missing pixel, but have different nearest cells.
    a['rain_mm_d']=np.array([[-9999.,8.],[2.,3.]])
    f,audit,qa=day(w,m,a,g,'2020-02-29',{'rain_mm_d':'a'*64})
    assert f.rain_mm_d.iloc[0]==pytest.approx(.25*2+.75*8)
    assert set(audit.replacement_grid)=={1,2}
    assert len(audit)==2 and (audit.source_sha256=='a'*64).all()
    assert f.wet_fraction.iloc[0]==.5

def test_nearest_rejects_invalid_semantics_preserves_zero_and_ties():
    g,_,w,m,a=inputs();a['wind_m_s']=np.array([[-1.,0.],[5.,3.]])
    f,audit,_=day(w,m,a,g,'2020-02-29');assert f.wind_m_s.iloc[0]==pytest.approx(1.25)
    picked,_=nearest(np.array([[1000.,1000.]]),np.array([0,1,2,3]),g)
    assert picked.tolist()==[0]
    a['wind_m_s'][:]=np.nan
    with pytest.raises(ValueError,match='no valid'):day(w,m,a,g,'2020-02-29')

def test_missing_raw_grid_uses_explicit_wet_fallback_only():
    g,_,w,m,a=inputs();a['wet_raw_fraction'][:]=-9999
    f,_,qa=day(w,m,a,g,'2020-02-29');assert f.wet_fraction.tolist()==[.1,.1]
    assert qa['fallback_svat_count']==3

def write_plan(root):
    g,m,_,_,arrays=inputs();root.mkdir(exist_ok=True)
    member=root/'members.csv';m.to_csv(member,index=False)
    cfg=dict(dataset_id='SYNTHETIC_INTEGRATION_ONLY',expected_members=3,expected_hrus=2,geometry=g,units=UNITS,
             members=dict(path=str(member.resolve()),sha256=sha256(member)),start='2020-02-29',end='2020-02-29',days={})
    cfg['days'][cfg['start']]={}
    for k,a in arrays.items():
        p=root/(k+'.asc')
        with p.open('w') as f:
            for key,v in g.items():f.write(f'{key} {v}\n')
            np.savetxt(f,a)
        cfg['days'][cfg['start']][k]=dict(path=str(p.resolve()),sha256=sha256(p))
    plan=root/'plan.json';plan.write_text(json.dumps(cfg));return plan

def test_day_batch_hash_geometry_leap_day_and_reuse(tmp_path):
    plan=write_plan(tmp_path/'input with spaces');out=tmp_path/'output'
    if os.environ.get('LWKM_MET_EXE'):
        exe=str(Path(os.environ['LWKM_MET_EXE']).resolve())
        subprocess.run([exe,'--plan',str(plan),'--output',str(out)],check=True)
        subprocess.run([exe,'--plan',str(plan),'--output',str(out)],check=True)
        result=json.loads((out/'manifest.json').read_text())['files']
    else:
        run(plan,out);result=run(plan,out)
    assert result[0]['reused'] is True
    from tools.production_transfer import receive
    r=receive(out/'transfer.json',out,tmp_path/'import')
    assert r['status']=='IMPORT_VERIFIED_CANDIDATE'
    cfg=json.loads(plan.read_text());cfg['days']['2020-02-29']['wind_m_s']['sha256']='0'*64;plan.write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='hash mismatch'):run(plan,out)

def test_daily_grid_weights_equal_independent_svat_weighting():
    g,original,w,m,a=inputs();a['rain_mm_d']=np.array([[0.,1.],[3.,7.]])
    f,_,_=day(w,m,a,g,'2020-02-29')
    expected=[]
    for hid,group in m.groupby('hru_id'):
        expected.append(sum(a['rain_mm_d'].ravel()[group.grid_id]*group.area_m2)/group.area_m2.sum())
    np.testing.assert_allclose(f.rain_mm_d,expected,rtol=0,atol=1e-14)
