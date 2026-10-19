"""Persist actual C2 runs, balances, warnings and controlled predecessor differences."""
import argparse,json,zipfile
from pathlib import Path
import pandas as pd
from tools.work_c_report import metrics
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def compare(current,previous,hid,label):
    a=pd.read_csv(previous,comment='*').set_index('DATE');b=pd.read_csv(current,comment='*').set_index('DATE')
    common=a.index.intersection(b.index);a=a.loc[common];b=b.loc[common]
    return dict(run_id=hid,comparison=label,common_output_rows=len(common),
        max_gwl_difference_cm=float((b.GWL-a.GWL).abs().max()),
        max_drn_difference_mm_d=float((b.DRN-a.DRN).abs().max()*10),
        total_drn_difference_mm=float((b.DRN.iloc[1:]-a.DRN.iloc[1:]).sum()*10),
        total_ssdi_difference_mm=float((b.SSDI.iloc[1:]-a.SSDI.iloc[1:]).sum()*10))


def report(work,previous,output):
    output.mkdir(parents=True,exist_ok=True);runs=[];m=[];comparisons=[];warnings=[]
    prior={r['run_id']:r for r in json.loads((previous/'modern-v2/summary.json').read_text())['runs'] if r.get('execution',{}).get('status')=='EXECUTION_PASS'}
    pm={r['run_id']:r for r in json.loads((work/'modern-pm/summary.json').read_text())['runs'] if r.get('execution',{}).get('status')=='EXECUTION_PASS'}
    for variant in ['modern-pm','catalogue-executions']:
        summary=json.loads((work/variant/'summary.json').read_text())
        for r in summary['runs']:
            if 'execution' not in r:continue
            p=Path(r['execution_directory']);csv=p/'result_output.csv';hid=r['run_id']
            runs.append(dict(variant=variant,**r))
            if r['execution']['status']=='EXECUTION_PASS':
                row=metrics(csv,hid,variant);row['elapsed_seconds']=r['execution']['elapsed_seconds'];m.append(row)
                previous_row=prior.get(hid) if variant=='modern-pm' else pm.get(hid)
                if previous_row:comparisons.append(compare(csv,Path(previous_row['execution_directory'])/'result_output.csv',hid,'C2_PM_minus_C1_modern_PM' if variant=='modern-pm' else 'OWNER_ET_minus_C2_PM'))
            w=p/'swap.wrn';warnings.append(dict(variant=variant,run_id=hid,sha256=sha256(w) if w.exists() else None,text=w.read_text() if w.exists() else ''))
    cf=json.loads((work/'sourced-cf/summary.json').read_text())
    for r in cf['results']:
        p=work/'sourced-cf/executions'/str(r['run_id']);row=metrics(p/'result_output.csv',r['run_id'],'sourced-cf');row['elapsed_seconds']=r['execution']['elapsed_seconds'];m.append(row)
        runs.append(dict(variant='sourced-cf',execution_directory=str(p.resolve()),**r))
    pd.DataFrame(m).to_csv(output/'run-metrics.csv',index=False);pd.DataFrame(comparisons).to_csv(output/'runtime-comparisons.csv',index=False)
    atomic_json(output/'executions.json',runs);atomic_json(output/'warnings.json',warnings)
    atomic_json(output/'sourced-cf.json',cf)
    summary=dict(calculations=len(runs),execution_pass=sum(r['execution']['status']=='EXECUTION_PASS' for r in runs),
        maximum_water_error_mm_d=max(r['max_total_water_error_mm_d'] for r in m),
        all_water_closures_pass=all(r['serialized_water_balance_pass'] for r in m),
        period='1971-01-01 through 1971-12-20',production_admitted=False)
    atomic_json(output/'runtime-summary.json',summary)
    with zipfile.ZipFile(output/'execution-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        index={};seen=set()
        def put(path,logical):
            h=sha256(path);index[logical]='sha256/'+h
            if h not in seen:z.write(path,'sha256/'+h);seen.add(h)
        for r in runs:
            p=Path(r['execution_directory']);prefix=f'{r["variant"]}/{r["run_id"]}/'
            for n in ['execution.json','result_output.csv','runtime.log','swap.wrn','swap.log','swap.err']:
                if (p/n).exists():put(p/n,prefix+n)
            if r.get('package'):
                package=Path(r['package'])
                for f in package.iterdir():
                    if f.suffix.lower() in ['.json','.dra','.bbc','.swp','.crp','.co2'] or r['run_id'] in [7870,7929,7871]:put(f,'packages/'+prefix+f.name)
        z.writestr('file-index.json',json.dumps(index,sort_keys=True,indent=2))
    print(json.dumps(summary));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['work','previous','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();report(a.work,a.previous,a.output)
