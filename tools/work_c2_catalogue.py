"""Bind supported research forcing explicitly to owner-rule DRA, no population borrowing."""
import argparse,json
from pathlib import Path
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def create(packages,grass,output):
    rows=json.loads((packages/'summary.json').read_text())['runs']
    overrides={}
    # Crop producer records the actual immutable package directory in its manifest root.
    cf=json.loads((grass/'summary.json').read_text())
    for r in cf['results']:
        candidates=[p for p in (grass/'packages').rglob('manifest.json') if json.loads(p.read_text())['run_id']==r['run_id']]
        if len(candidates)!=1:raise ValueError('ambiguous sourced grass package')
        overrides[r['run_id']]=candidates[0].parent
    runs={}
    for r in rows:
        if r['status']!='COMPLETE_RESEARCH_PACKAGE':continue
        root=overrides.get(r['run_id'],Path(r['package']))
        manifest=json.loads((root/'manifest.json').read_text());assets={}
        for n,m in manifest['assets'].items():
            if n=='swap.swp':continue
            assets[n]=dict(path=str((root/n).resolve()),sha256=sha256(root/n),
                logical_id=f'C2_RESEARCH_{r["run_id"]}_{n}',qualification_status='RESEARCH_CANDIDATE',
                semantic_contract='OWNER_3143f4d_DRA; HISTORICAL_BBC_FIRST_COLUMN; NO_EXTRAPOLATION; SOURCED_GRASS_CF_WHERE_REQUIRED',
                evidence_refs=['docs/evidence/2026-10-19-work-c2/','docs/production/WORK_C2_OWNER_DECISIONS_2026-10-19.md'])
        runs[str(r['run_id'])]=dict(assets=assets)
    catalogue=dict(schema_version=1,profile_id='LWKM_C2_OWNER_RESEARCH_V1',et_policy='owner_tulip_pm',
        start='1971-01-01',end='1971-12-20',expected_population=10242,runs=runs)
    atomic_json(output,catalogue);return catalogue

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['packages','grass','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(len(create(a.packages,a.grass,a.output)['runs']))
