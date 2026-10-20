"""Run a bounded real-engine ET-CAL01 qualification using C2 package bytes."""
import argparse
import json
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
from tools.et_calibration import (design, run_experiment, sensitivity, fit_surface,
                                  predict_surface, write_json, digest)


def restore(repo,output,ids):
    """Rehydrate exact inputs, including meteorology, by C2 execution hash."""
    z=zipfile.ZipFile(repo/'docs/evidence/2026-10-19-work-c2/execution-evidence.zip')
    index=json.loads(z.read('file-index.json'))
    old=zipfile.ZipFile(repo/'docs/evidence/2026-10-19-work-c/execution-evidence.zip')
    met=old.read('complete-example-7876/7876.met')
    for hid in ids:
        e=json.loads(z.read(index[f'catalogue-executions/{hid}/execution.json']))
        dest=output/str(hid);dest.mkdir(parents=True)
        for name,h in e['input_sha256'].items():
            b=met if name=='7876.met' else z.read('sha256/'+h)
            p=dest/name;p.write_bytes(b)
            if digest(p)!=h:raise ValueError('restoration mismatch '+name)
    return output


def boundary_controls(output,executable,runtime):
    """Deliberate artificial boundary-error probes, never new HRU authority."""
    import shutil,re
    from tools.et_calibration import scalar,replace_scalar,compare
    source=output/'packages/7870'
    base=pd.read_csv(output/'experiments/7870/004/decades.csv')
    records=[]
    for kind in ['bbc_plus_01mm_day','drainage_resistance_times_08']:
        p=output/'boundary-inputs'/kind
        shutil.copytree(source,p)
        if kind.startswith('bbc'):
            f=next(p.glob('*.bbc'));lines=f.read_text().splitlines()
            for i,line in enumerate(lines):
                words=line.split()
                if len(words)==2 and re.match(r'^\d{2}-',words[0]):
                    lines[i]=words[0]+' '+format(float(words[1])+.01,'.12e')
            f.write_text('\n'.join(lines)+'\n')
        else:
            f=next(p.glob('*.dra'));text=f.read_text()
            for key in re.findall(r'^\s*(DRARES\d+)\s*=',text,re.M):
                text=replace_scalar(text,key,scalar(text,key)*.8)
            f.write_text(text)
        par=dict(rsc_scale=1.,feddes_scale=1.)
        r,m,d=run_experiment(executable,p,output/'boundary-experiments'/kind,par,library_path=runtime)
        comparison=compare(d,base,par)
        records.append(dict(probe=kind,artificial_boundary_error=True,execution=r,metrics=m,comparison=comparison))
    write_json(output/'boundary-controls.json',records)
    return records


def archive(output):
    with zipfile.ZipFile(output/'execution-evidence.zip','w',zipfile.ZIP_DEFLATED) as bundle:
        ix={};seen=set()
        for root in [output/'packages',output/'experiments',output/'boundary-inputs',output/'boundary-experiments']:
            for path in sorted(root.rglob('*')):
                if path.is_file():
                    h=digest(path);ix[str(path.relative_to(output))]='sha256/'+h
                    if h not in seen:bundle.write(path,'sha256/'+h);seen.add(h)
        bundle.writestr('file-index.json',json.dumps(ix,sort_keys=True,indent=2))


def qualify(repo, output, executable, runtime):
    ids=[7870,7876,7929]
    packages=restore(repo,output/'packages',ids)
    results=[];summaries=[];parity=[]
    z=zipfile.ZipFile(repo/'docs/evidence/2026-10-19-work-c2/execution-evidence.zip')
    index=json.loads(z.read('file-index.json'))
    for hid in ids:
        outputs={};params=[];ys=[]
        for i,v in enumerate(design(True)):
            folder=output/'experiments'/str(hid)/f'{i:03d}'
            r,m,d=run_experiment(executable,packages/str(hid),folder,v,library_path=runtime)
            key=(v['rsc_scale'],v['feddes_scale']);outputs[key]=d;params.append(key);ys.append(d.ET.to_list())
            results.append({'hru':hid,'experiment':i,'parameters':v,'execution':r,'metrics':m})
            if key==(1.,1.):
                import io
                old=pd.read_csv(io.BytesIO(z.read(index[f'catalogue-executions/{hid}/result_output.csv'])),comment='*')
                new=pd.read_csv(folder/'run/result_output.csv',comment='*')
                cols=old.select_dtypes('number').columns.intersection(new.select_dtypes('number').columns)
                delta=float((old[cols]-new[cols]).abs().max().max())
                parity.append({'hru':hid,'max_abs_numeric_output_difference':delta,'exact_dates':old.DATE.equals(new.DATE)})
                if delta>1e-8 or not old.DATE.equals(new.DATE):raise ValueError('baseline C2 mismatch')
        s=sensitivity(outputs)
        surface=fit_surface(params,ys)
        # Independent off-grid real SWAP run, not fitted to the nine training points.
        off=dict(rsc_scale=1.125,feddes_scale=.875)
        r,m,d=run_experiment(executable,packages/str(hid),output/'experiments'/str(hid)/'offgrid',off,library_path=runtime)
        results.append({'hru':hid,'experiment':'offgrid','parameters':off,'execution':r,'metrics':m})
        pred=predict_surface(surface,[[off['rsc_scale'],off['feddes_scale']]])[0]
        s.update(hru=hid,surface=surface,offgrid_rmse_mm_decade=float(np.sqrt(np.mean((pred-d.ET.to_numpy())**2))))
        summaries.append(s)
        print(json.dumps({'hru':hid,'parameters':s['parameters'],'offgrid_rmse_mm_decade':s['offgrid_rmse_mm_decade']}),flush=True)
    write_json(output/'runs.json',results);write_json(output/'sensitivity.json',summaries);write_json(output/'baseline-parity.json',parity)
    pd.DataFrame([dict(hru=r['hru'],experiment=r['experiment'],**r['parameters'],**r['metrics'],elapsed_seconds=r['execution']['elapsed_seconds']) for r in results]).to_csv(output/'metrics.csv',index=False)
    summary={'status':'REAL_SWAP_RESEARCH_QUALIFIED','production_admitted':False,'real_metaswap_received':False,
             'runs':len(results),'all_executions_pass':all(r['execution']['status']=='EXECUTION_PASS' for r in results),
             'all_balances_pass':all(r['metrics']['serialized_water_balance_pass'] for r in results),
             'max_balance_error_mm_day':max(r['metrics']['max_total_water_error_mm_d'] for r in results),
             'total_engine_seconds':sum(r['execution']['elapsed_seconds'] for r in results),
             'period':'1971-01-01/1971-12-20','baseline_parity':parity,
             'limitations':['one truncated historical year','two grass profiles and one arable profile only','no irrigated, maize or nature validation','no independent-year validation or factual HRU calibration']}
    controls=boundary_controls(output,executable,runtime)
    summary['boundary_control_runs']=len(controls)
    summary['total_engine_seconds']+=sum(c['execution']['elapsed_seconds'] for c in controls)
    summary['max_balance_error_mm_day']=max([summary['max_balance_error_mm_day']]+[c['metrics']['max_total_water_error_mm_d'] for c in controls])
    write_json(output/'summary.json',summary)
    archive(output)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path('.'))
    for n in ['output','executable','runtime']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(qualify(a.repo,a.output,a.executable,a.runtime),indent=2))
