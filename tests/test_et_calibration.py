import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from tools.et_calibration import (decade,extract,compare,overlay,design,sensitivity,
    fit_surface,predict_surface,select_profile,library_plan,load_reference,PARAMETERS,RAW)


def reference(years=(2000,2001)):
    rows=[]
    for y in years:
        for m in range(1,13):
            for day in (1,11,21):
                a,b=decade(pd.Timestamp(y,m,day));d=(b-a).days+1
                rows.append(dict(start=a,end=b,days=d,ET=3.*d,T=2.*d,E_SOIL=.7*d,E_IC=.3*d,TPOT=2.5*d,IRRIG=0.))
    return pd.DataFrame(rows)


def package(p):
    p.mkdir();(p/'swap.swp').write_text("SWETR=0\n'crop'\n")
    (p/'crop.crp').write_text('SWCF=2\nSWDROUGHT=1\nRSC=100.\nHLIM3L=-800.\nHLIM3H=-200.\nHLIM4=-8000.\n')
    (p/'a.bbc').write_text('immutable boundary')
    return p


def test_overlay_bounds_activation_and_immutability(tmp_path):
    src=package(tmp_path/'src');before={f.name:f.read_bytes() for f in src.iterdir()}
    r=overlay(src,tmp_path/'dest',dict(rsc_scale=.75,feddes_scale=1.25))
    assert r['changes']['crop.crp']['after']['HLIM3L']==-1000
    assert '7.500000000000e+01' in (tmp_path/'dest/crop.crp').read_text()
    assert before=={f.name:f.read_bytes() for f in src.iterdir()}
    assert (tmp_path/'dest/swap.swp').read_bytes()==before['swap.swp']
    with pytest.raises(ValueError):overlay(src,tmp_path/'bad',dict(rsc_scale=.5,feddes_scale=1))
    (src/'swap.swp').write_text("SWETR=1\n'crop'\n")
    with pytest.raises(ValueError):overlay(src,tmp_path/'bad',dict(rsc_scale=1,feddes_scale=1))


def test_extract_leap_decade_and_initial_exclusion(tmp_path):
    dates=pd.date_range('2000-02-20','2000-02-29');f=pd.DataFrame({'DATE':dates})
    for n in ('TACT','TPOT','EACT','EPD','EIC','IRRIG'):f[n]=.1
    f.loc[0,['TACT','EACT','EPD','EIC']]=999.
    p=tmp_path/'daily.csv';f.to_csv(p,index=False)
    d=extract(p,'2000-02-21','2000-02-29')
    assert d.days.tolist()==[9] and d.ET.tolist()==[36.]
    assert d.STRESS_FRACTION.iloc[0]==0
    with pytest.raises(ValueError):extract(p,'2000-02-22','2000-02-29')
    f=f.drop(3);f.to_csv(p,index=False)
    with pytest.raises(ValueError):extract(p,'2000-02-21','2000-02-29')


def test_objective_diagnostics_prior_calendar():
    f=reference();p=dict(rsc_scale=1,feddes_scale=1)
    assert compare(f,f,p)['objective']==0
    g=f.copy();g['T']-=g.days;g['E_SOIL']+=g.days
    c=compare(g,f,p)
    assert c['objective']==0 and c['components']['T']['bias_mm']<0
    assert compare(f,f,dict(rsc_scale=1.25,feddes_scale=1))['regularization']==.025
    with pytest.raises(ValueError):compare(f.iloc[1:],f,p)
    with pytest.raises(ValueError):compare(f,pd.concat([f,f.iloc[:1]]),p)
    g=f.copy();g.loc[0,'ET']=np.nan
    with pytest.raises(ValueError):compare(g,f,p)


def test_surface_offgrid_and_no_extrapolation():
    p=np.array([[x['rsc_scale'],x['feddes_scale']] for x in design(True)])
    y=(p[:,0]**2+2*p[:,1]+3*p[:,0]*p[:,1])[:,None]
    s=fit_surface(p,y);q=np.array([[1.125,.875]])
    assert predict_surface(s,q)[0,0]==pytest.approx(q[0,0]**2+2*q[0,1]+3*q[0,0]*q[0,1])
    with pytest.raises(ValueError):predict_surface(s,[[1.5,1.]])
    with pytest.raises(ValueError):fit_surface(p[:4],y[:4])


def test_identical_parameter_responses_flagged():
    b=reference((2000,));out={}
    for x in design():
        g=b.copy();g.ET+=g.days*(x['rsc_scale']+x['feddes_scale']-2)
        g['T']+=g.days*(x['rsc_scale']+x['feddes_scale']-2)
        out[(x['rsc_scale'],x['feddes_scale'])]=g
    assert sensitivity(out)['weak_or_confounded']
    assert sensitivity(out)['derivative_cosine']==pytest.approx(1.)


def test_selection_requires_independent_years_irrigation_components():
    r=reference();b=r.copy();b.ET+=b.days*.5;b['T']+=b.days*.5
    c={(1.,1.):b,(1.25,1.):r.copy()}
    v=select_profile(c,r,[2000],[2001],real_reference=True,context_verified=True)
    assert v['status']=='RESEARCH_PROFILE_PROPOSED'
    assert v['applied_parameters']['rsc_scale']==1.25
    assert select_profile(c,r,[2000],[2001])['status']=='BASELINE_RETAINED'
    with pytest.raises(ValueError):select_profile(c,r,[2000],[2000])
    with pytest.raises(ValueError):select_profile(c,r,[2000],[2002])
    c[(1.25,1.)].IRRIG=10.
    assert 'irrigation mismatch' in str(select_profile(c,r,[2000],[2001],real_reference=True,context_verified=True))
    c[(1.25,1.)].IRRIG=0.;c[(1.25,1.)]['T']-=c[(1.25,1.)].days;c[(1.25,1.)]['E_SOIL']+=c[(1.25,1.)].days
    assert 'partition requires review' in str(select_profile(c,r,[2000],[2001],real_reference=True,context_verified=True))
    c[(1.25,1.)]=r.copy();c[(1.25,1.)].loc[r.start.dt.year==2001,['ET','T']]+=100
    assert 'no independent-year improvement' in str(select_profile(c,r,[2000],[2001],real_reference=True,context_verified=True))


def test_library_management_and_forcing_gates():
    f=pd.DataFrame([dict(case_id='a',bofek=1,landuse='nature',irrigated=True,groundwater='deep',weather='dry',forcing_qualified=True,soil_family='sand')])
    with pytest.raises(ValueError):library_plan(f)
    f.irrigated=False;f.forcing_qualified=False
    assert library_plan(f)['screening_runs']==0
    f.forcing_qualified=True
    assert library_plan(f)['screening_runs']==5


def native(tmp_path,complete=1):
    a,b=decade('2000-02-21');r=dict(hru_id=1,days=9,complete=complete)
    r.update({k:1. for k in RAW});r.update({'coverage_'+k:1. for k in RAW})
    p=tmp_path/'20000229.csv';pd.DataFrame([r]).to_csv(p,index=False)
    (tmp_path/'20000229.sha256').write_text('output='+hashlib.sha256(p.read_bytes()).hexdigest()+'\n')
    return p


def test_native_reference_components_coverage_hash_and_semantics(tmp_path):
    p=native(tmp_path)
    with pytest.raises(ValueError):load_reference(tmp_path,1)
    f=load_reference(tmp_path,1,semantic_qualified=True)
    assert f.ET.tolist()==[5.] and f.IRRIG.tolist()==[2.]
    assert f.BDGETACT_RESIDUAL.tolist()==[-4.]
    p.write_text(p.read_text()+'\n')
    with pytest.raises(ValueError):load_reference(tmp_path,1,semantic_qualified=True)
    native(tmp_path,0)
    with pytest.raises(ValueError):load_reference(tmp_path,1,semantic_qualified=True)


def test_scheduled_irrigation_and_feddes_order_rejected(tmp_path):
    src=package(tmp_path/'src')
    crop=src/'crop.crp';crop.write_text(crop.read_text()+'SCHEDULE=1\n')
    with pytest.raises(ValueError,match='scheduled irrigation'):
        overlay(src,tmp_path/'irrig',dict(rsc_scale=1,feddes_scale=1))
    crop.write_text(crop.read_text().replace('SCHEDULE=1','SCHEDULE=0').replace('HLIM4=-8000.','HLIM4=-850.'))
    with pytest.raises(ValueError,match='Feddes order'):
        overlay(src,tmp_path/'order',dict(rsc_scale=1,feddes_scale=1.25))


def test_selection_nonconsecutive_training_and_partial_year_block():
    r=reference((2000,2001,2002));b=r.copy();b.ET+=b.days*.5;b['T']+=b.days*.5
    c={(1.,1.):b,(1.25,1.):r.copy()}
    v=select_profile(c,r,[2000,2002],[2001],real_reference=True,context_verified=True)
    assert v['status']=='RESEARCH_PROFILE_PROPOSED' and len(v['yearwise_winners'])==3
    r=r.iloc[:-1].copy();c={k:f.iloc[:-1].copy() for k,f in c.items()}
    with pytest.raises(ValueError,match='complete independent'):
        select_profile(c,r,[2000,2001],[2002])


def test_inconsistent_components_and_zero_potential():
    r=reference();bad=r.copy();bad.ET+=1
    with pytest.raises(ValueError,match='component sum'):compare(bad,r,dict(rsc_scale=1,feddes_scale=1))
    r.TPOT=0
    assert compare(r,r,dict(rsc_scale=1,feddes_scale=1))['stress_reference'] is None
