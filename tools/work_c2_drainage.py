"""Replay owner rules from hash-verified source preparation; immutable HRU checkpoints."""
import argparse
from dataclasses import asdict
import hashlib,json,time
from pathlib import Path
import numpy as np
import pandas as pd
from tools.work_c_drainage import sha256,canonical,atomic_json
from tools.diagnose_dra_10242 import _build_physical_policy
from tools.dra_owner_policy import apply_owner_policy,POLICY_ID
from tools.dra_protected_compression import select_protected_candidate
from tools.dra_level_compression import to_render_level


def run(parent,output):
    output.mkdir(parents=True,exist_ok=True)
    identity=json.loads((parent/'identity.json').read_text());cache=parent/'prepared'
    hashes=json.loads((cache/'cache-hashes.json').read_text())
    for n,h in hashes.items():
        if sha256(cache/n)!=h:raise ValueError('source preparation cache changed: '+n)
    names=['work_c2_drainage.py','dra_owner_policy.py','diagnose_dra_10242.py',
           'dra_level_compression.py','dra_protected_compression.py','generate_dra.py']
    binding=dict(policy=POLICY_ID,parent_identity_sha256=sha256(parent/'identity.json'),
        prepared_hashes=hashes,code={n:sha256(Path(__file__).with_name(n)) for n in names})
    fingerprint=hashlib.sha256(canonical(binding).encode()).hexdigest()
    old=output/'identity.json'
    if old.exists() and json.loads(old.read_text())['fingerprint']!=fingerprint:raise ValueError('new version requires new directory')
    atomic_json(old,dict(binding=binding,fingerprint=fingerprint,original_sources=identity))
    members=pd.read_pickle(cache/'members.pkl');matrix=np.load(cache/'matrix.npy')
    stages=json.loads((cache/'stages.json').read_text());med=pd.read_csv(cache/'dqsat.csv');dq=dict(zip(med.hru,med.representative_dqsat))
    bad=(members.H1_cdr>0)&members.H1_inf.isna()
    cells=members.loc[bad,['hru','svat','x','y','row','col','H1_cdr']].copy()
    cells['interpretation']='NO_INFILTRATION_AT_THIS_CELL';cells['effective_H1_inf']=0.
    cells.to_csv(output/'h1-cell-decisions.csv',index=False)
    members=members.copy();members.loc[bad,'H1_inf']=0.
    directory=output/'hrus';directory.mkdir(exist_ok=True);rows=[];reused=0;t=time.monotonic()
    for hid,group in members.groupby('hru',sort=True):
        hid=int(hid);path=directory/f'{hid}.json'
        if path.exists():
            rec=json.loads(path.read_text())
            if rec['fingerprint']!=fingerprint:raise ValueError('stale checkpoint')
            reused+=1
        else:
            rec=dict(hru=hid,fingerprint=fingerprint,production_admitted=False)
            try:
                if str(hid) in stages['failures']:raise ValueError(stages['failures'][str(hid)])
                physical=_build_physical_policy(group,float(dq[hid]),bottom_policy='lhm_mean',stage_dates=stages['dates'],h1_depths=matrix[hid])
                rec['physical']=[asdict(x) for x in physical]
                kept,decision=apply_owner_policy(physical);rec['owner_decision']=decision
                rec['retained_physical']=[asdict(x) for x in kept]
                levels,audit=select_protected_candidate(kept,require_swap_interface=True)
                rec.update(audit=audit,levels=[to_render_level(x) for x in levels],status='DRA_INTERFACE_CANDIDATE',
                    swdra=1 if levels else 0)
            except (ValueError,AssertionError) as exc:rec.update(status='BLOCKED',error=str(exc))
            atomic_json(path,rec)
        rows.append(rec)
        if len(rows)%1000==0:print(len(rows),flush=True)
    summary=dict(policy=POLICY_ID,population=len(rows),candidates=sum(r['status']=='DRA_INTERFACE_CANDIDATE' for r in rows),
        blocked=sum(r['status']=='BLOCKED' for r in rows),reused_checkpoints=reused,elapsed_seconds=time.monotonic()-t,
        h1_missing_cells=len(cells),h1_affected_hrus=int(cells.hru.nunique()),production_admitted=False)
    events=[e for r in rows for e in r.get('owner_decision',{}).get('events',[])]
    summary['omitted_physical_contributions']=sum(e['action']=='OMIT_DRAINAGE_SYSTEM' for e in events)
    summary['disabled_infiltration_contributions']=sum(e['action']=='DISABLE_INFILTRATION' for e in events)
    summary['empty_drainage_hrus']=sum(r.get('swdra')==0 for r in rows)
    pd.DataFrame([{k:r.get(k) for k in ['hru','status','error','swdra']} for r in rows]).to_csv(output/'status.csv',index=False)
    atomic_json(output/'summary.json',summary);return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.parent,a.output)))
