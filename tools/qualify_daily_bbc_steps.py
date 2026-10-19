"""Explicit interface experiment on C2 assets, not modern source forcing."""
import argparse,json,re,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from tools.daily_forcing import effective_bbc
from tools.execute_swap_candidate import execute
from tools.package_preflight import validate
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def run(objects,output,executable,library):
    output.mkdir(parents=True,exist_ok=True)
    # Deliberately synthetic signed daily volumes for interface qualification.
    # Values span zero, sign changes, tiny values and sharp daily transitions.
    means=np.array([1.,-2.,3.,0.,.00001,-.00001,2.5,-1.25])
    dates=pd.date_range('1971-01-01',periods=len(means)).strftime('%Y-%m-%d')
    def case(swp):
        hid=int(swp.parent.name.split('_')[1]);rows=[]
        for dt in [.04,1.]:
            name=f'{hid}-dt{dt:g}';source=output/'inputs'/name
            if source.exists():shutil.rmtree(source)
            shutil.copytree(swp.parent,source)
            s=(source/'swap.swp').read_text()
            s=re.sub(r'TEND\s*=\s*1971-12-20','TEND = '+dates[-1],s)
            s=re.sub(r'DTMAX\s*=\s*[0-9.]+','DTMAX = '+str(dt),s)
            (source/'swap.swp').write_text(s)
            text=effective_bbc(pd.DataFrame(dict(date=dates,q_ext_mm_d=means)),start=dates[0],end=dates[-1],experimental_daily_steps=True)
            for b in source.glob('*.bbc'):b.write_text(text)
            validate(source)
            dest=output/'runs'/name
            if dest.exists():raise FileExistsError('Use a fresh qualification output: '+str(dest))
            result=execute(executable,source,dest,library_path=library,expected_start=dates[0],expected_end=dates[-1])
            row=dict(hru_id=hid,dtmax=dt,execution=result,interface_experiment=True,modern_source_run=False)
            if result['status']=='EXECUTION_PASS':
                f=pd.read_csv(dest/'result_output.csv',comment='*').iloc[1:]
                row['max_daily_volume_error_mm']=float(np.max(abs(f.BOT.to_numpy()*10-means)))
                row['max_balance_deviation_mm']=float(abs(f.BALDEV).max()*10)
                row['volume_pass']=row['max_daily_volume_error_mm']<=1e-7
            rows.append(row)
        return rows
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=[r for batch in pool.map(case,sorted(objects.glob('*/run_*/swap.swp'))) for r in batch]
    report=dict(cases=len(rows),model_pass=sum(r['execution']['status']=='EXECUTION_PASS' for r in rows),volume_pass=sum(r.get('volume_pass',False) for r in rows),max_daily_volume_error_mm=max((r['max_daily_volume_error_mm'] for r in rows if 'max_daily_volume_error_mm' in r),default=None),max_balance_deviation_mm=max((r['max_balance_deviation_mm'] for r in rows if 'max_balance_deviation_mm' in r),default=None),production_admitted=False,synthetic_interface_only=True,code_sha256=sha256(Path(__file__)),cases_detail=rows)
    atomic_json(output/'summary.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['objects','output','executable','library']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();r=run(a.objects,a.output,a.executable,a.library);print(json.dumps({k:v for k,v in r.items() if k!='cases_detail'}))
