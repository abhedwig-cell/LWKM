"""Selective, restartable Q0-Q4 collection from explicit consumer file bindings.

No recursive full-run scan. Plan items bind exact native paths, roles, dates,
layer, package, units, semantics evidence, plus optional prior SHA256.
"""
import argparse,json,shutil,tempfile
from pathlib import Path
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def collect(plan,output):
    data=json.loads(plan.read_text());output.mkdir(parents=True,exist_ok=True)
    objects=output/'objects';objects.mkdir(exist_ok=True);rows=[];seen=set()
    for x in data['items']:
        for k in ['logical_id','path','role','date','layer','package','units','consumer','semantics_evidence']:
            if not x.get(k):raise ValueError('unbound plan field: '+k)
        key=(x['logical_id'],x['date'])
        if key in seen:raise ValueError('duplicate consumer identity')
        seen.add(key);src=Path(x['path'])
        if not src.is_file():rows.append(dict(**x,status='MISSING'));continue
        h=sha256(src)
        if x.get('sha256') and x['sha256'].lower()!=h:raise ValueError('source SHA changed: '+x['logical_id'])
        target=objects/h;reused=target.exists()
        if reused:
            if sha256(target)!=h:raise ValueError('corrupt collected object')
        else:
            with tempfile.NamedTemporaryFile(dir=objects,delete=False) as f:temp=Path(f.name)
            try:
                shutil.copyfile(src,temp)
                if sha256(temp)!=h:raise ValueError('source changed during collection')
                temp.replace(target)
            finally:
                if temp.exists():temp.unlink()
        rows.append(dict(**{k:v for k,v in x.items() if k!='sha256'},sha256=h,object_path=str(target.resolve()),status='Q2_BYTES_VERIFIED',reused=reused))
    missing=sum(x['status']=='MISSING' for x in rows)
    qualification='Q2_STAGED_NOT_BUNDLE_VERIFIED'
    if not missing and data.get('controls'):
        from tools.lwkm_source_bundle import build_bundle_from_plan,verify_bundle,unpack_bundle
        bundle_plan=dict(schema='lwkm-source-plan-v1',controls=data['controls'],sources=[
            dict(logical_name=x['logical_id'],path=x['object_path'],**{'class':'run_output'},period=x['date']) for x in rows])
        atomic_json(output/'bundle-plan.json',bundle_plan)
        archive=output/'daily-source-bundle.zip'
        # Existing correct bundle is verified, not regenerated.
        binding=dict(plan_sha256=sha256(plan),source_hashes=[x['sha256'] for x in rows],control_hashes={x['path']:sha256(Path(x['path'])) for x in data['controls']})
        if archive.exists():
            prior=json.loads((output/'bundle-binding.json').read_text())
            if prior!=binding:raise ValueError('immutable bundle plan changed; use new directory')
        else:
            build_bundle_from_plan(output/'bundle-plan.json',archive)
            atomic_json(output/'bundle-binding.json',binding)
        verify_bundle(archive)
        with tempfile.TemporaryDirectory(prefix='lwkm-q4-') as td:unpack_bundle(archive,Path(td)/'fresh')
        qualification='Q4_BUNDLE_VERIFIED_NOT_SEMANTICALLY_ADMITTED'
        for x in rows:x['status']='Q4_BYTES_VERIFIED'

    result=dict(schema_version=1,plan_sha256=sha256(plan),count=len(rows),missing=missing,
        reused=sum(x.get('reused',False) for x in rows),qualification=qualification,production_admitted=False,files=rows)
    atomic_json(output/'manifest.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=collect(a.plan,a.output);print(json.dumps({k:v for k,v in r.items() if k!='files'}))
