"""LWKM WB03. Python port of diagnostic LWKM_MF_L1_Balance.cs.

Original layer-one budget first; corrected FLF only as a difference experiment.
No substitute storage, coupling, or residual flux is inferred.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,json,hashlib,re,sys
from pathlib import Path
import numpy as np
from wb01 import read_idf

ROOT=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow')
RUNROOT=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\run_2020_2022')
IBOUND=Path(r'E:\LHM_4.3.3\Data\2_Model_Input\modflow\bnd\ibound_l1.idf')
ROLES=('wel','drn','riv','bnd','sto','flf','qlat','ghb')

def find_coupling_mask(root, geometry, active):
    """Reproduce the October-16 coupling mask from original area_svat.inp."""
    from wb04_mask import find_area_svat, build_area_mask
    source=find_area_svat()
    target=Path(__file__).parent/'bronmasker_uit_area_svat'/'METASWAP_COUPLING_L1.IDF'
    # Check the original source every run; do not reuse a stale generated mask.
    if target.exists():
        import json
        from wb04_mask import sha
        meta=target.with_suffix('.json')
        if meta.exists():
            data=json.loads(meta.read_text(encoding='utf8'))
            if data.get('source_sha256')==sha(source) and data.get('mask_sha256')==sha(target):
                geo,arr,cover=read_idf(target)
                if geo==geometry and np.all(cover[active]):return target
        raise RuntimeError('Existing generated MetaSWAP mask cannot be verified; inspect or use a new package folder')
    return build_area_mask(source,geometry,active,target)

def days(start,end):
    d=dt.date.fromisoformat(start);b=dt.date.fromisoformat(end)
    if d>b or d<dt.date(1970,1,1) or b>dt.date(2022,12,31):raise ValueError('Invalid period')
    while d<=b:yield d;d+=dt.timedelta(days=1)

def expected_filename(name,day):
    return f'bdg{name}_{day}000000_l1.IDF'

def source(root,role,stamp,corrected=False):
    if role=='qlat':return root/'bdgqlat_reconstructed'/f'BDGQLAT_{stamp}.IDF'
    d=root/('bdg'+role)
    if role=='flf' and corrected:d=d/'diepe_slootkwel_gecorrigeerd'
    alternatives=[d/expected_filename(role,stamp),d/f'bdg{role}_{stamp}_l1.idf']
    matches=[p for p in alternatives if p.exists()]
    if len(matches)!=1:raise FileNotFoundError(f'{role} {stamp}: expected one source, found {matches}; checked {alternatives}')
    return matches[0]

def integrate_into(target,filled,path,geometry,require_all=False):
    geo,a,valid=read_idf(path)
    if geo[6:]!=geometry[6:]:raise ValueError('Cell size mismatch: '+str(path))
    nx,ny,xmin,xmax,ymin,ymax,dx,dy=geo
    if abs((xmin-geometry[2])/dx-round((xmin-geometry[2])/dx))>1e-5 or abs((geometry[5]-ymax)/dy-round((geometry[5]-ymax)/dy))>1e-5:
        raise ValueError('Grid offset mismatch: '+str(path))
    c=int(round((xmin-geometry[2])/dx));r=int(round((geometry[5]-ymax)/dy))
    if c<0 or r<0 or c+nx>geometry[0] or r+ny>geometry[1]:raise ValueError('Grid outside reference: '+str(path))
    dest=target[r:r+ny,c:c+nx];cov=filled[r:r+ny,c:c+nx]
    if np.any(cov & valid):raise ValueError('Overlapping valid partitions: '+str(path))
    dest[valid]=np.asarray(a)[valid];cov[valid]=True

def get_mosaic(paths,geometry,require_coverage=False):
    x=np.zeros((geometry[1],geometry[0]),dtype=np.float64)
    covered=np.zeros(x.shape,dtype=bool)
    for path in paths:integrate_into(x,covered,path,geometry)
    return x,covered

def get_merged(root,role,stamp,geometry,corrected=False):
    p=source(root,role,stamp,corrected)
    return get_mosaic([p],geometry)

def get_partitions(root,role,stamp,geometry,base=None):
    base=base or root/('bdg'+role)
    paths=[base/f'bdg{role}_{stamp}_l1_p{i:03d}.idf' for i in range(8)]
    missing=[p for p in paths if not p.exists()]
    if missing:raise FileNotFoundError(f'{role} {stamp}: {len(missing)} of 8 original partitions missing; first {missing[0]}')
    return get_mosaic(paths,geometry)

def get_systems(root,role,stamp,geometry,n):
    out=np.zeros((geometry[1],geometry[0]),dtype=np.float64)
    for i in range(1,n+1):
        p=root/('bdg'+role)/f'bdg{role}_sys{i}_{stamp}000000_l1.IDF'
        if not p.exists():raise FileNotFoundError('Missing system budget '+str(p))
        v,_=get_mosaic([p],geometry)
        out+=v  # systems overlap and must be summed, not mosaicked
    return out

def calendar_decade(day):return (day.year,day.month,min(3,(day.day-1)//10+1))

def run(args):
    root=args.root;outdir=args.output;outdir.mkdir(parents=True,exist_ok=True)
    if not args.mask.exists():raise FileNotFoundError('Original MODFLOW IBOUND absent: '+str(args.mask))
    geometry,mask,valid=read_idf(args.mask)
    active=np.asarray(mask)!=0
    active &= valid
    if not np.any(active):raise ValueError('No active IBOUND cells')
    if args.coupling_mask is None:
        args.coupling_mask=find_coupling_mask(root,geometry,active)
    coupled=None
    if args.coupling_mask:
        _,coupled_arr,cover=read_idf(args.coupling_mask)
        if _!=geometry:raise ValueError('Coupling mask geometry differs')
        if not np.all(cover[active]):raise ValueError('Coupling mask incomplete')
        coupled=np.asarray(coupled_arr)==1
        if np.any(~np.isin(np.asarray(coupled_arr)[active],[0,1])):raise ValueError('Unknown coupling mask value')
    groups={'all_active':active}
    if coupled is not None:
        groups['without_metaswap']=active & ~coupled
        groups['with_metaswap']=active & coupled
    records=[];yearly={};decades={};statuses=[]
    for day in days(args.start,args.end):
        stamp=day.strftime('%Y%m%d')
        try:
            terms={}
            terms['qlat'],cov=get_merged(root,'qlat',stamp,geometry)
            if not np.all(cov[active]):raise ValueError('QLAT NoData in active cell')
            terms['flf'],_ = get_merged(root,'flf',stamp,geometry)
            terms['wel'],_ = get_merged(root,'wel',stamp,geometry)
            terms['drn']=get_systems(root,'drn',stamp,geometry,3)
            terms['riv']=get_systems(root,'riv',stamp,geometry,4)
            for role in ('sto','bnd'):
                # original partitions are required for closure diagnostic
                terms[role],_=get_partitions(root,role,stamp,geometry,base=args.partitions/("bdg"+role))
            # GHB previously independently reconstructed; use existing server product
            terms['ghb'],_=get_merged(root,'ghb',stamp,geometry)
            residual=np.zeros(active.shape,dtype=np.float64)
            for x in terms.values():residual+=x
            corrected=None
            if args.flevoland:
                corrected,_=get_merged(root,'flf',stamp,geometry,corrected=True)
            for group,sel in groups.items():
                n=int(sel.sum())
                row={'date':stamp,'group':group,'cells':n}
                for role in ROLES:row[role+'_m3_day']=float(np.sum(terms[role][sel],dtype=np.float64))
                row['residual_m3_day']=float(np.sum(residual[sel],dtype=np.float64))
                row['mae_m3_cell_day']=float(np.mean(np.abs(residual[sel]))) if n else None
                row['maxabs_m3_cell_day']=float(np.max(np.abs(residual[sel]))) if n else None
                row['root_mean_square_m3_cell_day']=float(np.sqrt(np.mean(residual[sel]**2))) if n else None
                if corrected is not None:
                    row['flf_correction_m3_day']=float(np.sum((corrected-terms['flf'])[sel],dtype=np.float64))
                records.append(row)
                for target,key in ((decades,(day.year,day.month,(day.day-1)//10+1,group)),(yearly,(day.year,group))):
                    acc=target.setdefault(key,{'days':0,'cells':n})
                    acc['days']+=1
                    for col,v in row.items():
                        if col.endswith('_m3_day') and v is not None:acc[col.replace('_m3_day','_m3')]=acc.get(col.replace('_m3_day','_m3'),0.)+v
            statuses.append({'date':stamp,'status':'OK'})
            for row in records[-len(groups):]:
                if row['group']=='without_metaswap':
                    print('WITHOUT_METASWAP',stamp,'cells',row['cells'],'MAE',row['mae_m3_cell_day'], 'residual',row['residual_m3_day'],flush=True)
        except Exception as exc:
            statuses.append({'date':stamp,'status':'FAILED','error':str(exc)})
            if not args.continue_on_missing:
                _save(outdir,records,decades,yearly,statuses,args)
                raise RuntimeError(f'{stamp}: {exc}') from exc
        if len(statuses)%10==0:print(f'Processed {stamp}',flush=True)
    _save(outdir,records,decades,yearly,statuses,args)

def _csv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def _save(outdir,records,decades,years,statuses,args):
    _csv(outdir/'modflow_l1_daily.csv',records)
    _csv(outdir/'modflow_l1_decades.csv',[dict(year=k[0],month=k[1],decade=k[2],group=k[3],**v) for k,v in sorted(decades.items())])
    _csv(outdir/'modflow_l1_years.csv',[dict(year=k[0],group=k[1],**v) for k,v in sorted(years.items())])
    _csv(outdir/'day_status.csv',statuses)
    (outdir/'status.json').write_text(json.dumps({'days_ok':sum(x['status']=='OK' for x in statuses),'days_failed':sum(x['status']=='FAILED' for x in statuses),'closure':'DIAGNOSTIC_NOT_VERIFIED','source_flf':'original uncorrected','corrected_flf':'separate effect only' if args.flevoland else 'not processed','storage':'STO original eight partitions mandatory','coupling':str(args.coupling_mask) if args.coupling_mask else 'UNAVAILABLE'},indent=2),encoding='utf8')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--mask',type=Path,default=IBOUND)
    p.add_argument('--partitions',type=Path,default=RUNROOT/'modflow'/'results')
    p.add_argument('--coupling-mask',type=Path,help='Optional exact original 0/1 coupling raster; otherwise safe auto-discovery')
    p.add_argument('--output',type=Path,default=Path(__file__).parent/'uitvoer_wb04')
    p.add_argument('--start',default='2020-07-01');p.add_argument('--end',default='2020-07-01')
    p.add_argument('--flevoland',action='store_true')
    p.add_argument('--continue-on-missing',action='store_true')
    args=p.parse_args();run(args)
if __name__=='__main__':
    try:main()
    except Exception as e:print('WB03 STOP:',e,file=sys.stderr);sys.exit(2)
