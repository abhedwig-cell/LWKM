import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from tools.analyze_et_pilot_reference import (COLUMNS, RAW, analyze, unpack)


def frames():
    pilot=pd.read_csv(Path(__file__).resolve().parents[1]/'docs/evidence/2026-10-20-et-reception/pilot-hrus.csv')
    rows=[]
    for d in pd.date_range('2001-01-01','2001-12-31'):
        if d.day not in (10,20) and d!=d+pd.offsets.MonthEnd(0):continue
        for i in pilot.hru_id:
            raw=dict(zip(RAW,[-1,-1,-1,0,-1,-2,0,0,-4]))
            if i==224:raw['PSSW']=2
            rows.append(dict(hru_id=i,days=10 if d.day<=20 else d.day-20,complete=1,**raw,
                E_SOIL_POND=-2,E_INTERCEPTION_SPRINKLING=-1,T_ACTUAL=-1,ET_ACTUAL=-4,
                IRR_TOTAL=raw['PSSW'],BDGETACT_MINUS_ET=0,**{'coverage_'+n:1 for n in RAW},decade_end=d.strftime('%Y%m%d')))
    return pd.DataFrame(rows),pilot,pd.DataFrame({'hru_id':pilot.hru_id,'area_m2':1})


def test_diagnostics_keep_raw_values_and_do_not_open_gates(tmp_path):
    f,p,s=frames();before=f.copy(deep=True)
    annual,management,result=analyze(f,p,s,tmp_path)
    pd.testing.assert_frame_equal(f,before)
    assert result['full_hru_years']==21
    assert np.allclose(annual.ET,144) and np.allclose(annual.reduction_fraction,.5)
    assert result['max_abs_bdgetact_residual_mm_decade']==0
    assert result['rainfed_agricultural_hrus_with_irrigation_guard']==[224]
    assert not result['production_admitted'] and result['factual_calibrations']==0
    assert result['semantic_review_status'].startswith('PENDING')
    assert result['no_weather_years_classified'] and result['no_training_or_validation_years_assigned']
    assert management.loc[management.hru_id==224,'max_irrigation_mm_y'].iloc[0]==72


def test_tiny_negative_reduction_is_reported_without_clipping(tmp_path):
    f,p,s=frames();f['MSW_TPOT']=f.MSW_TPOT.astype(float);f.loc[0,'MSW_TPOT']=-.999999
    _,_,r=analyze(f,p,s,tmp_path)
    assert r['max_tact_over_tpot_mm_decade']==pytest.approx(1e-6)
    assert r['negative_reduction_not_clipped'] and r['tact_over_tpot_rows_1e_5mm']==0


@pytest.mark.parametrize('kind',['nonfinite','incomplete','wrong_derived','nature_irrigation'])
def test_fail_closed_scientific_contradictions(tmp_path,kind):
    f,p,s=frames()
    if kind=='nonfinite':f.loc[0,'MSW_EBS']=np.nan
    elif kind=='incomplete':f.loc[0,'complete']=0
    elif kind=='wrong_derived':f.loc[0,'ET_ACTUAL']=-9
    else:
        idx=f.index[f.hru_id==6173][0];f.loc[idx,['PSSW','IRR_TOTAL']]=1
    with pytest.raises(ValueError):analyze(f,p,s,tmp_path)


@pytest.mark.parametrize('names',[['root/../outside'],['C:/outside'],['/outside'],['root/a','root\\a']])
def test_reject_unsafe_zip_paths_and_separator_aliases(tmp_path,names):
    z=tmp_path/'unsafe.zip'
    with zipfile.ZipFile(z,'w') as f:
        for n in names:f.writestr(n,'test')
    with pytest.raises(ValueError):unpack(z,tmp_path/'out')


def test_windows_separator_archive_is_supported(tmp_path):
    z=tmp_path/'good.zip'
    with zipfile.ZipFile(z,'w') as f:f.writestr('root\\reference\\20010110.csv','a,b\r\n1,2\r\n')
    out=unpack(z,tmp_path/'out')
    assert (out/'reference/20010110.csv').read_bytes()==b'a,b\r\n1,2\r\n'


def test_endpoint_discontinuity_is_a_flag_not_a_weather_class(tmp_path):
    original,p,s=frames();blocks=[]
    for year in range(2001,2012):
        f=original.copy();dates=pd.to_datetime(f.decade_end)
        ends=[d.replace(year=year) if d.day<=20 else pd.Timestamp(year,d.month,1)+pd.offsets.MonthEnd(0) for d in dates]
        f['decade_end']=[d.strftime('%Y%m%d') for d in ends]
        f['days']=[10 if d.day<=20 else d.day-20 for d in ends]
        if year==2011:f[RAW+['E_SOIL_POND','E_INTERCEPTION_SPRINKLING','T_ACTUAL','ET_ACTUAL','IRR_TOTAL','BDGETACT_MINUS_ET']]*=.5
        blocks.append(f)
    _,_,result=analyze(pd.concat(blocks,ignore_index=True),p,s,tmp_path)
    assert result['endpoint_year_screen']==2011
    assert set(result['endpoint_year_et_below_60pct_previous_10_years_hrus'])==set(p.hru_id)
    assert result['no_weather_years_classified']
