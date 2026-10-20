"""Export the existing five-component Work A HRU shards as compact transfers."""
import argparse
import json
import sys
from pathlib import Path
import shutil
import pandas as pd
from tools.assemble_swap_package import sha256
from tools.process_daily_budget_plan import bound
from tools.run_dra_protected_population import atomic_json

def export(manifest,population,output):
    cfg=json.loads(manifest.read_text());ids=sorted(pd.read_csv(bound(population)).hru_id.unique().tolist())
    output.mkdir(parents=True,exist_ok=True);files=[]
    for row in cfg['days']:
        src=bound(row['files']['hrus']);f=pd.read_csv(src)
        required=['flf_mm_d','frf_mm_d','fff_mm_d','ghb_mm_d','wel_mm_d','q_ext_mm_d']
        if not set(required)<=set(f) or sorted(f.hru_id.tolist())!=ids or set(f.date)!={row['date']}:
            raise ValueError('incomplete five-component population-day')
        name=row['date']+'.csv';target=output/name
        if not target.exists() or sha256(target)!=sha256(src):shutil.copyfile(src,target)
        files.append(dict(date=row['date'],path=name,sha256=sha256(target)))
    if not files:raise ValueError('no daily products')
    shutil.copyfile(manifest,output/'source-manifest.json')
    result=dict(schema_version=1,product_kind='BBC',dataset_id='WORK_A_FIVE_COMPONENT_HRU_DAILY',population_sha256=population['sha256'],
                source_manifest_sha256=sha256(manifest),source_manifest_path='source-manifest.json',producer_sha256=sha256(Path(sys.executable) if getattr(sys,'frozen',False) else Path(__file__)),
                units='mm/day_positive_into_L1',start=min(r['date'] for r in files),end=max(r['date'] for r in files),
                hru_ids=list(map(int,ids)),status='RESEARCH_CANDIDATE',files=files,
                upstream_provenance={k:cfg[k] for k in ['wel_provenance','ghb_provenance','reconstructed_products'] if k in cfg})
    atomic_json(output/'transfer.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['manifest','population','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();export(a.manifest,json.loads(a.population.read_text()),a.output)
