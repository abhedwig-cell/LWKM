"""Execute a dependency-closed HRU component, then a controlled one-SVAT edit.

Unchanged clusters are compared by member sets. Numeric HRU identifiers are
local during this probe; a production release must reconcile global IDs.
"""
import argparse
import json
from pathlib import Path
import subprocess
import pandas as pd
from tools.hru_source_chain import verify_plan,sha,atomic_json
from tools.hru_incremental import impacted,reconcile_component
from tools.qualify_hru_replay import clean_membership,compare
from tools.compare_hru_partitions import compare_partitions,canonical_partition


def run(plan,work,output,rscript='Rscript',empty_group_adapter=False):
    _,src=verify_plan(plan);work=Path(work);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    columns=['svat','LDGB','LDGBclus','ghg(cm-mv)','is_valid_for_hru_cluster_building']
    pop=pd.read_csv(work/'W03/SVAT_QUALIFIED.csv.gz',usecols=columns)
    full=clean_membership(work/'W04-W05/HRU_MEMBERSHIP.csv')
    valid=pop[pop.is_valid_for_hru_cluster_building]
    # Smallest cluster-district with valid inputs; dependency closure may add
    # other cluster districts sharing a donor-search LDGB.
    sizes=valid.groupby('LDGBclus').size().sort_values()
    changed_id=int(valid.loc[valid.LDGBclus.eq(sizes.index[0]),'svat'].iloc[0])
    altered=pop.copy();altered.loc[altered.svat.eq(changed_id),'ghg(cm-mv)']+=1
    invalidation=impacted(pop,altered,full[['svat','HRU']]);ids=set(invalidation['recompute_svats'])
    reference=full[full.svat.isin(ids)]
    if len(ids)==len(pop):raise ValueError('No independent component; global recomputation required')
    processed=pd.read_csv(src['processed_svat']);subset=processed[processed.svat.isin(ids)].copy()
    outcomes={}
    for name in ['unchanged','changed']:
        root=output/name;inputs=root/'input';target=inputs/'Herschikking/20251114';target.mkdir(parents=True,exist_ok=True)
        subset.to_csv(target/'svat_info_lwkm_new.csv',index=False)
        if name=='changed':
            frame=pd.read_csv(target/'svat_info_lwkm_new.csv')
            frame.loc[frame.svat.eq(changed_id),'ghg(cm-mv)']+=1
            frame.to_csv(target/'svat_info_lwkm_new.csv',index=False)
        # Original base and coordinate tables remain byte-identical.
        (target/'SVAT_INFO.csv').symlink_to(src['base_svat'])
        (inputs/'xyLDGBclus.csv').symlink_to(src['ldgb'])
        result=root/'result';result.mkdir()
        with (root/'execution.log').open('w') as log:
            driver='replay_hru_component.R' if empty_group_adapter else 'replay_hru_source.R'
            p=subprocess.run([rscript,str(Path(__file__).with_name(driver).resolve()),str(src['r_source']),str(inputs.resolve()),str(result.resolve())],stdout=log,stderr=subprocess.STDOUT)
        if p.returncode:
            outcomes[name]=dict(status='SOURCE_RUNTIME_FAILED',returncode=p.returncode,log=str(root/'execution.log'))
            break
        candidate=clean_membership(result/'HRU_MEMBERSHIP.csv')
        outcomes[name]=dict(status='EXECUTED',partition=compare_partitions(reference,candidate),
            donor_changes=int(reference.set_index('svat').hru_cluster_donor_svat.ne(candidate.set_index('svat').hru_cluster_donor_svat.reindex(reference.svat).to_numpy()).sum()),
            membership_sha256=sha(result/'HRU_MEMBERSHIP.csv'),representative_sha256=sha(result/'HRU_REPRESENTATIVE.csv'))
        comparison,_=compare(reference,candidate,pd.read_csv(work/'W04-W05/HRU_REPRESENTATIVE.csv'),
            pd.read_csv(result/'HRU_REPRESENTATIVE.csv'),root/'comparison')
        outcomes[name]['same_members_changed_attributes']=comparison['same_members_changed_attributes']
        outcomes[name]['representative_changes']=comparison['representative_changes_with_same_members']
        reconciled,reconciliation=reconcile_component(full,candidate)
        reconciled[['svat','HRU','hru_cluster_donor_svat']].to_csv(root/'reconciled-membership.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        atomic_json(root/'id-reconciliation.json',reconciliation)
        outcomes[name]['id_reconciliation']=reconciliation
    report=dict(changed_svat=changed_id,selected_svats=len(ids),population=len(pop),empty_group_adapter=empty_group_adapter,
        affected_existing_hrus=len(invalidation['affected_existing_hrus']),
        untouched_hrus=len(invalidation['reusable_existing_hrus']),outcomes=outcomes,
        global_hru_id_reconciliation_required=False,stable_id_reconciliation_executed=True,production_admitted=False)
    if outcomes.get('unchanged',{}).get('status')=='EXECUTED' and (not outcomes['unchanged']['partition']['exact_partition_equal']
            or outcomes['unchanged']['donor_changes'] or outcomes['unchanged']['same_members_changed_attributes']):
        report['partial_replay_qualified']=False
    else:report['partial_replay_qualified']=len(outcomes)==2 and all(x['status']=='EXECUTED' for x in outcomes.values())
    atomic_json(output/'summary.json',report);atomic_json(output/'dependency-invalidation.json',invalidation)
    print(json.dumps(report));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['plan','work','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--rscript',default='Rscript');p.add_argument('--empty-group-adapter',action='store_true')
    a=p.parse_args();run(a.plan,a.work,a.output,a.rscript,a.empty_group_adapter)
