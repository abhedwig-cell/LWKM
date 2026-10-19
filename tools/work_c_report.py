"""Build bounded Work C evidence from actual packages, executions and population checks."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import zipfile
import pandas as pd
from tools.assemble_swap_package import sha256


def metrics(path,run_id,variant):
    f=pd.read_csv(path,comment='*');g=f.iloc[1:]
    if g.empty:raise ValueError('no simulated days')
    net=g.RAIN+g.IRRIG-g.RUNOFF-g.EIC-g.EPD-g.EACT-g.TACT-g.DRN+g.SSDI+g.BOT
    storage=f[['WTOT','PD_VOL','IC_VOL']].sum(axis=1).diff().iloc[1:]
    error=10*(net-storage)
    row={'run_id':run_id,'variant':variant,'start':str(g.DATE.iloc[0]),'end':str(g.DATE.iloc[-1]),
         'days':len(g),'max_total_water_error_mm_d':float(error.abs().max()),
         'total_water_error_period_mm':float(error.sum()),
         'serialized_water_balance_pass':bool(error.abs().max()<=.001),
         'serialized_water_balance_tolerance_mm_d':.001,
         'max_reported_baldev_mm':float(g.BALDEV.abs().max()*10),
         'mean_gwl_cm':float(g.GWL.mean()),'min_gwl_cm':float(g.GWL.min()),'max_gwl_cm':float(g.GWL.max())}
    for key in ('RAIN','IRRIG','RUNOFF','EIC','EPD','EACT','TACT','DRN','SSDI','BOT'):
        row[key.lower()+'_mm']=float(g[key].sum()*10)
    row['total_et_mm']=sum(row[k+'_mm'] for k in ('eic','epd','eact','tact'))
    return row


def report(work,database,swps,prior,output,*,modern='modern-final',drainage='drainage'):
    output.mkdir(parents=True,exist_ok=True)
    metric_rows=[];all_runs=[];comparisons=[];manifests=[];warnings=[]
    for variant in ('reference-final',modern):
        s=json.loads((work/variant/'summary.json').read_text())
        for row in s['runs']:
            if row.get('execution',{}).get('status')!='EXECUTION_PASS':continue
            folder=Path(row['execution_directory']);p=folder/'result_output.csv'
            m=metrics(p,row['run_id'],variant);m['elapsed_seconds']=row['execution']['elapsed_seconds'];metric_rows.append(m)
            all_runs.append({'run_id':row['run_id'],'variant':variant,'execution':row['execution']})
            pkg=Path(row['package'])
            manifests.append({'run_id':row['run_id'],'variant':variant,
                'fingerprint':row['fingerprint'],'manifest':json.loads((pkg/'manifest.json').read_text()),
                'provenance':json.loads((pkg/'provenance.json').read_text()),
                'preflight':json.loads((pkg/'preflight.json').read_text())})
            w=folder/'swap.wrn';warnings.append({'run_id':row['run_id'],'variant':variant,
                'warning_file_sha256':sha256(w) if w.exists() else None,
                'warning_text':w.read_text() if w.exists() else ''})
            old=prior/str(row['run_id'])/'result_output.csv'
            if variant=='reference-final' and old.exists():
                previous=json.loads((old.parent/'execution.json').read_text())
                if previous['status']!='EXECUTION_PASS':
                    comparisons.append({'run_id':row['run_id'],'prior_status':previous['status'],
                        'common_days':0,'comparison_status':'PRIOR_RUN_INCOMPLETE_NO_EQUIVALENCE_CLAIM'})
                    continue
                a=pd.read_csv(old,comment='*');b=pd.read_csv(p,comment='*')
                # Exclude both runs' terminal closure days from trajectory equivalence.
                b=b.iloc[1:-1];a=a[a.DATE.isin(b.DATE)].set_index('DATE');b=b.set_index('DATE')
                common=sorted(set(a.select_dtypes('number'))&set(b.select_dtypes('number')))
                delta=(a.loc[b.index,common]-b[common]).abs()
                comparisons.append({'run_id':row['run_id'],'common_days':len(b),
                    'max_abs_by_variable':delta.max().to_dict(),'reference':'PR3_INTERFACE_EXPERIMENT_NOT_ORIGINAL_HISTORICAL_OUTPUT'})
    cf=json.loads((work/'sourced-crop-factor'/'summary.json').read_text())
    for row in cf['results']:
        p=work/'sourced-crop-factor'/'executions'/str(row['run_id'])/'result_output.csv'
        m=metrics(p,row['run_id'],'sourced-crop-factor');m['elapsed_seconds']=row['execution']['elapsed_seconds'];metric_rows.append(m)
        all_runs.append({'run_id':row['run_id'],'variant':'sourced-crop-factor','execution':row['execution']})
    pd.DataFrame(metric_rows).to_csv(output/'run-metrics.csv',index=False)
    (output/'executions.json').write_text(json.dumps(all_runs,indent=2)+'\n')
    (output/'package-manifests.json').write_text(json.dumps(manifests,indent=2)+'\n')
    (output/'warnings.json').write_text(json.dumps(warnings,indent=2)+'\n')
    (output/'pr3-common-period-comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    d=work/drainage;states=pd.read_csv(d/'status.csv');counts=collections.Counter();limit=[]
    with gzip.open(output/'drainage-checkpoints.jsonl.gz','wt') as dst:
        for p in sorted((d/'hrus').glob('*.json'),key=lambda p:int(p.stem)):
            r=json.loads(p.read_text());dst.write(json.dumps(r,separators=(',',':'))+'\n')
            if r['status']=='BLOCKED':
                error=r['error'];kind=('MISSING_H1_FACTOR' if 'missing infiltration factor' in error else
                    'NO_PROTECTED_PARTITION' if 'NO_ACCEPTABLE' in error else
                    'INFRES_LIMIT' if 'INFRES range' in error else 'DRARES_LIMIT' if 'DRARES range' in error else 'OTHER')
                counts[kind]+=1
                if kind in ('INFRES_LIMIT','DRARES_LIMIT'):
                    resistance=float(error.rsplit(':',1)[1])
                    limit.append({'run_id':r['hru'],'kind':kind,'exact_resistance_d':resistance,
                        'maximum_parser_resistance_d':100000.,
                        'relative_conductance_increase_if_capped':resistance/100000.-1,
                        'flux_bias_if_capped_at_one_m_head_difference_mm_d':1000*(1/100000.-1/resistance)})
    pd.DataFrame(limit).to_csv(output/'resistance-interface-blockers.csv',index=False)
    bad=pd.read_csv(d/'missing_h1_factors.csv');bad[['hru','svat','x','y','row','col','H1_cdr']].to_csv(output/'h1-missing-factor-cells.csv',index=False)
    with sqlite3.connect(database) as con:runs=pd.read_sql_query('select run_id,soil_id,crop_id,lu_id,SWETR,SWBOTB,SWBBCFILE,area from Runs order by run_id',con)
    idx=json.loads((work/modern/'summary.json').read_text());ready={r['run_id'] for r in idx['runs'] if r['status']=='COMPLETE_RESEARCH_PACKAGE'}
    refs={int(p.parent.name.split('_')[1]) for p in (work.parent/'extracted/run_files(1)').glob('*/swap.swp')}
    statuses=[]
    for row in runs.itertuples(index=False):
        s=states[states.hru==row.run_id].iloc[0]
        p=swps/f'run_{row.run_id:05d}'/'swap.swp'
        statuses.append({'run_id':row.run_id,'swp_sha256':sha256(p),'swp_status':'GENERATED_DATAMODEL_ET_PROFILE',
            'dra_status':s.status,'dra_error':s.error if isinstance(s.error,str) else '',
            'modern_daily_met_status':'UNBOUND','modern_bbc_status':'UNBOUND' if row.SWBBCFILE==1 else 'NOT_EXTERNAL_FOR_THIS_CONTEXT',
            'reference_forcing_available':row.run_id in refs,'complete_modern_dra_research_package':row.run_id in ready,
            'production_admitted':False})
    pd.DataFrame(statuses).to_csv(output/'population-build-status.csv',index=False)
    # Deterministic request set from the entire population, no borrowed forcing.
    available=set(int(x) for x in states[states.status=='DRA_INTERFACE_CANDIDATE'].hru)-refs
    sample=runs[runs.run_id.isin(available)].sort_values(['lu_id','soil_id','run_id']).groupby('lu_id').head(1).copy()
    sample['execution_status']='BLOCKED_NO_HRU_BOUND_MET_AND_BBC'
    sample.to_csv(output/'external-representative-run-selection.csv',index=False)
    for n in ('summary.json','identity.json','status.csv'):shutil.copyfile(d/n,output/('drainage-'+n))
    shutil.copyfile(work/'sourced-crop-factor/summary.json',output/'sourced-crop-factor.json')
    metrics_frame=pd.DataFrame(metric_rows)
    summary={'schema_version':1,'baseline':'42813f9cfc9a1105fca593eb787eb7a8e30d6c7a',
        'scope':'1971-01-01 through 1971-12-20, no BBC extrapolation',
        'reference_packages':49,'reference_execution_pass':49,'modern_dra_packages':len(ready),
        'modern_dra_execution_pass':idx['execution_pass'],'sourced_cf_execution_pass':sum(x['execution']['status']=='EXECUTION_PASS' for x in cf['results']),'source_cf':1.0,
        'population_count':len(statuses),'dra_candidate_count':int((states.status=='DRA_INTERFACE_CANDIDATE').sum()),
        'dra_blocked_count':int((states.status=='BLOCKED').sum()),'dra_failure_classes':counts,
        'h1_missing_member_cells':len(bad),'h1_affected_hrus':int(bad.hru.nunique()),
        'maximum_independent_water_error_mm_d':float(metrics_frame.max_total_water_error_mm_d.max()),
        'all_serialized_balance_checks_pass':bool(metrics_frame.serialized_water_balance_pass.all()),
        'scientific_production_admitted':False,'native_etref_tulip':'NO_FACTORS; PM_VARIANT_EXECUTED_WITH_EXPLICIT_ET_POLICY'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # All current outputs and package recipes, one complete modern example.
    with zipfile.ZipFile(output/'execution-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for variant in ('reference-final',modern):
            s=json.loads((work/variant/'summary.json').read_text())
            for row in s['runs']:
                if row.get('execution',{}).get('status')!='EXECUTION_PASS':continue
                for p in Path(row['execution_directory']).iterdir():
                    if p.name in ('result_output.csv','runtime.log','execution.json','swap.log','swap.err','swap.wrn'):
                        z.write(p,f'{variant}/{row["run_id"]}/'+p.name)
                for name in ('swap.swp','manifest.json','preflight.json','provenance.json',f'{row["run_id"]}.dra',f'{row["run_id"]}.bbc'):
                    p=Path(row['package'])/name
                    if p.exists():z.write(p,f'packages/{variant}/{row["run_id"]}/'+name)
        s=json.loads((work/modern/'summary.json').read_text());r=next(x for x in s['runs'] if x['run_id']==7876)
        for p in Path(r['package']).iterdir():z.write(p,'complete-example-7876/'+p.name)
        for p in (work/'sourced-crop-factor').glob('executions/*/*'):
            if p.is_file() and p.name in ('result_output.csv','runtime.log','execution.json','swap.log','swap.err','swap.wrn'):
                z.write(p,'sourced-crop-factor/'+str(p.relative_to(work/'sourced-crop-factor')))
    print(json.dumps(summary))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('work','database','swps','prior','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--modern',default='modern-final');p.add_argument('--drainage',default='drainage')
    a=p.parse_args();report(a.work,a.database,a.swps,a.prior,a.output,modern=a.modern,drainage=a.drainage)
