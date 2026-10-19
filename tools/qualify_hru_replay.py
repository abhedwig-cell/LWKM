"""Compare replayed memberships, donors and representatives without label forcing."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from tools.hru_source_chain import atomic_json,sha,verify_plan
from tools.compare_hru_partitions import compare_partitions,canonical_partition
from tools.hru_incremental import impacted
from tools.xlsx_datamodel import materialize_workbook
from tools.swp_context import build_context
from tools.modern_swp import render


def clean_membership(path):
    x=pd.read_csv(path)
    # One supplied CSV includes the same svat_orig column twice. Verify its
    # content instead of silently choosing one of two different identities.
    if 'svat_orig.1' in x:
        if not x.svat_orig.equals(x['svat_orig.1']):raise ValueError('Conflicting duplicate SVAT identity')
        x=x.drop(columns='svat_orig.1')
    x=x.rename(columns={'svat_orig':'svat','svat_donor':'hru_cluster_donor_svat'})
    if x.svat.duplicated().any() or x.svat.isna().any():raise ValueError('Membership not a partition')
    return x


def compare(reference,candidate,rschema,cschema,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    partition=compare_partitions(reference,candidate)
    r=canonical_partition(reference);c=canonical_partition(candidate)
    reverse={v:k for k,v in r.items()};same={k:reverse[v] for k,v in c.items() if v in reverse}
    common=reference.set_index('svat').join(candidate.set_index('svat'),lsuffix='_ref',rsuffix='_new',how='outer')
    common['donor_changed']=common.hru_cluster_donor_svat_ref.ne(common.hru_cluster_donor_svat_new)
    common['hru_label_changed']=common.HRU_ref.ne(common.HRU_new)
    common['membership_changed']=[False if pd.notna(h) and same.get(int(h))==rh else True for h,rh in zip(common.HRU_new,common.HRU_ref)]
    cols=['HRU_ref','HRU_new','hru_cluster_donor_svat_ref','hru_cluster_donor_svat_new','donor_changed','hru_label_changed','membership_changed']
    common[cols].to_csv(out/'svat-comparison.csv.gz',compression={'method':'gzip','mtime':0})
    rs=rschema.set_index('HRU');cs=cschema.set_index('HRU');hrows=[];attrs=[]
    used=set()
    for hid,members in c.items():
        old=same.get(hid);used.add(old)
        row=dict(candidate_HRU=hid,reference_HRU=old,same_members=old is not None,
            candidate_members=len(members),candidate_support_m2=len(members)*62500.,
            representative_changed=True,attribute_difference_count=None)
        if old is not None:
            row['representative_changed']=bool(cs.loc[hid,'svat_repr']!=rs.loc[old,'svat_repr'])
            n=0
            for col in sorted(set(cs)&set(rs)):
                a,b=rs.loc[old,col],cs.loc[hid,col]
                equal=bool((pd.isna(a) and pd.isna(b)) or (np.isclose(a,b,atol=1e-9,rtol=1e-11,equal_nan=True) if isinstance(a,(int,float,np.number)) and isinstance(b,(int,float,np.number)) else a==b))
                if not equal:
                    n+=1;attrs.append(dict(candidate_HRU=hid,reference_HRU=old,field=col,reference=a,candidate=b))
            row['attribute_difference_count']=n
        hrows.append(row)
    hrus=pd.DataFrame(hrows);hrus.to_csv(out/'hru-comparison.csv',index=False)
    pd.DataFrame(attrs,columns=['candidate_HRU','reference_HRU','field','reference','candidate']).to_csv(out/'hru-attribute-differences.csv',index=False)
    report=dict(partition=partition,donor_changes=int(common.donor_changed.sum()),
        svats_with_changed_membership=int(common.membership_changed.sum()),hru_label_changes=int(common.hru_label_changed.sum()),
        same_member_hrus=int(hrus.same_members.sum()),representative_changes_with_same_members=int(hrus.loc[hrus.same_members,'representative_changed'].sum()),
        identical_hrus=int((hrus.same_members & hrus.attribute_difference_count.eq(0)).sum()),
        same_members_changed_attributes=int((hrus.same_members & hrus.attribute_difference_count.gt(0)).sum()),
        missing_reference_hrus=len(set(r)-used),extra_candidate_hrus=len(c)-len(same),production_admitted=False)
    atomic_json(out/'comparison.json',report)
    return report,hrus


def contexts(src,out,chain_rows=None):
    """Workbook execution proof, with a separate upstream-lineage gate.

    Do not manufacture new soil/crop parameters from cluster averages. The
    workbook is a versioned lookup authority, and changed HRUs remain blocked.
    """
    out=Path(out);out.mkdir(parents=True,exist_ok=True);db=out/'datamodel.sqlite'
    if db.exists():db.unlink()
    ingestion=materialize_workbook(src['workbook'],db)
    atomic_json(out/'workbook-ingestion.json',ingestion)
    with sqlite3.connect(db) as con:
        runs=pd.read_sql_query('select * from Runs order by run_id',con)
    schema=pd.read_csv(src['reference_schema']).set_index('HRU')
    candidates=chain_rows.set_index('reference_HRU') if chain_rows is not None else None
    c2=json.loads(gzip.open(Path('docs/evidence/2026-10-19-work-c2/swp-initial.json.gz'),'rt').read())
    expected={r['run_id']:r['swp_sha256'] for r in c2['rows']}
    raw=src['template'].read_bytes();rows=[];failure=[]
    for run in runs.to_dict('records'):
        hid=int(run['run_id'])
        try:
            ctx=build_context(db,hid);text=render(raw,ctx,et_policy='owner_tulip_pm');encoded=text.encode()
            digest=hashlib.sha256(encoded).hexdigest()
            # Keep complete SWP output; gzip JSONL below avoids 10,242 directories.
            row=dict(run_id=hid,context_sha256=hashlib.sha256(json.dumps(ctx,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest(),
                swp_sha256=digest,c2_identical=digest==expected.get(hid),
                workbook_area_m2=run['area'],cluster_support_m2=float(schema.loc[hid,'N'])*62500.,
                original_svat_area_m2=None,representative_svat=int(schema.loc[hid,'svat_repr']),
                complete_upstream_lineage=False,production_admitted=False)
            if candidates is not None and hid in candidates.index:
                cr=candidates.loc[hid]
                row['replayed_same_members_and_attributes']=bool(cr.same_members and cr.attribute_difference_count==0)
            else:row['replayed_same_members_and_attributes']=False
            rows.append(row)
            if 'archive' not in locals():
                archive=gzip.GzipFile(filename='',fileobj=(out/'contexts-and-swps.jsonl.gz').open('wb'),mode='wb',mtime=0)
            archive.write((json.dumps(dict(run_id=hid,context=ctx,swp=text),sort_keys=True,default=str,separators=(',',':'))+'\n').encode())
        except Exception as exc:failure.append(dict(run_id=hid,error=str(exc)))
        if len(rows)%1000==0:print('contexts',len(rows),flush=True)
    if 'archive' in locals():archive.close()
    pd.DataFrame(rows).to_csv(out/'context-comparison.csv',index=False)
    atomic_json(out/'context-failures.json',failure)
    report=dict(worksheets=len(ingestion['sheets']),runs=len(runs),typed_contexts=len(rows),failures=len(failure),
        swps_identical_to_c2=sum(r['c2_identical'] for r in rows),
        replayed_same_members_and_attributes=sum(r['replayed_same_members_and_attributes'] for r in rows),
        production_admitted=False,complete_upstream_lineage=False)
    atomic_json(out/'context-summary.json',report);return report


def qualify(plan,work,out,*,with_contexts=True):
    _,src=verify_plan(plan);work=Path(work);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    ref=clean_membership(src['reference_membership'])
    replay=work/'W04-W05';report=None;rows=None
    if (replay/'COMPLETE').exists():
        cand=clean_membership(replay/'HRU_MEMBERSHIP.csv')
        report,rows=compare(ref,cand,pd.read_csv(src['reference_schema']),pd.read_csv(replay/'HRU_REPRESENTATIVE.csv'),out)
    pop=pd.read_csv(work/'W03/SVAT_QUALIFIED.csv.gz',usecols=['svat','LDGB','LDGBclus','ghg(cm-mv)'])
    altered=pop.copy();altered.loc[altered.index[0],'ghg(cm-mv)']+=1
    inv=impacted(pop,altered,ref[['svat','HRU']]);atomic_json(out/'incremental-controlled-change.json',inv)
    # The unchanged graph must invalidate nothing.
    unchanged=impacted(pop,pop,ref[['svat','HRU']]);atomic_json(out/'incremental-unchanged.json',unchanged)
    if unchanged['recompute_svats']:raise ValueError('Unchanged source invalidated')
    if with_contexts:contexts(src,out/'W06',rows)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['plan','work','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--skip-contexts',action='store_true');a=p.parse_args()
    qualify(a.plan,a.work,a.output,with_contexts=not a.skip_contexts)
