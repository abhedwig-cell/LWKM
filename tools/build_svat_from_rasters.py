"""Declarative, geometry-checked W03 raster producer, without NODATA filling.

The manifest binds the ID raster, attribute rasters and lookup tables by SHA256.
Sampling retains native units; any conversion is an explicit multiplier in the
column specification. Snapshot selection is separate from raw production.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.hru_source_chain import sha,atomic_json
from tools.lhm_postprocess import read_ascii_grid


def geometry(g):return (g.ncols,g.nrows,g.xllcorner,g.yllcorner,g.cellsize)


def build(plan_path,output):
    root=Path(plan_path).resolve().parent;plan=json.loads(Path(plan_path).read_text())
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    bindings={}
    def path(binding):
        p=Path(binding['path']);p=p if p.is_absolute() else root/p
        if sha(p)!=binding['sha256']:raise ValueError('Source hash mismatch: '+str(p))
        for field in ['logical_id','units','semantic_role']:
            if not binding.get(field):raise ValueError('Missing source contract: '+field)
        bindings[binding['logical_id']]=binding
        return p
    grid=read_ascii_grid(path(plan['svat_raster']))
    active=np.isfinite(grid.values)&(grid.values!=grid.nodata)&(grid.values>0)
    row,col=np.where(active);ids=grid.values[active]
    if not np.equal(ids,np.floor(ids)).all() or len(np.unique(ids))!=len(ids):raise ValueError('Non-unique or noninteger SVAT IDs')
    frame=pd.DataFrame({'svat':ids.astype(int),'xc(m)':grid.xllcorner+(col+.5)*grid.cellsize,
        'yc(m)':grid.yllcorner+(grid.nrows-row-.5)*grid.cellsize})
    for name,binding in plan['columns'].items():
        if name in frame:raise ValueError('Column would overwrite SVAT identity')
        g=read_ascii_grid(path(binding))
        if geometry(g)!=geometry(grid):raise ValueError('Raster geometry mismatch: '+name)
        values=g.values[active].astype(float)
        values[(values==g.nodata)|~np.isfinite(values)]=np.nan
        frame[name]=values*binding.get('multiplier',1.)
    for binding in plan.get('attribute_tables',[]):
        table=pd.read_csv(path(binding)).rename(columns=binding.get('rename',{}))
        key=binding.get('key','svat');cols=[key]+binding['columns']
        if table[key].duplicated().any() or table[key].isna().any():raise ValueError('Ambiguous attribute table')
        if any(c in frame for c in cols[1:]):raise ValueError('Attribute table would overwrite identity')
        frame=frame.merge(table[cols],on=key,how='left',validate='one_to_one',sort=False)
    for lookup in plan.get('lookups',[]):
        table=pd.read_csv(path(lookup));key=lookup['key'];cols=[key]+lookup['columns']
        if table[key].duplicated().any() or table[key].isna().any():raise ValueError('Ambiguous lookup')
        if any(c in frame for c in cols[1:]):raise ValueError('Lookup would overwrite an attribute')
        frame=frame.merge(table[cols],on=key,how='left',validate='many_to_one',sort=False)
    missing=frame[plan['required_columns']].isna().sum()
    if missing.any():
        atomic_json(output/'blocker.json',dict(status='BLOCKED_BY_SOURCE_COVERAGE',
            inputs=bindings,rows=len(frame),missing_by_field={k:int(v) for k,v in missing.items() if v},
            production_admitted=False))
        raise ValueError('Missing required source data: '+str({k:int(v) for k,v in missing.items() if v}))
    domain=plan.get('domain',{'column':'lu2','selected_values':[1,2],'known_values':[1,2,3]})
    if frame[domain['column']].isna().any() or not set(frame[domain['column']].unique())<=set(domain['known_values']):raise ValueError('Unknown domain class')
    frame['is_lwkm_domain']=frame[domain['column']].isin(domain['selected_values'])
    frame.to_csv(output/'SVAT_SOURCE.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    atomic_json(output/'manifest.json',dict(schema_version=1,inputs=bindings,
        code_sha256=sha(Path(__file__)),plan_sha256=sha(plan_path),geometry=geometry(grid),
        rows=len(frame),selected=int(frame.is_lwkm_domain.sum()),
        output_sha256=sha(output/'SVAT_SOURCE.csv.gz'),production_admitted=False))
    return frame


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.plan,a.output)
