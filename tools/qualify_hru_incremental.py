"""Actual population cache experiment with one controlled execution-context edit."""
import argparse
import gzip
import json
from pathlib import Path
from tools.hru_context_cache import update
from tools.hru_source_chain import sha,atomic_json,fingerprint
from tools.modern_swp import render


def run(archive,template,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    db=output/'cache.sqlite'
    if db.exists():raise ValueError('Use a fresh experiment directory')
    raw=Path(template).read_bytes()
    identity=fingerprint(dict(et_policy='owner_tulip_pm',code_and_template={str(p):sha(p) for p in [Path(template),Path('tools/modern_swp.py'),Path('tools/swp_template_adapter.py'),Path('tools/swp_renderer.py'),Path('tools/swp_context.py')]}))
    calls=[]
    def renderer(ctx):calls.append(1);return render(raw,ctx,et_policy='owner_tulip_pm')
    def records(change=False):
        with gzip.open(archive,'rt') as f:
            for i,line in enumerate(f):
                r=json.loads(line)
                if change and i==0:r['context']['GWLI']=float(r['context']['GWLI'])-1
                yield r
    initial=update(records(),db,identity,renderer,import_verified=True)
    unchanged=update(records(),db,identity,renderer)
    if calls:raise ValueError('Unchanged renderer was called')
    changed=update(records(True),db,identity,renderer)
    if len(calls)!=1 or changed['written']!=1:raise ValueError('Unexpected regeneration count')
    before={r['run_id']:r['swp_sha256'] for r in initial['rows']}
    differences=[r['run_id'] for r in changed['rows'] if before[r['run_id']]!=r['swp_sha256']]
    summary=dict(input_archive_sha256=sha(archive),renderer_identity=identity,
        population=initial['count'],initial_imported=initial['written'],unchanged_reused=unchanged['reused'],
        modified_contexts=1,changed_written=changed['written'],changed_reused=changed['reused'],
        actual_renderer_calls=len(calls),different_swp_ids=differences,
        limitation='Context/SWP invalidation is executed. Upstream cluster dependency closure is separately tested; no partial R-cluster equivalence is claimed.',production_admitted=False)
    for name,value in [('initial',initial),('unchanged',unchanged),('changed',changed)]:
        with gzip.GzipFile(filename='',fileobj=(output/(name+'.json.gz')).open('wb'),mode='wb',mtime=0) as f:f.write(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
    atomic_json(output/'summary.json',summary);print(json.dumps(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['archive','template','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.archive,a.template,a.output)
