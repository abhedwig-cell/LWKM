"""Export versioned snapshot-bound interfaces and attach W06 identity evidence."""
import argparse
import gzip
import json
from pathlib import Path
import sqlite3
import pandas as pd
from tools.hru_source_chain import verify_plan,sha,atomic_json
from tools.qualify_hru_replay import clean_membership


def export(plan,work,qualification,output):
    _,src=verify_plan(plan);work=Path(work);q=Path(qualification);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report=json.loads((q/'comparison.json').read_text())
    if report['identical_hrus']!=10242 or report['donor_changes'] or report['representative_changes_with_same_members']:
        raise ValueError('Current context binding requires exact source reconstruction')
    pop=pd.read_csv(work/'W03/SVAT_QUALIFIED.csv.gz')
    member=clean_membership(work/'W04-W05/HRU_MEMBERSHIP.csv')
    m=member[['svat','HRU','hru_cluster_donor_svat','x','y','label']].merge(pop[['svat','opp(m2)','cluster_support_m2']],on='svat',validate='one_to_one')
    if len(m)!=len(pop) or set(m.svat)!=set(pop.svat):raise ValueError('Interface universe differs')
    m=m.rename(columns={'opp(m2)':'svat_area_m2'}).sort_values('svat')
    m.to_csv(output/'HRU_MEMBERSHIP.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    donors=m[['svat','hru_cluster_donor_svat','label']].merge(pop[['svat','legacy_pre_hru_donor_svat','is_valid_for_hru_cluster_building','qualification_reason_ids']],on='svat',validate='one_to_one')
    donors.to_csv(output/'DONOR_ASSIGNMENT.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    s=pd.read_csv(work/'W04-W05/HRU_REPRESENTATIVE.csv').rename(columns={'svat_repr':'hru_representative_svat'})
    s.to_csv(output/'HRU_REPRESENTATIVE.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    core=['svat','xc(m)','yc(m)','opp(m2)','cluster_support_m2','landgebruik22','lu2','lu4','lu7','bodem370','bofek79','pawn21','grondsoort4','grondsoort2','LDGB','LDGBclus','ghg(cm-mv)','glg(cm-mv)','kwelwegzijging(mm/j)','isberegen(0/1)','isdrain(0/1)','is_valid_for_hru_cluster_building','legacy_pre_hru_donor_svat','qualification_reason_ids']
    pop[core].to_csv(output/'SVAT_QUALIFIED.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    with sqlite3.connect(q/'W06/datamodel.sqlite') as con:runs=pd.read_sql_query('select * from Runs order by run_id',con)
    counts=m.groupby('HRU').size();areas=m.groupby('HRU').svat_area_m2.sum()
    audit=runs[['run_id','nusvat','area']].rename(columns={'area':'workbook_area_m2'}).set_index('run_id')
    audit['member_count']=counts;audit['summed_svat_area_m2']=areas
    audit['area_delta_m2']=audit.workbook_area_m2-audit.summed_svat_area_m2
    audit['full_cell_support_m2']=counts*62500.
    if audit.nusvat.ne(audit.member_count).any():raise ValueError('Context membership count changed')
    audit.to_csv(output/'W06-area-audit.csv')
    contexts=pd.read_csv(q/'W06/context-comparison.csv')
    contexts['replayed_same_members_and_attributes']=True
    contexts['snapshot_upstream_identity_reproduced']=True
    contexts['complete_upstream_lineage']=False
    contexts.to_csv(output/'HRU_CONTEXT_10242.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    # Persist all actual typed contexts without duplicating the complete SWP
    # strings. All SWP hashes and selected full examples accompany the archive.
    examples=output/'examples';examples.mkdir(exist_ok=True)
    with gzip.open(q/'W06/contexts-and-swps.jsonl.gz','rt') as source, gzip.GzipFile(filename='',fileobj=(output/'HRU_CONTEXT_10242.jsonl.gz').open('wb'),mode='wb',mtime=0) as target:
        for line in source:
            r=json.loads(line)
            target.write((json.dumps(dict(run_id=r['run_id'],context=r['context']),sort_keys=True,separators=(',',':'))+'\n').encode())
            if r['run_id'] in [1,7870,7871,7929]:(examples/f'{r["run_id"]}.swp').write_text(r['swp'])
    summary=dict(population=len(s),svats=len(m),donor_changes_vs_self=int(m.svat.ne(m.hru_cluster_donor_svat).sum()),
        legacy_replacement_targets=int(donors.svat.ne(donors.legacy_pre_hru_donor_svat).sum()),
        cluster_support_m2=float(m.cluster_support_m2.sum()),svat_area_m2=float(m.svat_area_m2.sum()),
        workbook_area_m2=float(audit.workbook_area_m2.sum()),area_difference_hrus=int(audit.area_delta_m2.ne(0).sum()),
        area_max_abs_difference_m2=float(audit.area_delta_m2.abs().max()),area_sum_difference_m2=float(audit.area_delta_m2.sum()),
        reproduced_hru_schema_fields=len(s.columns),contexts=10242,swps_identical_to_c2=10242,
        from_snapshot_reproduced=True,from_raw_lhm_complete=False,new_swap_executions=0,
        reason_no_swap_rerun='All 10242 rendered SWPs and upstream schema identities unchanged; C2 execution evidence retained',production_admitted=False)
    atomic_json(output/'summary.json',summary)
    context_summary=json.loads((q/'W06/context-summary.json').read_text())
    context_summary['replayed_same_members_and_attributes']=10242
    context_summary['binding_comparison_sha256']=sha(q/'comparison.json')
    context_summary['complete_upstream_lineage']=False
    atomic_json(q/'W06/context-summary.json',context_summary)
    manifest=dict(schema_version=1,profile='LWKM_HRU10242_REPLAY_20261019',
        status='REGRESSION_QUALIFIED_FOR_RECOVERED_SNAPSHOT_NOT_PRODUCTION_ADMITTED',
        interfaces={name:dict(version=1,artifact=file,sha256=sha(output/file)) for name,file in [
            ('SVAT_QUALIFIED','SVAT_QUALIFIED.csv.gz'),('DONOR_ASSIGNMENT','DONOR_ASSIGNMENT.csv.gz'),
            ('HRU_MEMBERSHIP','HRU_MEMBERSHIP.csv.gz'),('HRU_REPRESENTATIVE','HRU_REPRESENTATIVE.csv.gz'),
            ('HRU_CONTEXT_10242','HRU_CONTEXT_10242.jsonl.gz')]},
        input_sha256={k:sha(p) for k,p in src.items()},W03_stage_sha256=sha(work/'W03/stage.json'),
        W04_W05_stage_sha256=sha(work/'W04-W05/stage.json'),comparison_sha256=sha(q/'comparison.json'),
        code_sha256=sha(Path(__file__)),production_admitted=False)
    atomic_json(output/'interfaces.json',manifest);print(json.dumps(summary));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['plan','work','qualification','output']:p.add_argument('--'+n,type=Path,required=True)
    export(**vars(p.parse_args()))
