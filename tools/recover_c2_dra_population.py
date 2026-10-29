"""Recover 10213 exact C2 DRA files and serialize 29 full-record approximations.

Existing C2 bytes stay unchanged. The 29 are research candidates with explicit
fit errors, not automatically admitted hydrological equivalents.
"""
import argparse,gzip,json,re
from pathlib import Path
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json
from tools.modern_swp import render
from tools.swp_full_oracle import parse_named_table
from tools.swp_template_adapter import TABLE_HEADERS
from tools.w07_build_29_dra import from_record
from tools.w07_autofive_full_records import solve
from tools.dra_level_compression import to_render_level
from tools.generate_dra import render_dra_explicit


def records(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:
        for line in f:yield json.loads(line)


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('immutable output differs: '+str(path))
    else:
        tmp=path.with_suffix('.partial');tmp.write_bytes(data);tmp.replace(path)


def recover(checkpoints,existing,contexts,template,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    (output/'manifest.json').unlink(missing_ok=True)
    context={int(r['run_id']):r['context'] for r in records(contexts)}
    checkpoint={int(r['hru']):r for r in records(checkpoints)}
    rows={};source=template.read_bytes()
    for r in records(existing):
        h=int(r['hru']);data=r['text'].encode()
        import hashlib
        if hashlib.sha256(data).hexdigest()!=r['sha256']:raise ValueError('C2 DRA hash mismatch')
        if h in rows:raise ValueError('duplicate archived DRA')
        p=output/'dra'/f'{h}.dra';save(p,data)
        rows[h]=dict(hru=h,status='C2_BYTE_IDENTICAL',path=str(p),sha256=sha256(p))
    for h,c in sorted(checkpoint.items()):
        if h in rows:continue
        if c['status']!='BLOCKED' or not c.get('retained_physical'):
            raise ValueError('missing complete checkpoint: '+str(h))
        swp=render(source,context[h],et_policy='owner_tulip_pm')
        swp=re.sub(r'(?m)^(\s*TEND\s*=)\s*\S+',r'\1 1971-12-20',swp)
        n=len(parse_named_table(swp,TABLE_HEADERS['TABLE_SOILHYDRFUNC']))
        levels,audit=solve([from_record(s) for s in c['retained_physical']])
        dra=render_dra_explicit([to_render_level(s) for s in levels],n,1971,1972,0.)
        p=output/'dra'/f'{h}.dra';save(p,dra.encode())
        save(output/'swp'/f'run_{h:05d}'/'swap.swp',swp.encode())
        rows[h]=dict(hru=h,status='APPROXIMATE_DRA_NOT_HYDROLOGICALLY_ADMITTED',
            path=str(p),sha256=sha256(p),soil_horizons=n,represented_levels=len(levels),audit=audit)
    if set(rows)!=set(checkpoint) or set(checkpoint)!=set(context):
        raise ValueError('population identity mismatch')
    report=dict(schema_version=1,status='COMPLETE_C2_DRA_CANDIDATE_POPULATION',production_admitted=False,
        source_sha256={str(p):sha256(p) for p in [checkpoints,existing,contexts,template]},
        hrus=len(rows),byte_identical=sum(r['status']=='C2_BYTE_IDENTICAL' for r in rows.values()),
        approximated=sum(r['status']!='C2_BYTE_IDENTICAL' for r in rows.values()),
        render_years=[1971,1972],complete_historical_stage_coverage=False,rows=[rows[h] for h in sorted(rows)],
        limitations=['Recovered original C2 period only; no historical stage extrapolation',
                     '29 actual files from full real-source checkpoints, not 29 SWAP executions',
                     'No scientific error envelope or modern BBC/MET forcing admission'])
    atomic_json(output/'manifest.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['checkpoints','existing','contexts','template','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();r=recover(a.checkpoints,a.existing,a.contexts,a.template,a.output)
    print(json.dumps({k:r[k] for k in ['hrus','byte_identical','approximated','status']}))
