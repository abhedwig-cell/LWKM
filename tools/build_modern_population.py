"""Build every typed SWP, retain unresolved package status and 49-case differences."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from tools.modern_swp import render,PROFILE_ID
from tools.swp_context import build_context
from tools.swp_full_oracle import compare_text


def build(database,template,output,oracles):
    output.mkdir(parents=True,exist_ok=True)
    raw=template.read_bytes()
    with sqlite3.connect(database) as con:
        ids=[r[0] for r in con.execute('select run_id from Runs order by run_id')]
    historical={int(p.parent.name.split('_')[1]):p for p in oracles.glob('*/swap.swp')}
    rows=[];reg=[];start=time.monotonic();reused=0
    for i in ids:
        try:
            s=render(raw,build_context(database,i))
            p=output/f'run_{i:05d}'/'swap.swp';p.parent.mkdir(exist_ok=True)
            encoded=s.encode('utf-8')
            if p.exists() and p.read_bytes()==encoded:
                reused+=1
            else:
                tmp=p.with_suffix('.swp.partial');tmp.write_bytes(encoded);tmp.replace(p)
            rec={'run_id':i,'swp_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                 'status':'SWP_GENERATED_PACKAGE_INCOMPLETE',
                 'missing_qualification':['DRA','MET','BBC_IF_ENABLED','CROP_ASSETS'],
                 'production_admitted':False}
            rows.append(rec)
            (p.parent/'candidate.json').write_text(json.dumps(rec,indent=2)+'\n')
            if i in historical:
                try:
                    diffs=compare_text(historical[i].read_text(),s)
                    reg.append({'run_id':i,'status':'PASS' if not diffs else 'DIFFERENCES_NOT_ADMITTED',
                                'differences':[{'path':d.path,'expected':d.expected,'actual':d.actual} for d in diffs]})
                except Exception as e:reg.append({'run_id':i,'status':'COMPARATOR_FAIL','error':str(e)})
        except Exception as e:rows.append({'run_id':i,'status':'FAILED','error':str(e)})
    result={'schema_version':1,'profile':PROFILE_ID,'run_count':len(ids),
            'elapsed_seconds':time.monotonic()-start,'unchanged_swp_reused':reused,
            'production_admitted':False,'rows':rows}
    (output/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'regression-49.json').write_text(json.dumps(reg,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('database','template','output','oracles'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();r=build(a.database,a.template,a.output,a.oracles)
    print(json.dumps({'run_count':r['run_count'],'failed':sum(x['status']=='FAILED' for x in r['rows'])}))
