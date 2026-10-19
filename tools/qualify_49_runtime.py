"""Raw historical parser replay and explicit one-year modern compatibility test.

Compatibility uses first numerical BBC diagnostic column only. This is a
declared interface experiment, never modern groundwater authority or a
scientific admission. Oracle directories are not changed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
from tools.modern_swp import render
from tools.swp_context import build_context
from tools.execute_swap_candidate import execute


def run_case(p,root,executable,database,template,library):
    i=int(p.parent.name.split('_')[1])
    raw=execute(executable,p.parent,root/'raw'/str(i),timeout=30,library_path=library)
    candidate=root/'inputs'/str(i);shutil.copytree(p.parent,candidate)
    c=build_context(database,i)
    (candidate/'swap.swp').write_text(render(template.read_bytes(),c,policy={'TEND':'1971-12-31'}))
    for bbc in candidate.glob('*.bbc'):
        out=[]
        for line in bbc.read_text().splitlines():
            a=line.split()
            if len(a)>2 and re.fullmatch(r'\d{2}-[a-zA-Z]{3}-\d{4}',a[0]):line=' '.join(a[:2])
            out.append(line)
        bbc.write_text('\n'.join(out)+'\n')
    modern=execute(executable,candidate,root/'compatibility'/str(i),timeout=60,library_path=library)
    return {'run_id':i,'raw_historical':raw,'modern_interface_compatibility':modern,
            'production_admitted':False,'bbc_policy':'FIRST_DIAGNOSTIC_COLUMN_EXPERIMENT_ONLY'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('oracles','output','database','template','executable','library'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    cases=sorted(a.oracles.glob('*/swap.swp'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda x:run_case(x,a.output,a.executable,a.database,a.template,a.library),cases))
    (a.output/'summary.json').write_text(json.dumps({'case_count':len(rows),'production_admitted':False,'cases':rows},indent=2)+'\n')
    print(json.dumps({'case_count':len(rows),'compatibility_pass':sum(x['modern_interface_compatibility']['status']=='EXECUTION_PASS' for x in rows)}))
