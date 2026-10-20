"""Hash-bound W03-W06 reconstruction; historical replay is never admission.

Run: python -m tools.hru_source_chain --plan PLAN.json --output OUTPUT
All paths in a plan are relative to the plan unless absolute. Stage products
are immutable and reused only after output hashes have been rechecked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from tools.build_canonical_svat import FLAG_COLUMNS
from tools.lhm_postprocess import read_ascii_grid
from tools.hru_incremental import row_fingerprints

SOURCE_SHA="6e5055241590be6bf7f7afe53a2eaf3f03ab3e0627cb9a82bbae138b73eb599e"


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False,default=str)+'\n');tmp.replace(path)


def verify_plan(path):
    plan=json.loads(Path(path).read_text());root=Path(path).resolve().parent
    sources={}
    for name,record in plan['inputs'].items():
        p=Path(record['path']);p=p if p.is_absolute() else root/p
        if sha(p)!=record['sha256']:raise ValueError('Input hash mismatch: '+name)
        for field in ['logical_id','semantic_role','qualification_status','source_location']:
            if not record.get(field):raise ValueError(f'{name}: missing {field}')
        sources[name]=p.resolve()
    if sha(sources['r_source'])!=SOURCE_SHA:raise ValueError('Unexpected historical R authority')
    return plan,sources


def unique(df,col):
    if df[col].isna().any() or df[col].duplicated().any():raise ValueError('Invalid identity: '+col)


def sample_raster(grid,frame):
    col=(frame['xc(m)'].to_numpy()-grid.xllcorner)/grid.cellsize-.5
    row=grid.nrows-(frame['yc(m)'].to_numpy()-grid.yllcorner)/grid.cellsize-.5
    if not (np.allclose(col,np.rint(col),atol=1e-8,rtol=0) and np.allclose(row,np.rint(row),atol=1e-8,rtol=0)):
        raise ValueError('SVATs are not aligned on cell centres')
    col=np.rint(col).astype(int);row=np.rint(row).astype(int)
    if ((col<0)|(col>=grid.ncols)|(row<0)|(row>=grid.nrows)).any():raise ValueError('Outside raster geometry')
    values=grid.values[row,col]
    if (~np.isfinite(values)|(values==grid.nodata)).any():raise ValueError('Missing source raster cells')
    return values


def prepare_population(base,processed,ldgb,lookup):
    """Recreate selected original state and retain the three donor concepts."""
    unique(base,'svat');unique(processed,'svat')
    mapped=base.landgebruik22.map(lookup.set_index('LU-ID')['LWKM-ID'])
    if mapped.isna().any():raise ValueError('Missing land-use lookup')
    selected=mapped.gt(0)
    if not selected.equals(base.lu2.isin([1,2])):raise ValueError('Domain definitions disagree')
    if not selected.equals(base['islwkm(0/1)'].eq(1)):raise ValueError('Historical domain flag differs')
    pop=base.loc[selected].copy()
    if set(pop.svat)!=set(processed.svat):raise ValueError('Processed population differs')
    if pop[['xc(m)','yc(m)']].duplicated().any():raise ValueError('Overlapping SVAT cells')
    if not np.isfinite(pop['opp(m2)']).all() or (pop['opp(m2)']<=0).any():raise ValueError('Invalid area')
    flags=pop[FLAG_COLUMNS].apply(pd.to_numeric,errors='raise')
    if flags.isna().any().any() or (flags<0).any().any():raise ValueError('Unknown qualification flags')
    pop['is_valid_for_hru_cluster_building']=~flags.gt(0).any(axis=1)
    donor=processed.set_index('svat').svat_donor.reindex(pop.svat).to_numpy()
    pop['legacy_pre_hru_donor_svat']=donor
    if not np.array_equal(donor!=pop.svat,~pop.is_valid_for_hru_cluster_building):
        raise ValueError('Replacement targets differ from qualification targets')
    if not set(donor)<=set(pop.svat):raise ValueError('Pre-HRU donor outside selected population')
    pop['qualification_reason_ids']=[';'.join(c for c in FLAG_COLUMNS if r[c]>0) for r in flags.to_dict('records')]
    unique(ldgb.rename(columns={'x':'xc(m)','y':'yc(m)'}).assign(coord=lambda x:list(zip(x['xc(m)'],x['yc(m)']))),'coord')
    coords=ldgb.rename(columns={'x':'xc(m)','y':'yc(m)'})
    pop=pop.merge(coords,on=['xc(m)','yc(m)'],how='left',validate='many_to_one',sort=False)
    missing=pop.LDGBclus.isna()
    pop['ldgb_assignment']='EXACT_XY'
    if missing.any():
        tree=cKDTree(coords[['xc(m)','yc(m)']].to_numpy())
        dist,idx=tree.query(pop.loc[missing,['xc(m)','yc(m)']].to_numpy(),k=1)
        pop.loc[missing,['LDGBclus','LDGB']]=coords.iloc[idx][['LDGBclus','LDGB']].to_numpy()
        pop.loc[missing,'ldgb_assignment']='NEAREST_XY_TIE_NOT_RANN_QUALIFIED'
        pop.loc[missing,'ldgb_distance_m']=dist
    pop['cluster_support_m2']=62500.
    # This restores original targets. Nature drain override is only applied
    # to valid rows by the historical source, not the restored suspect rows.
    pop['cluster_isdrain']=pop['isdrain(0/1)']
    pop.loc[pop.is_valid_for_hru_cluster_building & pop.lu2.eq(2),'cluster_isdrain']=0
    return pop


def audit_replacement(base,processed):
    """Independent materialization regression; donor selection is NOT inferred."""
    targets=processed[processed.svat.ne(processed.svat_donor)].copy()
    source=base.set_index('svat')
    donor=source.reindex(targets.svat_donor).reset_index(drop=True)
    original=source.reindex(targets.svat).reset_index(drop=True)
    targets=targets.reset_index(drop=True)
    rows=[]
    for col in targets:
        if col in ['svat','svat_donor','x','y','opp(m2)']:continue
        if col not in donor:continue
        eq=targets[col].eq(donor[col])|(targets[col].isna()&donor[col].isna())
        rows.append(dict(column=col,mismatches=int((~eq).sum()),role='DONOR_PROPERTY'))
    for col,src in [('x','xc(m)'),('y','yc(m)'),('opp(m2)','opp(m2)')]:
        rows.append(dict(column=col,mismatches=int(targets[col].ne(original[src]).sum()),role='TARGET_PROPERTY'))
    return pd.DataFrame(rows)


def cache_valid(directory,fingerprint):
    p=directory/'stage.json'
    if not p.exists():return False
    old=json.loads(p.read_text())
    if old['fingerprint']!=fingerprint:raise ValueError('Changed stage inputs require a new output directory')
    for name,digest in old['outputs'].items():
        if not (directory/name).is_file() or sha(directory/name)!=digest:raise ValueError('Corrupt cached product: '+name)
    return True


def seal(directory,fingerprint,parents,status):
    files={str(p.relative_to(directory)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='stage.json'}
    atomic_json(directory/'stage.json',dict(fingerprint=fingerprint,parents=parents,outputs=files,
        status=status,production_admitted=False))


def fingerprint(binding):
    return hashlib.sha256(json.dumps(binding,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def run(plan_path,output,*,rscript='Rscript',prepare_only=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    plan,src=verify_plan(plan_path)
    code={p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('replay_hru_source.R'),Path(__file__).with_name('hru_incremental.py')]}
    parents={k:sha(v) for k,v in src.items()}
    fp=fingerprint(dict(inputs=parents,code=code,policy=plan['policy']))
    stage=output/'W03';reused=cache_valid(stage,fp)
    if not reused:
        stage.mkdir(exist_ok=True)
        base=pd.read_csv(src['base_svat']);processed=pd.read_csv(src['processed_svat']);ldgb=pd.read_csv(src['ldgb'])
        pop=prepare_population(base,processed,ldgb,pd.read_csv(src['landuse_lookup']))
        replacement=audit_replacement(base,processed)
        if replacement.mismatches.any():raise ValueError('Pre-HRU replacement differs from documented copy')
        replacement.to_csv(stage/'replacement-regression.csv',index=False)
        grid=read_ascii_grid(src['svat_raster'])
        sampled=sample_raster(grid,pop)
        if not np.array_equal(sampled,pop.svat):raise ValueError('SVAT raster ID mismatch')
        filt=read_ascii_grid(src['historical_filter'])
        if (grid.ncols,grid.nrows,grid.xllcorner,grid.yllcorner,grid.cellsize)!=(filt.ncols,filt.nrows,filt.xllcorner,filt.yllcorner,filt.cellsize):raise ValueError('Filter geometry differs')
        support=np.isin(grid.values,pop.svat)
        old=filt.values>0
        different=np.argwhere(support!=old)
        pd.DataFrame([dict(row=int(r),col=int(c),svat=int(grid.values[r,c]),historical_selected=bool(old[r,c]),selected=bool(support[r,c])) for r,c in different]).to_csv(stage/'legacy-filter-differences.csv',index=False)
        pop.to_csv(stage/'SVAT_QUALIFIED.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        rowfp=row_fingerprints(pop)
        atomic_json(stage/'svat-fingerprints.json',rowfp)
        summary=dict(base_svats=len(base),selected_svats=len(pop),excluded_svats=len(base)-len(pop),
            suspected=int((~pop.is_valid_for_hru_cluster_building).sum()),
            nearest_ldgb=int(pop.ldgb_assignment.ne('EXACT_XY').sum()),
            historical_filter_difference_count=len(different),
            target_area_m2=float(pop['opp(m2)'].sum()),cluster_support_m2=float(pop.cluster_support_m2.sum()),
            grid=dict(ncols=grid.ncols,nrows=grid.nrows,cellsize=grid.cellsize,xllcorner=grid.xllcorner,yllcorner=grid.yllcorner),
            raw_raster_producer_complete=False,source_snapshot_reconstruction=True,production_admitted=False)
        atomic_json(stage/'summary.json',summary)
        seal(stage,fp,parents,'QUALIFIED_NOT_ADMITTED_AS_SNAPSHOT_RECONSTRUCTION')
    result=dict(W03_reused=reused,fingerprint=fp,production_admitted=False)
    if not prepare_only:
        replay=output/'W04-W05'
        runtime=subprocess.run([rscript,'--version'],text=True,capture_output=True,check=True).stdout.strip()
        rfp=fingerprint(dict(parent=fp,r_runtime=runtime,packages_probe=subprocess.run([rscript,'-e',
            'cat(paste(installed.packages()[,1],installed.packages()[,3],collapse=";"))'],text=True,capture_output=True,check=True).stdout))
        reused_r=cache_valid(replay,rfp)
        if not reused_r:
            replay.mkdir(exist_ok=True)
            staging=output/'r-input';(staging/'Herschikking/20251114').mkdir(parents=True,exist_ok=True)
            for name,dest in [('base_svat','Herschikking/20251114/SVAT_INFO.csv'),('processed_svat','Herschikking/20251114/svat_info_lwkm_new.csv'),('ldgb','xyLDGBclus.csv')]:
                p=staging/dest
                if p.is_symlink():p.unlink()
                if p.exists():raise ValueError('Unexpected staging input')
                p.symlink_to(src[name])
            with (replay/'execution.log').open('w') as log:
                p=subprocess.run([rscript,str(Path(__file__).with_name('replay_hru_source.R').resolve()),str(src['r_source']),str(staging.resolve()),str(replay.resolve())],stdout=log,stderr=subprocess.STDOUT)
            if p.returncode:
                atomic_json(output/'blocker.json',dict(stage='W04-W05',exit_code=p.returncode,log=str(replay/'execution.log'),production_admitted=False))
                raise RuntimeError('Historical R replay failed; see execution.log')
            seal(replay,rfp,dict(parent_W03=fp,r_runtime=runtime),'REPLAY_COMPLETE_NOT_ADMITTED')
        result['W04_W05_reused']=reused_r
    atomic_json(output/'run.json',result)
    print(json.dumps(result));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--rscript',default='Rscript');p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args();run(a.plan,a.output,rscript=a.rscript,prepare_only=a.prepare_only)
