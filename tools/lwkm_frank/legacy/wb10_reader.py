"""LWKM WB10. Seven-source MetaSWAP decade water balance, raw source signs.

The computed residual is an explicit seven-term diagnostic, NOT admitted
as a full-model closure when the separately reported qspgw term is unavailable.
"""
from __future__ import annotations
import argparse, calendar, csv, hashlib, json, re, struct, sys
from datetime import date
from pathlib import Path
import numpy as np

BASE = Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
METASWAP = BASE/'LWKM_run_resultaten_totaal'/'metaswap'
AREA = Path(r'E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp')
SCAP = Path(r'E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\scap_svat.inp')
EXPECTED_SVATS = 645582
VARIABLES = ('bdgdecstot','bdgpm','bdgpssw','bdgpsgw','bdgetact','bdgqrun','bdgqmodf')
EXCEPTION_SVAT = 207543


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()


def atomic_json(path, obj):
    path=Path(path);temp=path.with_name(path.name+'.partial')
    temp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')
    temp.replace(path)


def atomic_csv(path,rows,fieldnames):
    path=Path(path);temp=path.with_name(path.name+'.partial')
    with temp.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,extrasaction='ignore');w.writeheader();w.writerows(rows)
    temp.replace(path)


def decades(start_year,end_year):
    for year in range(start_year,end_year+1):
        for month in range(1,13):
            last=calendar.monthrange(year,month)[1]
            for ix,(begin,end) in enumerate(((1,10),(11,20),(21,last)),1):
                yield {'period':f'{year}{month:02d}_D{ix}', 'year':year,
                       'date_start':f'{year}{month:02d}{begin:02d}',
                       'date_end':f'{year}{month:02d}{end:02d}','days':end-begin+1}


def read_area(path):
    ids=[];areas=[];xs=[];ys=[]
    with Path(path).open('r',encoding='utf-8-sig',errors='replace') as f:
        for no,line in enumerate(f,1):
            s=line.strip()
            if not s or s[0] in '*#!':continue
            a=s.replace(',','.').split()
            if not a or not re.fullmatch(r'\d+',a[0]):continue
            if len(a)!=14:raise ValueError(f'AREA_SVAT line {no}: expected 14 columns, got {len(a)}')
            ident=int(a[0]); area=float(a[1]); x=float(a[9]); y=float(a[10])
            if ident<=0 or not np.isfinite([area,x,y]).all() or area<=0:
                raise ValueError(f'AREA_SVAT invalid at line {no}')
            ids.append(ident);areas.append(area);xs.append(x);ys.append(y)
    if len(ids)!=EXPECTED_SVATS:raise ValueError(f'AREA_SVAT: {len(ids)} SVAT records instead of {EXPECTED_SVATS}')
    if len(set(ids))!=len(ids):raise ValueError('AREA_SVAT duplicate IDs')
    return tuple(np.asarray(x,dtype=t) for x,t in ((ids,np.int64),(areas,np.float64),(xs,np.float64),(ys,np.float64)))


def raster(path):
    with Path(path).open('rb') as f: header=f.read(52)
    if len(header)!=52:raise ValueError(f'Short IDF header: {path}')
    magic,nx,ny=struct.unpack('<3i',header[:12])
    if magic!=1271 or not (0<nx<=5000 and 0<ny<=5000):raise ValueError(f'Unsupported IDF: {path}')
    xmin,xmax,ymin,ymax,_,_,nodata=struct.unpack('<7f',header[12:40])
    dx,dy=struct.unpack('<2f',header[44:52])
    if header[40:42]!=b'\x00\x00' or dx<=0 or dy<=0:raise ValueError(f'Unsupported geometry IDF: {path}')
    if not np.all(np.isfinite([xmin,xmax,ymin,ymax,dx,dy])) or abs(nx*dx-(xmax-xmin))>.01 or abs(ny*dy-(ymax-ymin))>.01:
        raise ValueError(f'Invalid extent: {path}')
    if Path(path).stat().st_size<52+nx*ny*4:raise ValueError(f'Truncated IDF: {path}')
    values=np.memmap(path,mode='r',dtype='<f4',offset=52,shape=(ny,nx))
    return (nx,ny,xmin,ymax,dx,dy),nodata,values


def sample_xy(geo,x,y):
    nx,ny,xmin,ymax,dx,dy=geo
    cf=(x-xmin)/dx-.5; rf=(ymax-y)/dy-.5
    cc=np.rint(cf).astype(np.int64);rr=np.rint(rf).astype(np.int64)
    good=(abs(cf-cc)<.001)&(abs(rf-rr)<.001)&(cc>=0)&(cc<nx)&(rr>=0)&(rr<ny)
    if not good.all():raise ValueError(f'Raster does not contain {int((~good).sum())} SVAT cell centres; examples {np.flatnonzero(~good)[:5].tolist()}')
    return rr,cc


def source_index(root):
    """Bind each of seven names to ONE folder; detect duplicates and missing days."""
    root=Path(root)
    folders={p.name.casefold():p for p in root.iterdir() if p.is_dir()}
    indexes={}
    for var in VARIABLES:
        folder=folders.get(var)
        if folder is None:raise FileNotFoundError(f'Cannot find MetaSWAP source folder {root/var}')
        rx=re.compile(re.escape(var)+r'_((?:19|20)\d{6})(?:\d{6})?_l1\.idf$',re.I)
        idx={}
        for file in folder.iterdir():
            if not file.is_file():continue
            m=rx.fullmatch(file.name)
            if not m:continue
            stamp=m[1]
            if stamp in idx:raise ValueError(f'Duplicate {var} for {stamp}: {idx[stamp]} and {file}')
            idx[stamp]=file
        indexes[var]=idx
    return indexes


def evaluate(files, ids, areas, xs, ys,exception_id=EXCEPTION_SVAT):
    """Return seven-term residual per SVAT, preserving raw signs and unknowns."""
    arrs=[];hashes={};covers={};stats={}
    for var,path in files.items():
        geo,nodata,data=raster(path)
        rr,cc=sample_xy(geo,xs,ys)
        vals=np.asarray(data[rr,cc],dtype=np.float64)
        valid=np.isfinite(vals)&(vals!=nodata)&(np.abs(vals)<1e35)
        arrs.append(vals);covers[var]=valid
        hashes[var]=sha(path)
        stats[var]={'valid_svat_count':int(valid.sum()),'valid_area_m2':float(areas[valid].sum()),
                    'volume_m3':float(np.dot(areas[valid],vals[valid])) if valid.all() else None,
                    'source_file':str(path),'sha256':hashes[var]}
    complete=np.logical_and.reduce(list(covers.values()))
    # NoData is not zero: only compute sums on fully covered members.
    raw=np.full(len(ids),np.nan,dtype=np.float64)
    raw[complete]=np.sum(np.asarray(arrs)[:,complete],axis=0)
    residual=-raw
    eligible=complete&(ids!=exception_id)
    exc=complete&(ids==exception_id)
    signed=float(np.dot(residual[eligible],areas[eligible]))
    absvol=float(np.dot(np.abs(residual[eligible]),areas[eligible]))
    out={'valid_svat_count':int(complete.sum()),'valid_area_m2':float(areas[complete].sum()),
         'eligible_svat_count':int(eligible.sum()),'eligible_area_m2':float(areas[eligible].sum()),
         'excluded_exception_svat':int(exception_id),
         'exception_covered':bool(exc.any()),
         'exception_seven_term_residual_m3':float(np.dot(residual[exc],areas[exc])) if exc.any() else None,
         'seven_term_signed_residual_m3_ex_exception':signed,
         'seven_term_abs_residual_m3_ex_exception':absvol,
         'seven_term_mae_mm_ex_exception':1000*absvol/float(areas[eligible].sum()) if eligible.any() else None,
         'seven_term_residual_max_abs_mm_ex_exception':float(np.max(np.abs(residual[eligible]))*1000) if eligible.any() else None,
         'component_details':stats,
         'complete':bool(complete.all()),
         'incomplete_svat_count':int((~complete).sum())}
    return out,residual,complete


def run(args):
    if args.from_year>args.to_year:raise ValueError('Bad period')
    ids,areas,xs,ys=read_area(args.area)
    idx=source_index(args.root)
    periods=list(decades(args.from_year,args.to_year))
    for d in periods:
        for var in VARIABLES:
            if d['date_end'] not in idx[var]:raise FileNotFoundError(f'Missing {var}, decade {d["date_end"]}')
    args.out.mkdir(parents=True,exist_ok=True)
    config={'schema':'WB10-1','period':f'{args.from_year}-{args.to_year}',
            'area':str(args.area),'area_sha256':sha(args.area),
            'root':str(args.root),'variables':list(VARIABLES),
            'sign':'original + is incoming; ET negative; decStot source sign',
            'balance_formula':'seven_term_vcr=-sum(decStot,Pm,Pssw,Psgw,ETact,qrun,qmodf)',
            'qdr':'zero by LWKM owner project decision',
            'qspgw':'not supplied; only SVAT 207543 is eligible for MODFLOW layer-1 exception',
            'full_closure_claim':False,
            'unit':'m3/m2 per calendar decade',
            'expected_svats':EXPECTED_SVATS}
    identity=args.out/'identity.json'
    if identity.exists() and json.loads(identity.read_text(encoding='utf8'))!=config:
        raise ValueError('Output directory belongs to different source settings; choose a new output folder')
    if not identity.exists():atomic_json(identity,config)
    resultfile=args.out/'decades.csv'
    names=['period','year','date_start','date_end','days','complete','valid_svat_count','incomplete_svat_count',
           'eligible_svat_count','seven_term_signed_residual_m3_ex_exception',
           'seven_term_abs_residual_m3_ex_exception','seven_term_mae_mm_ex_exception',
           'seven_term_residual_max_abs_mm_ex_exception','exception_seven_term_residual_m3',
           'qmodf_m3','decstot_m3','pm_m3','pssw_m3','psgw_m3','etact_m3','qrun_m3','source_receipt_sha256']
    prev={}
    if resultfile.exists():
        with resultfile.open('r',encoding='utf-8',newline='') as f:
            prev={r['period']:r for r in csv.DictReader(f)}
    annual={} # accumulate small nation summaries; year-specific per-SVAT annual outputs are not materialized by default
    processed=0;reused=0
    for d in periods:
        if args.limit and processed+reused>=args.limit:break
        period=d['period']; files={v:idx[v][d['date_end']] for v in VARIABLES}
        receipt=args.out/'receipts'/f'{period}.json'
        hashes={v:sha(path) for v,path in files.items()}
        if receipt.exists() and period in prev:
            meta=json.loads(receipt.read_text(encoding='utf8'))
            if meta.get('source_sha256')==hashes and meta.get('identity_sha256')==sha(identity):
                reused+=1;print('REUSED',period,flush=True);continue
            raise ValueError(f'Existing checkpoint differs for {period}; choose a new output folder')
        if receipt.exists() or period in prev:raise ValueError(f'Partial checkpoint for {period}; stop safely')
        result,residual,complete=evaluate(files,ids,areas,xs,ys)
        # Save all SVAT residuals for pilot 2020 by default; annual aggregation is separate future task.
        if args.save_svat and complete.all():
            folder=args.out/'svat_residuals';folder.mkdir(exist_ok=True)
            dest=folder/f'{period}.npz';temp=folder/f'{period}.partial.npz'
            np.savez_compressed(temp,svat_id=ids,residual_m3_m2=residual,area_m2=areas)
            temp.replace(dest)
            result['svat_residual_file']=str(dest);result['svat_residual_sha256']=sha(dest)
        simple={**d,'complete':int(result['complete']),
                'valid_svat_count':result['valid_svat_count'],
                'incomplete_svat_count':result['incomplete_svat_count'],
                'eligible_svat_count':result['eligible_svat_count'],
                **{k:result[k] for k in ('seven_term_signed_residual_m3_ex_exception','seven_term_abs_residual_m3_ex_exception','seven_term_mae_mm_ex_exception','seven_term_residual_max_abs_mm_ex_exception','exception_seven_term_residual_m3')},
                **{{'bdgqmodf':'qmodf_m3','bdgdecstot':'decstot_m3','bdgpm':'pm_m3','bdgpssw':'pssw_m3','bdgpsgw':'psgw_m3','bdgetact':'etact_m3','bdgqrun':'qrun_m3'}[v]:result['component_details'][v]['volume_m3'] for v in VARIABLES}}
        receipt.parent.mkdir(exist_ok=True)
        meta={'period':period,'identity_sha256':sha(identity),'source_sha256':hashes,'results':result}
        atomic_json(receipt,meta)
        simple['source_receipt_sha256']=sha(receipt)
        prev[period]=simple;atomic_csv(resultfile,[prev[k] for k in sorted(prev)],names)
        processed+=1
        print('DONE',period,'covered',result['valid_svat_count'],'seven-term MAE mm',round(result['seven_term_mae_mm_ex_exception'],7),flush=True)
    # Recreate annual only for years with all 36 complete decades.
    year_rows=[]
    for year in range(args.from_year,args.to_year+1):
        vals=[prev.get(d['period']) for d in periods if d['year']==year]
        if len(vals)!=36 or any(v is None for v in vals):continue
        if any(int(v['complete'])!=1 for v in vals):continue
        row={'year':year,'decades':36,'days':sum(int(v['days']) for v in vals)}
        for key in ['seven_term_signed_residual_m3_ex_exception','seven_term_abs_residual_m3_ex_exception',
                    'qmodf_m3','decstot_m3','pm_m3','pssw_m3','psgw_m3','etact_m3','qrun_m3']:
            row[key]=sum(float(v[key]) for v in vals)
        # area-weighted MAE across all years is total abs volume / area. Annual mm, not average decade mm.
        row['seven_term_abs_residual_mm_year_ex_exception']=1000*row['seven_term_abs_residual_m3_ex_exception']/float(areas[ids!=EXCEPTION_SVAT].sum())
        year_rows.append(row)
    if year_rows:atomic_csv(args.out/'years.csv',year_rows,list(year_rows[0]))
    climate=[r for r in year_rows if 1991<=r['year']<=2020]
    if len(climate)==30:
        fields=['seven_term_signed_residual_m3_ex_exception','seven_term_abs_residual_m3_ex_exception',
                'qmodf_m3','decstot_m3','pm_m3','pssw_m3','psgw_m3','etact_m3','qrun_m3']
        report={'period':'1991-2020','years':30,'decades':1080,'status':'SEVEN_TERM_DIAGNOSTIC_NOT_FULL_CLOSURE',
                'annual_mean_m3':{k:sum(float(r[k]) for r in climate)/30 for k in fields},
                'total_m3':{k:sum(float(r[k]) for r in climate) for k in fields},
                'exception_svat':EXCEPTION_SVAT,'missing_qspgw':True}
        atomic_json(args.out/'climate_1991_2020.json',report)
    atomic_json(args.out/'status.json',{'status':'SEVEN_TERM_DIAGNOSTIC_NOT_FULL_CLOSURE',
        'expected_decades':len(periods),'processed_decades':len(prev),'created_this_run':processed,'reused_this_run':reused,
        'complete_decades':sum(int(v['complete'])==1 for v in prev.values()),
        'exception_svat':EXCEPTION_SVAT,'missing_term':'qspgw','qdr_zero_owner_decision':True,
        'complete_years':[r['year'] for r in year_rows]})


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=METASWAP)
    p.add_argument('--area',type=Path,default=AREA)
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'uitvoer_wb10')
    p.add_argument('--from-year',type=int,default=2020)
    p.add_argument('--to-year',type=int,default=2020)
    p.add_argument('--limit',type=int,default=0)
    p.add_argument('--save-svat',action='store_true',help='Save compressed SVAT residual for every decade, potentially very large')
    a=p.parse_args()
    try:run(a)
    except Exception as exc:
        print('WB10 STOP:',exc,file=sys.stderr);sys.exit(2)

if __name__=='__main__':main()
