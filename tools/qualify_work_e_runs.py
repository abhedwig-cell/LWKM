"""Rebuild four complete source-bound C2 packages and run real SWAP 4.3.1.

Historical research forcing is retained exactly. This is not a modern national
forcing qualification. Caller supplies the original engine and Intel runtime.
"""
import argparse,gzip,hashlib,json,zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tools.modern_swp import render
from tools.package_preflight import validate
from tools.execute_swap_candidate import execute
from tools.work_c_report import metrics
from tools.run_dra_protected_population import atomic_json
from tools.assemble_swap_package import sha256

HRUS=(7870,7871,7876,7929)


def qualify(repo,executable,library,output):
    repo,output=Path(repo),Path(output);output.mkdir(parents=True,exist_ok=True)
    cat=repo/'docs/evidence/2026-10-19-work-c2/research-input-catalogue.json'
    catalogue=json.loads(cat.read_text())
    wanted={a['sha256'] for h in HRUS for a in catalogue['runs'][str(h)]['assets'].values()}
    found={}
    archives=[]
    for archive in sorted((repo/'docs/evidence').rglob('*.zip')):
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                key=Path(info.filename).name
                if key in wanted:
                    data=z.read(info)
                    if hashlib.sha256(data).hexdigest()!=key:raise ValueError('archived asset corruption')
                    found[key]=data;archives.append(archive)
    if wanted-set(found):raise ValueError('missing source-bound archived assets')
    context_path=repo/'docs/evidence/2026-10-19-work-b/interfaces/HRU_CONTEXT_10242.jsonl.gz'
    with gzip.open(context_path,'rt') as f:
        contexts={r['run_id']:r['context'] for r in map(json.loads,f) if r['run_id'] in HRUS}
    template=repo/'tests/fixtures/d1/wwl.swp'
    for h in HRUS:
        dest=output/'inputs'/f'run_{h:05d}';dest.mkdir(parents=True,exist_ok=False)
        for name,asset in catalogue['runs'][str(h)]['assets'].items():(dest/name).write_bytes(found[asset['sha256']])
        (dest/'swap.swp').write_text(render(template.read_bytes(),contexts[h],
            policy=dict(TSTART='1971-01-01',TEND='1971-12-20'),et_policy='owner_tulip_pm'))
        validate(dest)
    def case(h):
        source=output/'inputs'/f'run_{h:05d}';dest=output/'runs'/str(h)
        r=execute(executable,source,dest,library_path=library,
                  expected_start='1971-01-01',expected_end='1971-12-20')
        r['hru']=h
        if r['status']=='EXECUTION_PASS':r['water_balance']=metrics(dest/'result_output.csv',h,'WORK_E_SOURCE_BOUND_C2_REPLAY')
        return r
    rows=list(ThreadPoolExecutor(4).map(case,HRUS))
    report=dict(status='HISTORICAL_C2_END_TO_END_REPLAY',production_admitted=False,hrus=len(rows),
        executed_pass=sum(r['status']=='EXECUTION_PASS' for r in rows),
        water_balance_pass=sum(r.get('water_balance',{}).get('serialized_water_balance_pass',False) for r in rows),
        source_sha256={str(p):sha256(p) for p in [cat,context_path,template,*sorted(set(archives))]},
        runtime_sha256={p.name:sha256(p) for p in Path(library).glob('*.so*') if p.is_file()},
        limitations=['Historical C2 BBC/MET/CRP and modern source-bound SWP/DRA, no new daily server forcing',
                     '1971-01-01 through 1971-12-20; no forcing extrapolation',
                     'Four existing HRUs, not 29 approximation cases or 10242 modern model runs'],runs=rows)
    atomic_json(output/'summary.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['repo','executable','library','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();r=qualify(a.repo,a.executable,a.library,a.output)
    print(json.dumps({k:r[k] for k in ['hrus','executed_pass','water_balance_pass']}))
