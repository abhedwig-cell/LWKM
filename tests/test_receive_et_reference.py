import json
from pathlib import Path
import pandas as pd
import pytest
from tools.et_calibration import RAW
from tools.execute_swap_candidate import digest
from tools.receive_et_reference import receive,verify,reference,calendar_ends


def native(root,start='2001-01-01',end='2001-01-31',incomplete=False):
    root.mkdir();pd.DataFrame([dict(hru_id=i,svats=1,area_m2=62500) for i in (1,2)]).to_csv(root/'hru_support.csv',index=False)
    for date in calendar_ends(start,end):
        rows=[]
        for hid in (1,2):
            r=dict(hru_id=hid,days=11 if date.endswith('31') else 10,complete=1)
            r.update({n:'1.234567890' for n in RAW});r.update({'coverage_'+n:'1' for n in RAW})
            if incomplete and hid==2:r.update(complete=0,MSW_EBS='',coverage_MSW_EBS='.5')
            rows.append(r)
        path=root/(date+'.csv');pd.DataFrame(rows).to_csv(path,index=False)
        (root/(date+'.sha256')).write_text('output='+digest(path)+'\nproducer='+'1'*64+'\n')
    return root


def test_receive_lossless_subset_semantic_gate_and_idempotence(tmp_path):
    src=native(tmp_path/'source');out=tmp_path/'received'
    r=receive(src,out,[2],'2001-01-01','2001-01-31',data_origin='synthetic')
    assert r['decades']==3 and not r['production_admitted'] and not r['scientific_reference_qualified']
    assert pd.read_csv(out/'20010110.csv',dtype=str).MSW_EBS.iloc[0]=='1.234567890'
    assert receive(src,out,[2],'2001-01-01','2001-01-31',data_origin='synthetic')['reused']
    review=tmp_path/'review.json';review.write_text(json.dumps({'status':'PENDING'}))
    with pytest.raises(ValueError,match='review not bound'):reference(out,2,review)
    review.write_text(json.dumps(dict(status='SEMANTICS_REVIEWED',receipt_sha256=digest(out/'receipt.json'),
        unit='mm/calendar_decade',sign='positive_loss_or_gift',period='calendar_decade_amount',evidence_refs=['synthetic unit fixture'])))
    f=reference(out,2,review)
    assert len(f)==3 and f.ET.iloc[0]==pytest.approx(5*1.234567890)
    (out/'20010110.csv').write_text('tampered')
    with pytest.raises(ValueError,match='changed'):verify(out)
    with pytest.raises(ValueError):receive(src,out,[2],'2001-01-01','2001-01-31',data_origin='synthetic')


def test_incomplete_preserved_not_filled(tmp_path):
    src=native(tmp_path/'source',incomplete=True);out=tmp_path/'received'
    r=receive(src,out,[2],'2001-01-01','2001-01-31',data_origin='real_unreviewed')
    assert r['incomplete_hru_decades']==3
    assert pd.read_csv(out/'20010110.csv').MSW_EBS.isna().all()


def test_missing_period_bad_hash_bad_calendar(tmp_path):
    src=native(tmp_path/'source');out=tmp_path/'received'
    (src/'20010120.csv').unlink()
    with pytest.raises(FileNotFoundError):receive(src,out,[1],'2001-01-01','2001-01-31',data_origin='synthetic')
    assert not out.exists()
    (src/'20010110.csv').write_text('wrong')
    with pytest.raises(ValueError,match='hash mismatch'):receive(src,out,[1],'2001-01-01','2001-01-10',data_origin='synthetic')
    with pytest.raises(ValueError):calendar_ends('2001-01-02','2001-01-31')


def test_manifest_path_and_fractional_day_rejected(tmp_path):
    src=native(tmp_path/'source');out=tmp_path/'received'
    p=src/'20010110.csv';f=pd.read_csv(p);f['days']=10.5;f.to_csv(p,index=False)
    (src/'20010110.sha256').write_text('output='+digest(p)+'\n')
    with pytest.raises(ValueError,match='length'):receive(src,out,[1],'2001-01-01','2001-01-10',data_origin='synthetic')


def test_pilot_deterministic_diverse_and_no_blocked_selection():
    from tools.prepare_et_pilot import select_prototypes
    f=pd.DataFrame([dict(hru_id=i,profile='grass_rainfed',ghg_screening_bin='deep_proxy',
       ghg_median_cm=100+i,net_kwel_median_mm_y=20.,root_limit_cm=40.,bofek79=i,
       structural_blocked=i==1,soil_binding_unresolved=i==2) for i in (1,2,3,4)])
    a=select_prototypes(f);b=select_prototypes(f.sample(frac=1,random_state=4))
    assert a.hru_id.tolist()==b.hru_id.tolist()==[3]


@pytest.mark.parametrize('negative_gifts',[False,True])
def test_explicit_mixed_source_signs_keep_raw_values_and_normalize_gifts(tmp_path,negative_gifts):
    from tools.et_calibration import compare
    src=native(tmp_path/'source')
    signs={name:(1 if name in ('PSGW','PSSW') and not negative_gifts else -1) for name in RAW}
    for p in src.glob('????????.csv'):
        f=pd.read_csv(p)
        for name in RAW:f[name]*=signs[name]
        f.to_csv(p,index=False)
        p.with_suffix('.sha256').write_text('output='+digest(p)+'\n')
    out=tmp_path/'received';receive(src,out,[2],'2001-01-01','2001-01-31',data_origin='synthetic')
    before={p.name:digest(p) for p in out.iterdir()}
    review=tmp_path/'review.json'
    body=dict(status='SEMANTICS_REVIEWED',receipt_sha256=digest(out/'receipt.json'),
        unit='mm/calendar_decade',sign='positive_loss_or_gift',period='calendar_decade_amount',
        evidence_refs=['synthetic known-sign construction'],source_signs=signs)
    review.write_text(json.dumps(body));f=reference(out,2,review)
    assert f.MSW_EBS.iloc[0]<0 and f.NORMALIZED_MSW_EBS.iloc[0]>0
    assert f.PSGW.iloc[0]*signs['PSGW']>0 and f.SOURCE_SIGN_PSGW.iloc[0]==signs['PSGW']
    assert f.ET.iloc[0]==pytest.approx(5*1.234567890)
    assert f.BDGETACT_RESIDUAL.iloc[0]==pytest.approx(-4*1.234567890)
    score=compare(f,f,dict(rsc_scale=1.,feddes_scale=1.))
    assert score['data_loss']==0 and score['psgw_reference_mm']==pytest.approx(f.NORMALIZED_PSGW.sum())
    assert before=={p.name:digest(p) for p in out.iterdir()}
    assert f.attrs['semantic_review_sha256']==digest(review)
    body.pop('source_signs');review.write_text(json.dumps(body))
    with pytest.raises(ValueError,match='negative loss/gift'):reference(out,2,review)
    for invalid in (None,[],{'MSW_EBS':-1},{**signs,'PSGW':0},{**signs,'PSGW':True},{**signs,'PSGW':1.0}):
        body['source_signs']=invalid;review.write_text(json.dumps(body))
        with pytest.raises(ValueError,match='source signs'):reference(out,2,review)
