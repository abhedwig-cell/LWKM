"""Generic HRU package builder from an explicit consumer-bound input catalogue.

The catalogue is the interface to the server workstream. Missing forcing is
reported per HRU, never borrowed from a neighbouring or historical case. This
builder emits candidates; it cannot self-admit a scientific transformation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
from tools.modern_swp import render
from tools.swp_context import build_context
from tools.assemble_swap_package import assemble,sha256
from tools.package_preflight import validate
from tools.run_dra_protected_population import atomic_json,canonical


def build(database,template,catalogue,output,*,allow_research_inputs=False):
    data=json.loads(catalogue.read_text())
    if data.get('schema_version')!=1 or not data.get('profile_id'):
        raise ValueError('invalid package catalogue')
    if data.get('et_policy') not in ('datamodel','penman_monteith'):
        raise ValueError('catalogue must explicitly select an ET policy')
    bound=data.get('runs',{})
    with sqlite3.connect(database) as c:ids=[int(x[0]) for x in c.execute('select run_id from Runs order by run_id')]
    if set(map(int,bound))-set(ids):raise ValueError('catalogue has unknown HRU IDs')
    if data.get('expected_population')!=len(ids):raise ValueError('population count mismatch')
    output.mkdir(parents=True,exist_ok=True);results=[]
    for hid in ids:
        record={'run_id':hid,'production_admitted':False}
        try:
            entry=bound.get(str(hid))
            if entry is None:raise ValueError('EXTERNAL_INPUT_UNBOUND: no HRU-specific forcing catalogue')
            ctx=build_context(database,hid)
            with tempfile.TemporaryDirectory(prefix='lwkm-catalogue-') as td:
                stage=Path(td);assets={}
                for name,meta in entry['assets'].items():
                    if Path(name).name!=name or '/' in name or '\\' in name or ':' in name or name=='swap.swp':
                        raise ValueError('unsafe/reserved catalogue asset name')
                    for key in ('path','sha256','logical_id','qualification_status','semantic_contract','evidence_refs'):
                        if not meta.get(key):raise ValueError('incomplete source binding: '+name)
                    if meta['qualification_status']!='PRODUCTION_ADMITTED' and not allow_research_inputs:
                        raise ValueError('input not production admitted: '+name)
                    src=Path(meta['path'])
                    if sha256(src)!=meta['sha256']:raise ValueError('source hash mismatch: '+name)
                    shutil.copyfile(src,stage/name)
                    assets[name]={'path':str(stage/name),'sha256':meta['sha256'],
                                  'qualification_id':meta['logical_id']}
                (stage/'swap.swp').write_text(render(template.read_bytes(),ctx,
                    policy={'TSTART':data['start'],'TEND':data['end']},et_policy=data['et_policy']))
                assets['swap.swp']={'path':str(stage/'swap.swp'),'sha256':sha256(stage/'swap.swp'),
                                    'qualification_id':'EXPLICIT_RENDER_CANDIDATE_NOT_ADMITTED'}
                preflight=validate(stage)
                if set(assets)!=set(preflight['files']):raise ValueError('catalogue has undeclared/unconsumed assets')
                identity={'profile':data['profile_id'],'et_policy':data['et_policy'],
                          'hashes':{n:m['sha256'] for n,m in assets.items()},
                          'source_bindings':entry,
                          'research_inputs_explicitly_allowed':allow_research_inputs,
                          'builder_sha256':sha256(Path(__file__)),
                          'preflight_sha256':sha256(Path(__file__).with_name('package_preflight.py'))}
                digest=hashlib.sha256(canonical(identity).encode()).hexdigest()
                root=output/'objects'/digest;target=root/f'run_{hid:05d}'
                reused=target.exists()
                if reused:
                    manifest=json.loads((target/'manifest.json').read_text())
                    if {n:m['sha256'] for n,m in manifest['assets'].items()}!=identity['hashes']:
                        raise ValueError('cached manifest changed')
                    if any(sha256(target/n)!=m['sha256'] for n,m in assets.items()):raise ValueError('cached asset changed')
                    validate(target)
                else:
                    assemble(hid,assets,root,profile_id=data['profile_id'],code_commit='sha256:'+identity['builder_sha256'],
                        file_keys=('METFIL',),required_assets=preflight['files'])
                    atomic_json(target/'input-bindings.json',{'catalogue_sha256':sha256(catalogue),'entry':entry,'identity':identity})
                    atomic_json(target/'preflight.json',preflight)
                record.update(status='COMPLETE_CANDIDATE_PACKAGE',package=str(target.resolve()),
                    fingerprint=digest,reused=reused,manifest_sha256=sha256(target/'manifest.json'))
        except (ValueError,KeyError,FileNotFoundError) as exc:record.update(status='BLOCKED',error=str(exc))
        results.append(record)
    summary={'schema_version':1,'population':len(ids),'complete_packages':sum(r['status']=='COMPLETE_CANDIDATE_PACKAGE' for r in results),
             'reused_packages':sum(r.get('reused',False) for r in results),'production_admitted':False,'runs':results}
    atomic_json(output/'build-status.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('database','template','catalogue','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--allow-research-inputs',action='store_true')
    a=p.parse_args();r=build(a.database,a.template,a.catalogue,a.output,allow_research_inputs=a.allow_research_inputs)
    print(json.dumps({k:v for k,v in r.items() if k!='runs'}))
