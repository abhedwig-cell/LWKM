"""Synthetic end-to-end receipt-to-comparator qualification; zero factual fits."""
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
from tools.qualify_et_synthetic import synthetic
from tools.receive_et_reference import receive,reference,select_received
from tools.et_calibration import RAW,compare,select_profile,write_json
from tools.execute_swap_candidate import digest


def qualify(output, source_signs=None):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    source=output/'native';source.mkdir(parents=True)
    signs={n:1 for n in RAW} if source_signs is None else source_signs
    target=synthetic((1.25,1.));ids=[1,2,3]
    pd.DataFrame([dict(hru_id=h,svats=1,area_m2=62500) for h in ids]).to_csv(source/'hru_support.csv',index=False)
    for r in target.itertuples():
        values=dict(MSW_TACT=r.T,MSW_EBS=r.E_SOIL*.6,MSW_EPD=r.E_SOIL*.4,
                    MSW_EIC=r.E_IC*.8,MSW_ESP=r.E_IC*.2,MSW_TPOT=r.TPOT,PSGW=0.,PSSW=0.,BDGETACT=r.ET+.01)
        values={name:values[name]*signs[name] for name in RAW}
        rows=[dict(hru_id=h,days=r.days,complete=1,**values,**{'coverage_'+n:1. for n in RAW}) for h in ids]
        date=r.end.strftime('%Y%m%d');p=source/(date+'.csv');pd.DataFrame(rows).to_csv(p,index=False)
        (source/(date+'.sha256')).write_text('output='+digest(p)+'\nfixture=SYNTHETIC_ONLY\n')
    received=output/'received'
    r=receive(source,received,[2,3],'2001-01-01','2003-12-31',data_origin='synthetic')
    reused=receive(source,received,[2,3],'2001-01-01','2003-12-31',data_origin='synthetic')
    assert reused['reused']
    review=output/'synthetic-semantics-review.json'
    write_json(review,dict(status='SEMANTICS_REVIEWED',receipt_sha256=digest(received/'receipt.json'),
        unit='mm/calendar_decade',sign='positive_loss_or_gift',period='calendar_decade_amount',source_signs=signs,evidence_refs=['synthetic construction in tools/qualify_et_reception.py']))
    ref=reference(received,2,review)
    score=compare(target,ref,dict(rsc_scale=1.25,feddes_scale=1.))
    assert score['data_loss']<1e-20 and abs(score['bdgetact_residual_mm']-1.08)<1e-10
    candidates={(1.,1.):synthetic((1.,1.)),(1.25,1.):target}
    selected=select_received(received,2,review,candidates,[2001,2002],[2003])
    assert selected['status']=='BASELINE_RETAINED'
    ref.to_csv(output/'extracted-reference-hru2_SYNTHETIC.csv',index=False)
    report={'status':'SYNTHETIC_INTEGRATION_PASS','synthetic_only':True,'real_reference_received':False,
            'source_signs':signs,'raw_source_tact_preserved':bool(np.allclose(ref.MSW_TACT.to_numpy(),target['T'].to_numpy()*signs['MSW_TACT'],rtol=1e-14,atol=1e-14)),
            'native_decades':r['decades'],'native_hrus':len(ids),'received_hrus':2,
            'lossless_reception_and_reuse_pass':True,'comparison':score,'selection':selected,
            'production_admitted':False,'code_sha256':{n:digest(Path(__file__).parent/n) for n in ['receive_et_reference.py','prepare_et_pilot.py','et_calibration.py','qualify_et_reception.py']}}
    write_json(output/'qualification.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(qualify(p.parse_args().output),indent=2))
