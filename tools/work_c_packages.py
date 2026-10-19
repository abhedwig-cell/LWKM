"""Content-addressed research packages from real 49-case forcing and modern contexts.

No modern forcing is invented. BBC projection and period intersection are
explicit research policies. Production paths must use separately admitted
daily inputs instead. Modern drainage failures never fall back to oracle DRA.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
import pandas as pd
from tools.modern_swp import render
from tools.swp_context import build_context
from tools.package_preflight import validate,dated_table,scalar
from tools.assemble_swap_package import assemble,sha256
from tools.generate_dra import render_dra_explicit
from tools.run_dra_protected_population import canonical,atomic_json
from tools.execute_swap_candidate import execute

VERSION='WORK_C_PM_RESEARCH_V1'


def project_bbc(source):
    lines=[];removed=0
    for line in source.splitlines():
        tokens=line.split()
        if tokens and re.fullmatch(r'\d{1,2}-[a-zA-Z]{3}-\d{4}',tokens[0]):
            if len(tokens)!=4:raise ValueError('expected three-column historical BBC diagnostic')
            line=' '.join(tokens[:2]);removed+=2
        lines.append(line)
    out='\n'.join(lines)+'\n'
    dates,_=dated_table(out,'DATE2 QBOT2')
    return out,dates,removed


def build_one(run_id,oracle,database,template,output,drainage,*,mode='oracle',end='1971-12-31',
              start='1971-01-01',et_policy='penman_monteith'):
    context=build_context(database,run_id)
    bbc,days,removed=project_bbc((oracle/f'{run_id}.bbc').read_text())
    # Explicit source intersection: never append persistence values to bridge a gap.
    actual_start=max(pd.Timestamp(start).date(),days[0])
    actual_end=min(pd.Timestamp(end).date(),days[-1])
    if actual_end<actual_start:raise ValueError('empty supported forcing period')
    with tempfile.TemporaryDirectory(prefix='lwkm-work-c-') as td:
        staging=Path(td)
        for p in oracle.iterdir():
            if p.is_file() and p.suffix.lower() in ('.crp','.co2','.met','.dra'):
                (staging/p.name).write_bytes(p.read_bytes())
        (staging/f'{run_id}.bbc').write_text(bbc)
        render_policy={'TSTART':actual_start.isoformat(),'TEND':actual_end.isoformat()}
        if mode=='modern':
            record=json.loads((drainage/'hrus'/f'{run_id}.json').read_text())
            if record['status']!='DRA_INTERFACE_CANDIDATE':raise ValueError(record.get('error','blocked drainage'))
            if record['levels']:
                dra=render_dra_explicit(record['levels'],len(context['TABLE_SOILHYDRFUNC']),
                    actual_start.year,actual_end.year+1,0.0)
                (staging/f'{run_id}.dra').write_text(dra)
            else:
                render_policy.update(SWDRA=0,SWITCH_SWDRA_OPTION_1=False)
        (staging/'swap.swp').write_text(render(template.read_bytes(),context,
            policy=render_policy,et_policy=et_policy))
        preflight=validate(staging)
        assets={name:{'path':str(staging/name),'sha256':sha256(staging/name),
                      'qualification_id':'RESEARCH_INPUT_NOT_PRODUCTION_ADMITTED'} for name in preflight['files']}
        provenance={'profile':VERSION,'drainage_mode':mode,'et_policy':et_policy,
                    'requested_start':start,'requested_end':end,
                    'actual_start':actual_start.isoformat(),'actual_end':actual_end.isoformat(),
                    'period_policy':'EXPLICIT_SOURCE_INTERSECTION_NO_EXTRAPOLATION',
                    'bbc_policy':'FIRST_DIAGNOSTIC_COLUMN_RESEARCH_ONLY','removed_diagnostic_values':removed,
                    'original_workbook_swet':context['SWETR'],
                    'original_bbc_sha256':sha256(oracle/f'{run_id}.bbc'),
                    'template_sha256':sha256(template),
                    'input_hashes':{n:a['sha256'] for n,a in assets.items()},
                    'code_hashes':{n:sha256(Path(__file__).with_name(n)) for n in (
                        'work_c_packages.py','package_preflight.py','modern_swp.py',
                        'generate_dra.py','assemble_swap_package.py','swp_context.py')}}
        if mode=='modern':provenance['drainage_checkpoint_sha256']=sha256(drainage/'hrus'/f'{run_id}.json')
        fingerprint=hashlib.sha256(canonical(provenance).encode()).hexdigest()
        target=output/'objects'/fingerprint/f'run_{run_id:05d}'
        reused=target.exists()
        if reused:
            manifest=json.loads((target/'manifest.json').read_text())
            if {n:a['sha256'] for n,a in manifest['assets'].items()}!=provenance['input_hashes']:
                raise ValueError('cached package manifest mismatch')
            if any(sha256(target/n)!=a['sha256'] for n,a in manifest['assets'].items()):
                raise ValueError('cached package bytes changed')
            validate(target)
        else:
            assemble(run_id,assets,target.parent,profile_id=VERSION,
                code_commit='sha256:'+hashlib.sha256(canonical(provenance['code_hashes']).encode()).hexdigest(),
                required_assets=preflight['files'],file_keys=('METFIL',),required_file_keys=('METFIL',))
            atomic_json(target/'provenance.json',provenance)
            atomic_json(target/'preflight.json',preflight)
        return {'run_id':run_id,'status':'COMPLETE_RESEARCH_PACKAGE','mode':mode,
                'package':str(target.resolve()),'fingerprint':fingerprint,
                'manifest_sha256':sha256(target/'manifest.json'),'reused':reused,
                'days':(actual_end-actual_start).days+1,'production_admitted':False}


def build(oracles,database,template,output,drainage,*,mode='oracle',end='1971-12-31',
          start='1971-01-01',run_models=False,executable=None,library=None):
    output.mkdir(parents=True,exist_ok=True);begin=time.monotonic()
    rows=[]
    for swp in sorted(oracles.glob('*/swap.swp')):
        hid=int(swp.parent.name.split('_')[1])
        try:r=build_one(hid,swp.parent,database,template,output,drainage,mode=mode,start=start,end=end)
        except (ValueError,FileNotFoundError,KeyError) as e:
            r={'run_id':hid,'status':'BLOCKED','mode':mode,'error':str(e),'production_admitted':False}
        rows.append(r)
    if run_models:
        def model(r):
            if r['status']!='COMPLETE_RESEARCH_PACKAGE':return
            engine={'package':r['fingerprint'],'executable':sha256(executable),
                    'runner':sha256(Path(__file__).with_name('execute_swap_candidate.py')),
                    'libimf':sha256(library/'libimf.so')}
            execution_key=hashlib.sha256(canonical(engine).encode()).hexdigest()
            destination=output/'executions'/execution_key
            if destination.exists():
                prior=json.loads((destination/'execution.json').read_text())
                if prior['input_sha256']!={n:sha256(Path(r['package'])/n) for n in prior['input_sha256']}:
                    raise ValueError('execution cache input mismatch')
                if any(not (destination/n).is_file() or sha256(destination/n)!=h for n,h in prior['output_sha256'].items()):
                    raise ValueError('execution cache output mismatch')
                r['execution']=prior;r['execution_reused']=True
            else:
                period=json.loads((Path(r['package'])/'preflight.json').read_text())
                r['execution']=execute(executable,Path(r['package']),destination,timeout=120,library_path=library,
                    expected_start=period['start'],expected_end=period['end'])
                r['execution_reused']=False
            r['execution_directory']=str(destination.resolve())
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(model,rows))
    report={'profile':VERSION,'mode':mode,'run_count':len(rows),
            'complete_packages':sum(r['status']=='COMPLETE_RESEARCH_PACKAGE' for r in rows),
            'reused_packages':sum(r.get('reused',False) for r in rows),
            'execution_pass':sum(r.get('execution',{}).get('status')=='EXECUTION_PASS' for r in rows),
            'elapsed_seconds':time.monotonic()-begin,'production_admitted':False,'runs':rows}
    atomic_json(output/'summary.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('oracles','database','template','output','drainage'):p.add_argument('--'+n,type=Path,required=True)
    for n in ('executable','library'):p.add_argument('--'+n,type=Path)
    p.add_argument('--mode',choices=['oracle','modern'],default='oracle')
    p.add_argument('--start',default='1971-01-01');p.add_argument('--end',default='1971-12-31')
    p.add_argument('--run',action='store_true');p.add_argument('--research-oracle',action='store_true',required=True)
    a=p.parse_args();r=build(a.oracles,a.database,a.template,a.output,a.drainage,mode=a.mode,
        start=a.start,end=a.end,run_models=a.run,executable=a.executable,library=a.library)
    print(json.dumps({k:v for k,v in r.items() if k!='runs'}))
