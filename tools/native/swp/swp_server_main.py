"""Offline Windows entry point for 10,242 SWP generation using established LWKM authority."""
import argparse, json, hashlib, sqlite3, sys
from pathlib import Path
from tools.modern_swp import render, SOURCE_SHA256, PROFILE_ID
from tools.swp_context import build_context

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--database',required=True,type=Path)
    p.add_argument('--template',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--et-policy',default='datamodel',choices=['datamodel','penman_monteith','owner_tulip_pm'])
    p.add_argument('--expected',type=int,default=None,help='Optional release-specific expected HRU count')
    args=p.parse_args()
    if not args.database.is_file() or not args.template.is_file():
        raise SystemExit("Missing SQLite database or SWP template")
    raw=args.template.read_bytes()
    fingerprint=hashlib.sha256(raw).hexdigest()
    if fingerprint!=SOURCE_SHA256:raise SystemExit("Template SHA mismatch: "+fingerprint)
    with sqlite3.connect(str(args.database)) as con:
        ids=[int(row[0]) for row in con.execute('SELECT run_id FROM Runs ORDER BY run_id')]
    if not ids or len(set(ids))!=len(ids) or any(i<=0 for i in ids):
        raise SystemExit('Invalid HRU population identities')
    n_hrus=len(ids)
    if args.expected is not None and n_hrus!=args.expected:
        raise SystemExit(f"Unexpected HRU population: {n_hrus}; expected {args.expected}")
    args.output.mkdir(parents=True,exist_ok=True)
    records=[]
    for hru in ids:
        try:
            context=build_context(args.database,hru)
            swp=render(raw,context,et_policy=args.et_policy)
            out=args.output/f'run_{hru:05d}'/'swap.swp'
            out.parent.mkdir(parents=True,exist_ok=True)
            data=swp.encode('utf-8')
            if not out.exists() or out.read_bytes()!=data:
                temp=out.with_suffix('.swp.partial')
                temp.write_bytes(data)
                temp.replace(out)
            records.append({'hru':hru,'status':'SWP_CREATED','sha256':hashlib.sha256(data).hexdigest()})
        except Exception as exc:
            records.append({'hru':hru,'status':'FAILED','error':str(exc)})
    ok=sum(x['status']=='SWP_CREATED' for x in records)
    report={'schema_version':1,'profile':PROFILE_ID,'expected':n_hrus,'generated':ok,
        'failed':len(records)-ok,'template_sha256':fingerprint,
        'database_sha256':hashlib.sha256(args.database.read_bytes()).hexdigest(),
        'production_admitted':False,'records':records}
    (args.output/'swp_generation_status.json').write_text(json.dumps(report,indent=2)+chr(10),encoding='utf-8')
    print(f'SWP generated={ok}/{n_hrus} failed={len(records)-ok}')
    return 0 if ok==n_hrus else 2
if __name__=='__main__':sys.exit(main())
