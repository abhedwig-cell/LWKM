"""Package final C2 identities and all population DRA bytes for reproducible transfer."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def bundle(work,previous,output):
    output.mkdir(parents=True,exist_ok=True)
    for source,name in [('drainage/identity.json','drainage-identity.json'),('drainage/initial-summary.json','drainage-initial.json'),
            ('drainage/summary.json','drainage-incremental.json'),('drainage/h1-cell-decisions.csv','h1-cell-decisions.csv'),
            ('catalogue.json','research-input-catalogue.json')]:shutil.copyfile(work/source,output/name)
    for source,name in [('population-swp/initial-build.json','swp-initial.json.gz'),('population-swp/build.json','swp-incremental.json.gz'),
            ('dra-population/initial-build-status.json','dra-initial.json.gz'),('dra-population/build-status.json','dra-incremental.json.gz'),
            ('catalogue-build/initial-build-status.json','catalogue-initial.json.gz'),('catalogue-build/build-status.json','catalogue-incremental.json.gz'),
            ('modern-pm/summary.json','modern-pm.json.gz'),('catalogue-executions/initial-summary.json','owner-execution-initial.json.gz'),
            ('catalogue-executions/summary.json','owner-execution-incremental.json.gz')]:
        with gzip.open(output/name,'wb') as f:f.write((work/source).read_bytes())
    changed=[]
    new=json.loads((work/'population-swp/build.json').read_text())
    old=json.loads((previous.parent/'work/modern-population-final/build.json').read_text());old={r['run_id']:r['swp_sha256'] for r in old['rows']}
    for r in new['rows']:
        if r['swp_sha256']!=old[r['run_id']]:changed.append(dict(run_id=r['run_id'],before=old[r['run_id']],after=r['swp_sha256']))
    atomic_json(output/'swp-profile-changes.json',dict(changed_count=len(changed),changes=changed))
    with gzip.open(output/'all-dra-files.jsonl.gz','wt') as dst:
        for p in sorted((work/'dra-population').glob('*.dra'),key=lambda p:int(p.stem)):
            dst.write(json.dumps(dict(hru=int(p.stem),sha256=sha256(p),text=p.read_text()),separators=(',',':'))+'\n')
    for p in work.parent.glob('work-c2-*.log'):shutil.copyfile(p,output/p.name.removeprefix('work-c2-'))
    code=[p for p in Path('tools').glob('*.py') if p.name.startswith('work_c2_') or p.name in ['dra_owner_policy.py','build_owner_dra_population.py','execute_catalogue_packages.py','modern_swp.py','work_c_packages.py','build_modern_population.py','build_production_packages.py']]
    atomic_json(output/'code-file-hashes.json',{str(p):sha256(p) for p in sorted(code)})
    atomic_json(output/'artifact-sha256.json',{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='artifact-sha256.json'})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['work','previous','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();bundle(a.work,a.previous,a.output)
