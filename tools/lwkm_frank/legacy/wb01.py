"""LWKM WB01: inventory and daily raw MODFLOW layer-1 budget accounting.
No interpretation of unverified budget signs, nor invented storage closure.
"""
import argparse, csv, datetime as dt, hashlib, json, pathlib, re, struct, sys
import numpy as np
ROOT=pathlib.Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow')
ROLES=('qlat','flf','ghb','wel','drn','riv','bnd','sto','chd','rch','evt','ets','sfr','lak','uzf')
# These are known file conventions. Other file names must be reviewed before admission.
RX=re.compile(r'(?i)^bdg([a-z0-9]+)_((?:19|20)\d{6})(?:\d{6})?_l1\.idf$|^BDGQLAT_((?:19|20)\d{6})\.IDF$',re.I)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def read_idf(path):
    with open(path,'rb') as f:head=f.read(52)
    if len(head)!=52:raise ValueError('Short IDF header '+str(path))
    magic,nx,ny=struct.unpack('<iii',head[:12]);
    if magic!=1271 or min(nx,ny)<=0:raise ValueError('Unqualified IDF format '+str(path))
    xmin,xmax,ymin,ymax,_,_,nodata=struct.unpack('<7f',head[12:40])
    dx,dy=struct.unpack('<ff',head[44:52]);equidistant,topbot=head[40:42]
    if equidistant or topbot or dx<=0 or dy<=0:raise ValueError('Unqualified geometry '+str(path))
    if pathlib.Path(path).stat().st_size<52+4*nx*ny:raise ValueError('Truncated IDF '+str(path))
    a=np.memmap(path,dtype='<f4',offset=52,shape=(ny,nx),mode='r')
    valid=np.isfinite(a)&(a!=nodata)
    return (nx,ny,xmin,xmax,ymin,ymax,dx,dy), a, valid

def scan(root):
    found={r:{} for r in ROLES}; duplicates=[]; unmatched=[]
    for directory in [root/'bdgqlat_reconstructed'] + [root/('bdg'+r) for r in ROLES if r!='qlat']:
        if not directory.exists():continue
        for p in directory.rglob('*'):
            if not p.is_file() or p.suffix.lower()!='.idf':continue
            m=RX.match(p.name)
            if not m:
                if len(unmatched)<100:unmatched.append(str(p))
                continue
            role=(m.group(1) or 'qlat').lower(); stamp=m.group(2) or m.group(3)
            if role not in found:continue
            if stamp in found[role]:duplicates.append([role,stamp,str(found[role][stamp]),str(p)])
            else:found[role][stamp]=p
    return found,duplicates,unmatched

def date_range(a,b):
    start,end=dt.date.fromisoformat(a),dt.date.fromisoformat(b)
    if start>end or start<dt.date(1970,1,1) or end>dt.date(2022,12,31):raise ValueError('Date range outside 1970-2022')
    d=start
    while d<=end:
        yield d.strftime('%Y%m%d');d+=dt.timedelta(days=1)

def write_csv(path,rows,fields):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=pathlib.Path,default=ROOT)
    p.add_argument('--output',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent/'uitvoer')
    p.add_argument('--start',default='1970-01-01');p.add_argument('--end',default='2022-12-31')
    p.add_argument('--inventory-only',action='store_true')
    p.add_argument('--require-qlat',action='store_true',help='fail if any QLAT day missing')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    days=list(date_range(a.start,a.end));found,dupes,unmatched=scan(a.root)
    stats=[]
    for role,series in found.items():
        available=set(series);missing=[d for d in days if d not in available]
        stats.append(dict(role=role,days_found=len(available),days_in_period=len(available.intersection(days)),days_missing=len(missing),first_missing=';'.join(missing[:10]),sample=str(next(iter(series.values()),''))))
    write_csv(a.output/'inventory.csv',stats,['role','days_found','days_in_period','days_missing','first_missing','sample'])
    (a.output/'inventory_details.json').write_text(json.dumps({'duplicates':dupes[:100],'unmatched_examples':unmatched,'period':[a.start,a.end]},indent=2),encoding='utf8')
    if dupes:raise ValueError('Duplicate source files: inspect inventory_details.json')
    if a.inventory_only:print('INVENTARISATIE GEREED: '+str(a.output));return
    missing=[d for d in days if d not in found['qlat']]
    if missing and a.require_qlat:raise ValueError(f'{len(missing)} QLAT days missing, first {missing[:5]}')
    # Daily raw budgets are NOT a closed water balance. These reflect source signs.
    # Geometry must exactly match QLAT before combining; no resampling.
    daily=[]; reference=None
    for ix,day in enumerate(days):
        if day not in found['qlat']:continue
        row={'date':day}
        ref,_,_=read_idf(found['qlat'][day]);reference=ref if reference is None else reference
        if ref!=reference:raise ValueError('QLAT geometry changed '+day)
        for role in ROLES:
            f=found[role].get(day)
            if not f:row[role+'_raw_m3_day']='';continue
            geo,data,valid=read_idf(f)
            if geo!=reference:raise ValueError(f'{role} geometry differs on {day}; do not resample')
            # NoData must not contribute. Report coverage for quality inspection.
            row[role+'_raw_m3_day']=format(float(np.sum(data[valid],dtype=np.float64)),'.12g')
            row[role+'_valid_cells']=int(valid.sum())
        daily.append(row)
        if (ix+1)%100==0:print(f'{day} ({ix+1}/{len(days)})',flush=True)
    fields=['date']+[v for role in ROLES for v in (role+'_raw_m3_day',role+'_valid_cells')]
    write_csv(a.output/'daily_source_signed_totals.csv',daily,fields)
    years=[]
    for year in sorted({r['date'][:4] for r in daily}):
        subset=[r for r in daily if r['date'].startswith(year)]
        row={'year':year,'days_qlat':len(subset)}
        for role in ROLES:
            vals=[float(r[role+'_raw_m3_day']) for r in subset if r.get(role+'_raw_m3_day') not in ('',None)]
            row[role+'_raw_m3']=sum(vals) if vals else ''
            row[role+'_days']=len(vals)
        years.append(row)
    write_csv(a.output/'annual_source_signed_totals.csv',years,['year','days_qlat']+[v for r in ROLES for v in (r+'_raw_m3',r+'_days')])
    (a.output/'STATUS.txt').write_text('RESEARCH INVENTORY AND SOURCE-SIGNED TOTALS ONLY. No physical budget closure; no MODFLOW storage, MetaSWAP coupling or verified signs for other packages. QLAT per-cell IDFs stay authoritative.\n',encoding='utf8')
    print('GEREED: '+str(a.output))
if __name__=='__main__':
    try:main()
    except Exception as e:print('WB01 STOP: '+str(e),file=sys.stderr);sys.exit(2)
