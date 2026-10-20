"""Entirely synthetic multi-year tests; no LHM observations or HRU calibration."""
import argparse,copy
from pathlib import Path
import numpy as np
import pandas as pd
from tools.et_calibration import decade,design,select_profile,write_json


def synthetic(scale,years=(2001,2002,2003)):
    rows=[]
    for y in years:
        for m in range(1,13):
            for day in (1,11,21):
                a,b=decade(pd.Timestamp(y,m,day));d=(b-a).days+1
                season=max(.1,np.sin(np.pi*(m-1)/12))
                # Known artificial response; no inferred physical truth.
                t=2*season+6*(scale[0]-1)*season+2*(scale[1]-1)*season**2
                e=.7;ic=.3;irrig=0.
                rows.append(dict(start=a,end=b,days=d,T=t*d,E_SOIL=e*d,E_IC=ic*d,ET=(t+e+ic)*d,TPOT=4*d,IRRIG=irrig))
    return pd.DataFrame(rows)


def qualify(output):
    output.mkdir(parents=True)
    target=synthetic((1.25,1.))
    candidates={(p['rsc_scale'],p['feddes_scale']):synthetic((p['rsc_scale'],p['feddes_scale'])) for p in design(True)}
    positive=select_profile(candidates,target,[2001,2002],[2003],real_reference=True,context_verified=True)
    assert positive['applied_parameters']==dict(rsc_scale=1.25,feddes_scale=1.)
    # real_reference=True above exercises the admission branch only; all bytes
    # remain synthetic and the published result below explicitly labels them.
    synthetic_guard=select_profile(candidates,target,[2001,2002],[2003])
    assert synthetic_guard['status']=='BASELINE_RETAINED'
    partition=copy.deepcopy(candidates)
    transfer=partition[(1.25,1.)]['T']*.6
    partition[(1.25,1.)]['T']-=transfer;partition[(1.25,1.)]['E_SOIL']+=transfer
    partition_guard=select_profile(partition,target,[2001,2002],[2003],real_reference=True,context_verified=True)
    assert partition_guard['status']=='BASELINE_RETAINED'
    irrigation=target.copy();irrigation.IRRIG=10.
    irrigation_guard=select_profile(candidates,irrigation,[2001,2002],[2003],real_reference=True,context_verified=True)
    assert irrigation_guard['status']=='BASELINE_RETAINED'
    reverse=copy.deepcopy(candidates)
    for k,f in reverse.items():
        if k!=(1.,1.):f.loc[f.start.dt.year==2003,['ET','T']]+=1000.
    reversal_guard=select_profile(reverse,target,[2001,2002],[2003],real_reference=True,context_verified=True)
    assert reversal_guard['status']=='BASELINE_RETAINED'
    report={'synthetic_only':True,'real_reference_received':False,'factual_hru_calibrations':0,
            'known_parameter_recovery_pass':True,'synthetic_admission_guard_pass':True,
            'partition_compensation_guard_pass':True,'irrigation_guard_pass':True,'independent_year_reversal_guard_pass':True,
            'recovery_branch_result_SIMULATED':positive,'synthetic_guard':synthetic_guard,
            'partition_guard':partition_guard,'irrigation_guard':irrigation_guard,'reversal_guard':reversal_guard}
    write_json(output/'synthetic-qualification.json',report)
    target.to_csv(output/'synthetic-reference.csv',index=False)
    for k,f in candidates.items():f.to_csv(output/f'synthetic-response-{k[0]}-{k[1]}.csv',index=False)
    print('Five synthetic qualification scenarios passed; zero factual HRU calibrations.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    qualify(p.parse_args().output)
