"""Real 2020-07-01 input replay; estimates/derived GHB never become original budget data."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.idf_reader import read_idf
from tools.modflow_daily_rasters import mosaic,into_cell_from_faces
from tools.groundwater_l1_boundary import aggregate
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def run(root,relation,out):
    out.mkdir(parents=True,exist_ok=True)
    manifest=pd.read_csv(root/'manifest.csv',encoding='utf-8-sig');sources=[]
    for r in manifest.itertuples(index=False):
        if r.Status!='FOUND':continue
        p=root/Path(r.ArchivePath.replace('\\','/')).name
        if sha256(p).lower()!=r.SHA256.lower():raise ValueError('source manifest hash mismatch: '+p.name)
        sources.append(dict(role=r.Component,path=str(p.resolve()),original=r.Source,sha256=sha256(p)))
    head=read_idf(next(root.glob('*head_next_midnight*')));active=np.isfinite(head.values)&(head.values!=head.nodata)
    arrays={}
    for role in ['bdgfrf','bdgfff','bdgflf','bdgwel']:
        paths=[Path(s['path']) for s in sources if s['role'].startswith(role)]
        arrays[role]=mosaic(paths,head)
    # The saved-budget sign hypothesis is versioned separately from standard
    # MODFLOW sign conventions. No statement of original LIST verification.
    lat=-into_cell_from_faces(arrays['bdgfrf'],arrays['bdgfff'])
    def crop(p):
        g=read_idf(p);c=(head.xmin-g.xmin)/g.dx;r=(g.ymax-head.ymax)/g.dy
        if g.dx!=head.dx or g.dy!=head.dy or abs(c-round(c))>1e-6 or abs(r-round(r))>1e-6:raise ValueError('GHB misalignment')
        c,r=int(round(c)),int(round(r));v=g.values[r:r+head.nrow,c:c+head.ncol].astype(float)
        if v.shape!=head.values.shape:raise ValueError('GHB coverage')
        return np.where(v==g.nodata,np.nan,v)
    cond=crop(root/'ghb_cond_l1.idf');boundary=crop(root/'ghb_head_l1.idf')
    ghb=np.where(cond==0,0.,cond*(boundary-head.values))
    # Missing conductance is not silently changed into absence of a package.
    f=pd.read_csv(relation,low_memory=False)
    cols=np.floor((f.x.to_numpy()-head.xmin)/head.dx).astype(int);rows=np.floor((head.ymax-f.y.to_numpy())/head.dy).astype(int)
    if ((rows<0)|(cols<0)|(rows>=head.nrow)|(cols>=head.ncol)).any():raise ValueError('membership outside source grid')
    membership=pd.DataFrame(dict(hru_id=f.HRU,cell_id=rows*head.ncol+cols,area_m2=head.dx*head.dy,row=rows,col=cols))
    if membership.cell_id.duplicated().any():raise ValueError('overlapping member cells')
    cells=pd.DataFrame(dict(date='2020-07-01',cell_id=membership.cell_id,flf=arrays['bdgflf'][rows,cols],
        lat=lat[rows,cols],ghb=ghb[rows,cols],wel=arrays['bdgwel'][rows,cols]))
    good=np.isfinite(cells[['flf','lat','ghb','wel']]).all(axis=1)&active[rows,cols]
    status=membership.assign(known=good).groupby('hru_id').agg(member_cells=('cell_id','size'),known_cells=('known','sum'))
    eligible=status.index[status.member_cells==status.known_cells]
    m=membership[membership.hru_id.isin(eligible)];c=cells[cells.cell_id.isin(m.cell_id)]
    results=aggregate(c,m[['hru_id','cell_id','area_m2']],start='2020-07-01',end='2020-07-01') if len(m) else pd.DataFrame()
    results.to_csv(out/'hru-components-RESEARCH.csv',index=False,float_format='%.12g')
    cells.to_csv(out/'cell-components-RESEARCH.csv.gz',index=False,compression={'method':'gzip','mtime':0},float_format='%.12g')
    status.to_csv(out/'coverage.csv');membership.to_csv(out/'membership.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    audit=dict(date='2020-07-01',hru_population=len(status),complete_numerical_hrus=len(eligible),
        represented_cells=len(membership),known_component_cells=int(good.sum()),
        source_semantics=dict(flf='SAVED_POSITIVE_ASSUMED_INTO_LAYER1',lat='CURRENT_MINUS_PREVIOUS_SAVED_FACES',
            ghb='DERIVED_C_TIMES_HEAD_DIFFERENCE_END_MIDNIGHT_NOT_ORIGINAL_DAILY_BUDGET',wel='ESTIMATED_2020_NOT_ORIGINAL'),
        production_admitted=False,missing_cells_not_zero_filled=True,sources=sources,
        auxiliary_sources={p.name:sha256(p) for p in [root/'ghb_cond_l1.idf',root/'ghb_head_l1.idf']},
        code_sha256=sha256(Path(__file__)),
        outputs={p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name!='audit.json'})
    atomic_json(out/'audit.json',audit);print(json.dumps({k:v for k,v in audit.items() if k not in ['sources','outputs']}));return audit

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['root','relation','out']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.root,a.relation,a.out)
