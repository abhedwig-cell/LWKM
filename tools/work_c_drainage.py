"""Focused, restartable seven-system population qualification, one selected period.

Reuses established raster aggregation and protected physical compression. No
parameter imputation or resistance clipping. Each HRU checkpoint is independent
and fingerprinted; previous numerical failures are cached as well as passes.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from tools.diagnose_dra_10242 import (_extract_bundle,_read_relation_context,
    _prepare_static_members,_h1_stage_files,_find_one,_build_h1_level_matrix,
    _build_physical_policy)
from tools.dra_protected_compression import select_protected_candidate
from tools.dra_level_compression import to_render_level
from tools.prepare_dra_positive_median_dqsat import prepare
from tools.compare_dqsat_authority import read_ascii_grid
from tools.run_dra_protected_population import atomic_json,canonical
from tools.assemble_swap_package import sha256

VERSION="work-c-primary-drainage-v2-interface-aware"


def run(relation,schema,dqsat,h1,remaining,output,start,end):
    output.mkdir(parents=True,exist_ok=True)
    identity={p.name:sha256(p) for p in (relation,schema,dqsat,h1,remaining)}
    expected={"LHM433_H1_MVG_Q4.zip":"3c27cb509dd6d60f5ae8b434fd1ba0f4aca10d81a1b1815b077c5b52a818abfa",
              "LHM433_DRA_REMAINING_Q4.zip":"6de1ccbdb646f809523fd3cbedd5143bc2a73470a1f48d0b04b13be93fa7a3a4"}
    for p in (h1,remaining):
        if sha256(p)!=expected[p.name]:raise ValueError("source bundle identity mismatch")
    source_identity={"algorithm":VERSION,"inputs":identity,"start":start,"end":end}
    # Include implementation dependencies, so code changes cannot reuse stale results.
    deps=[Path(__file__),*(Path(__file__).with_name(n) for n in (
        'diagnose_dra_10242.py','generate_dra.py','dra_level_compression.py',
        'dra_protected_compression.py','prepare_dra_positive_median_dqsat.py',
        'derive_representative_dqsat.py','compare_dqsat_authority.py','dqsat_policy.py','idf_reader.py'))]
    source_identity['code']={p.name:sha256(p) for p in deps}
    fingerprint=hashlib.sha256(canonical(source_identity).encode()).hexdigest()
    old=output/'identity.json'
    if old.exists() and json.loads(old.read_text())['fingerprint']!=fingerprint:
        raise ValueError("different source/code/period requires a new output directory")
    atomic_json(old,{**source_identity,'fingerprint':fingerprint})
    checkpoint=output/'hrus';checkpoint.mkdir(exist_ok=True)
    rel=pd.read_csv(relation,low_memory=False);sch=pd.read_csv(schema,low_memory=False)
    ids=sorted(int(x) for x in sch.HRU)
    if len(ids)!=len(set(ids)):raise ValueError('duplicate HRU schema')
    existing={int(p.stem) for p in checkpoint.glob('*.json')}
    todo=set(ids)-existing
    begin=time.monotonic()
    if todo:
        cache=output/'prepared';cache.mkdir(exist_ok=True)
        if not (cache/'members.pkl').exists():
            for z in (h1,remaining):
                if not (cache/z.stem).exists():_extract_bundle(z,cache)
            membership,coords,_=_read_relation_context(relation)
            members=_prepare_static_members(membership,coords,cache/h1.stem,cache/remaining.stem)
            stages=_h1_stage_files(cache/h1.stem,start,end)
            dates,matrix,failures=_build_h1_level_matrix(members,stages,
                reference_idf=_find_one(cache/h1.stem,'COND_HL1_250.IDF'))
            med=prepare(sch,rel,read_ascii_grid(dqsat))
            # Persist a precise source-exception table, including cell coordinates.
            bad=members[(members.H1_cdr>0)&members.H1_inf.isna()]
            bad.to_csv(output/'missing_h1_factors.csv',index=False)
            members.to_pickle(cache/'members.pkl');np.save(cache/'matrix.npy',matrix)
            atomic_json(cache/'stages.json',{'dates':dates,'failures':failures})
            med.to_csv(cache/'dqsat.csv',index=False)
            atomic_json(cache/'cache-hashes.json',{p.name:sha256(p) for p in cache.iterdir() if p.is_file()})
        hashes=json.loads((cache/'cache-hashes.json').read_text())
        if any(sha256(cache/n)!=h for n,h in hashes.items()):raise ValueError('prepared cache changed')
        members=pd.read_pickle(cache/'members.pkl');matrix=np.load(cache/'matrix.npy')
        stages=json.loads((cache/'stages.json').read_text());failures={int(k):v for k,v in stages['failures'].items()}
        med=pd.read_csv(cache/'dqsat.csv');dq=dict(zip(med.hru,med.representative_dqsat))
        if set(members.hru.unique())!=set(ids):raise ValueError('schema/membership HRU domain mismatch')
        for count,(hid,group) in enumerate(members.groupby('hru',sort=True),1):
            hid=int(hid)
            if hid not in todo:continue
            rec={'hru':hid,'fingerprint':fingerprint,'production_admitted':False}
            try:
                if hid in failures:raise ValueError(failures[hid])
                physical=_build_physical_policy(group,float(dq[hid]),bottom_policy='lhm_mean',
                    stage_dates=stages['dates'],h1_depths=matrix[hid])
                levels,audit=select_protected_candidate(physical,require_swap_interface=True)
                rec['physical']=[asdict(x) for x in physical]
                rec['audit']=audit
                rec['levels']=[to_render_level(x) for x in levels]
                rec['status']='DRA_INTERFACE_CANDIDATE'
            except (ValueError,AssertionError) as e:
                rec.update(status='BLOCKED',error=str(e))
            atomic_json(checkpoint/f'{hid}.json',rec)
            if count%100==0:
                atomic_json(output/'progress.json',{'completed':len(list(checkpoint.glob('*.json'))),'total':len(ids)})
                print(f'checkpoint {count}/{len(ids)}',flush=True)
    rows=[json.loads((checkpoint/f'{i}.json').read_text()) for i in ids]
    if any(r['fingerprint']!=fingerprint for r in rows):raise ValueError('stale HRU checkpoint')
    report={'status':'CANDIDATES_NOT_PRODUCTION_ADMITTED','hru_count':len(ids),
            'candidate_count':sum(r['status']=='DRA_INTERFACE_CANDIDATE' for r in rows),
            'blocked_count':sum(r['status']=='BLOCKED' for r in rows),
            'reused_checkpoints':len(ids)-len(todo),'elapsed_seconds':time.monotonic()-begin,
            'start':start,'end':end,'fingerprint':fingerprint,'production_admitted':False}
    pd.DataFrame([{k:r.get(k) for k in ('hru','status','error')} for r in rows]).to_csv(output/'status.csv',index=False)
    atomic_json(output/'summary.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('relation','schema','dqsat','h1','remaining','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--start',default='1971-01-01');p.add_argument('--end',default='1972-01-01')
    a=p.parse_args();print(json.dumps(run(a.relation,a.schema,a.dqsat,a.h1,a.remaining,a.output,a.start,a.end)))
