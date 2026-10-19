import json
import numpy as np
import pandas as pd
import pytest
from tools.daily_forcing import modern_met,effective_bbc,MET_COLUMNS,weighted_weather
from tools.modflow_daily_rasters import into_cell_from_faces,integrate_intervals
from tools.server.collect_daily_consumers import collect


def weather():
    return pd.DataFrame([dict(date='2020-07-01',**dict(zip(MET_COLUMNS,[10000.,10.,20.,1.2,2.,.001,2.,.0001])))])


def test_modern_rain_and_wet_preserved_without_historical_imputation():
    text=modern_met(weather(),start='2020-07-01',end='2020-07-01',station=1)
    assert '0.001' in text and '0.0001' in text


@pytest.mark.parametrize('field,value',[('rain_mm_d',-1),('wet_fraction',0),('vapour_pressure_kpa',float('nan')),('wind_m_s',-1)])
def test_invalid_weather_rejected(field,value):
    f=weather();f[field]=value
    with pytest.raises(ValueError):modern_met(f,start='2020-07-01',end='2020-07-01',station=1)


def test_missing_weather_day_not_extended():
    with pytest.raises(ValueError):modern_met(weather(),start='2020-07-01',end='2020-07-02',station=1)


def test_area_weighted_weather_with_complete_sites():
    a=weather();a['site_id']='a';b=a.copy();b.site_id='b';b.rain_mm_d=.003
    weights=pd.DataFrame(dict(hru_id=[1,1],site_id=['a','b'],weight=[.25,.75]))
    result=weighted_weather(pd.concat([a,b]),weights,start='2020-07-01',end='2020-07-01')
    assert result.rain_mm_d.iloc[0]==pytest.approx(.0025)
    with pytest.raises(ValueError,match='missing weather'):weighted_weather(a,weights,start='2020-07-01',end='2020-07-01')


def test_daily_flux_units_and_terminal_point():
    f=pd.DataFrame(dict(date=['2020-07-01'],q_ext_mm_d=[-2.5]))
    text=effective_bbc(f,start='2020-07-01',end='2020-07-01')
    assert '2020-07-01 -0.25' in text and '2020-07-02 -0.25' in text


def test_varying_daily_means_not_silently_nodal_interpolated():
    f=pd.DataFrame(dict(date=['2020-07-01','2020-07-02'],q_ext_mm_d=[1.,2.]))
    from tools.package_preflight import dated_table
    with pytest.raises(ValueError,match='not volume-qualified'):effective_bbc(f,start='2020-07-01',end='2020-07-02')
    text=effective_bbc(f,start='2020-07-01',end='2020-07-02',experimental_daily_steps=True)
    days,rows=dated_table(text,'DATE2 QBOT2',daily_steps=True)
    assert [float(x[1]) for x in rows]==[.1,.1,.2,.2]
    with pytest.raises(ValueError,match='invalid BBC daily step'):
        dated_table(text.replace('2020-07-02 0.1','2020-07-02 0.3'),'DATE2 QBOT2',daily_steps=True)


def test_internal_face_exchange_cancels():
    r=np.array([[7.,0.]])
    np.testing.assert_array_equal(into_cell_from_faces(r,np.zeros_like(r)),[[-7.,7.]])


def test_rate_integration_split_at_midnight():
    r=integrate_intervals([('2020-07-01','2020-07-02 12:00',np.array([4.])),('2020-07-02 12:00','2020-07-03',np.array([8.]))],start='2020-07-01',end='2020-07-02')
    assert r['2020-07-01'][0]==4 and r['2020-07-02'][0]==6
    with pytest.raises(ValueError):integrate_intervals([],start='2020-07-01',end='2020-07-01')


def test_selective_collection_q4_reuse_and_source_change(tmp_path):
    src=tmp_path/'source';src.write_bytes(b'actual bytes');control=tmp_path/'control';control.write_text('source config')
    item=dict(logical_id='FLF_L1',path=str(src),role='flf',date='2020-07-01',layer=1,package='FLF',units='m3/day',consumer='GW_L1',semantics_evidence='test fixture only')
    plan=tmp_path/'plan.json';plan.write_text(json.dumps(dict(items=[item],controls=[dict(path=str(control))])))
    a=collect(plan,tmp_path/'out');assert a['qualification'].startswith('Q4_')
    b=collect(plan,tmp_path/'out');assert b['reused']==1
    control.write_text('changed configuration')
    with pytest.raises(ValueError,match='immutable bundle'):collect(plan,tmp_path/'out')


def test_catalogue_bridge_does_not_retain_historical_forcing(tmp_path):
    from tools.bind_daily_catalogue import bind
    base=tmp_path/'base.json';base.write_text(json.dumps(dict(runs={'7':{'assets':{'7.met':{'path':'old'},'7.bbc':{'path':'old'}}}},expected_population=10242,et_policy='owner_tulip_pm')))
    pairs=tmp_path/'pairs.json';pairs.write_text(json.dumps(dict(start='2020-07-01',end='2020-07-01',runs=[dict(hru_id=7,status='BLOCKED')])) )
    r=bind(base,pairs,tmp_path/'new.json')
    assert r['runs']=={} and r['start']=='2020-07-01' and r['et_policy']=='owner_tulip_pm'


def test_bbc_zero_is_a_real_token_for_swap_parser():
    f=pd.DataFrame(dict(date=['2020-07-01','2020-07-02'],q_ext_mm_d=[1.,0.]))
    text=effective_bbc(f,start='2020-07-01',end='2020-07-02',experimental_daily_steps=True)
    assert '2020-07-02 0.' in text
