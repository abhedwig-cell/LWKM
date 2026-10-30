"""Bounded renderer replay with historical parameters, explicitly QA-only.

This does not qualify new grid-to-HRU parameter derivation.
"""
import argparse
import gzip
import json
from pathlib import Path
import shutil
from tools.swp_direct_render import Catalog
from tools.modern_swp import render
from tools.execute_swap_candidate import execute
from tools.work_c_report import metrics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('historical-contexts','input-root','catalog','template','executable','library-path','output','evidence'):
        p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();catalog=Catalog(a.catalog);template=a.template.read_bytes()
    if a.output.exists():raise FileExistsError('Use a fresh replay output directory')
    a.output.mkdir(parents=True)
    results=[];cases={7870,7871,7876,7929}
    with gzip.open(a.historical_contexts,'rt') as f:
        for line in f:
            c=json.loads(line)['context'];hid=int(c['run_id'])
            if hid not in cases:continue
            run=c['run'];run['TEND']='1971-12-20'
            src=a.output/f'input_{hid}'
            shutil.copytree(a.input_root/f'run_{hid:05}',src)
            (src/'swap.swp').write_text(render(template,catalog.context(run),et_policy='owner_tulip_pm'))
            dest=a.output/f'run_{hid}'
            r=execute(a.executable,src,dest,library_path=a.library_path,
                      expected_start='1971-01-01',expected_end='1971-12-20')
            if r['status']=='EXECUTION_PASS':
                r['water_balance']=metrics(dest/'result_output.csv',hid,'DIRECT_CATALOG_RENDERER_HISTORICAL_REPLAY')
            r['HRU']=hid;results.append(r)
    if {r['HRU'] for r in results}!=cases:raise ValueError('missing replay HRUs')
    report=dict(scope='HISTORICAL_PARAMETER_REPLAY_OF_NEW_CSV_CATALOG_RENDERER_NOT_NEW_GRID_DERIVATION',
                production_admitted=False,runs=results)
    a.evidence.parent.mkdir(parents=True,exist_ok=True)
    a.evidence.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if all(r['status']=='EXECUTION_PASS' and r['water_balance']['serialized_water_balance_pass'] for r in results) else 1


if __name__=='__main__':raise SystemExit(main())
