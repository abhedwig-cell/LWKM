#!/usr/bin/env python3
"""LWKM Frank: MetaSWAP evaporation components and irrigation, SVAT, 1991-2020.

Original IDF values are m3/m2 per *decade*, signed, on SVAT support. Read
once; accumulate source data per year with consistent NoData masks. No qmodf.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys
from pathlib import Path
import numpy as np
import wb10_reader as w

BASE = Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
ROOT = BASE/'LWKM_run_resultaten_totaal'/'metaswap'
AREA = Path(r'E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp')
OUT = BASE/'LWKM_run_resultaten_totaal'/'frank_export_aanvulling_v01'
VARS=('msw_Tact','msw_Eic','msw_Ebs','msw_Epd','msw_Esp')
VER='frank-msw-et-only-v02-20261106'
SIGNED=BASE/'LWKM_run_resultaten_totaal'/'frank_export'/'MSW_SOURCE_SIGNED_1991_2020.csv'


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def atomic_json(path,obj):
    tmp=path.with_suffix(path.suffix+'.partial')
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    tmp.replace(path)

def index_source(root,years):
    root=Path(root);folders={p.name.lower():p for p in root.iterdir() if p.is_dir()}
    index={}
    for role in VARS:
        folder=folders.get(role.lower())
        if folder is None:raise FileNotFoundError(f'Ontbrekende bronmap {root/role}')
        pat=re.compile(re.escape(role)+r'_([12]\d{7})(?:\d{6})?_l1\.idf',re.I)
        found={}
        for p in folder.iterdir():
            if not p.is_file():continue
            m=pat.fullmatch(p.name)
            if m:
                if m[1] in found:raise ValueError(f'Dubbele {role}/{m[1]}: {p} {found[m[1]]}')
                found[m[1]]=p
        index[role]=found
    missing=[]
    for d in w.decades(min(years),max(years)):
        for role in VARS:
            if d['date_end'] not in index[role]:missing.append((role,d['date_end']))
    if missing:raise FileNotFoundError(f'{len(missing)} ontbrekende bron-IDFs; eerste 12: {missing[:12]}')
    return index

def annual(year,index,ids,xs,ys,area_sha,out):
    base=out/'cache'/f'MSW_EXTRA_{year}'
    npz=base.with_suffix('.npz');receipt=base.with_suffix('.json')
    sources=[(role,d['date_end'],index[role][d['date_end']]) for d in w.decades(year,year) for role in VARS]
    sig=[]
    for role,date,path in sources:
        st=path.stat();sig.append([role,date,str(path),st.st_size,st.st_mtime_ns])
    signature=hashlib.sha256(json.dumps(sig,separators=(',',':')).encode()).hexdigest()
    if npz.exists() or receipt.exists():
        if not (npz.exists() and receipt.exists()):raise RuntimeError('Onvolledige jaarcache; gebruik nieuwe outputmap')
        info=json.loads(receipt.read_text('utf-8'))
        if info.get('version')!=VER or info.get('area_sha256')!=area_sha or info.get('source_signature')!=signature or info.get('cache_sha256')!=digest(npz):
            raise RuntimeError(f'Cache {year} is ongeldig; oude uitvoer niet hergebruiken')
        with np.load(npz) as data:
            if not np.array_equal(data['SVAT'],ids):raise RuntimeError('Jaarcache verkeerde SVAT-populatie')
            return {k:data[k].copy() for k in VARS},data['valid'].astype(bool)
    totals={k:np.zeros(len(ids),dtype=np.float64) for k in VARS}
    complete=np.ones(len(ids),dtype=bool)
    for j,d in enumerate(w.decades(year,year),1):
        for role in VARS:
            src=index[role][d['date_end']]
            geo,nodata,grid=w.raster(src)
            rr,cc=w.sample_xy(geo,xs,ys)
            vals=np.asarray(grid[rr,cc],dtype=np.float64)
            valid=np.isfinite(vals)&(vals!=nodata)&(np.abs(vals)<1e35)
            complete &= valid
            totals[role]+=np.where(valid,vals,0.)
        if j%12==0:print(f'{year}: {j}/36 decades',flush=True)
    out.joinpath('cache').mkdir(parents=True,exist_ok=True)
    temp=npz.with_suffix('.partial.npz')
    np.savez_compressed(temp,SVAT=ids,valid=complete.astype(np.uint8),**totals)
    temp.replace(npz)
    atomic_json(receipt,{'version':VER,'year':year,'area_sha256':area_sha,'source_signature':signature,'source_count':len(sources),'cache_sha256':digest(npz),'complete_svats':int(complete.sum()),'note':'source size+mtime signature; not per-IDF SHA256'})
    return totals,complete

def prior_irrigation(path,ids):
    required={'SVAT','complete_source','bdgpssw_signed_mm_per_year','bdgpsgw_signed_mm_per_year'}
    if not path.is_file():raise FileNotFoundError('Bestaande signed MetaSWAP bronexport niet aanwezig: '+str(path))
    prior={}
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not required.issubset(reader.fieldnames or []):raise ValueError('Signed MetaSWAP bronexport mist Psgw/Pssw kolommen')
        for row in reader:
            ident=int(row['SVAT'])
            if ident in prior:raise ValueError('Dubbele SVAT in bestaande signed export')
            prior[ident]=(float(row['bdgpsgw_signed_mm_per_year'])+float(row['bdgpssw_signed_mm_per_year'])
                          if row['complete_source']=='1' and row['bdgpsgw_signed_mm_per_year'] and row['bdgpssw_signed_mm_per_year'] else float('nan'))
    if set(prior)!=set(map(int,ids)):raise ValueError('Signed export heeft afwijkende SVAT-populatie')
    return np.asarray([prior[int(i)] for i in ids],dtype=np.float64)

def run(args):
    if args.start<1970 or args.end>2022 or args.end<args.start:raise ValueError('Ongeldige periode')
    years=list(range(args.start,args.end+1))
    ids,areas,xs,ys=w.read_area(args.area)
    index=index_source(args.root,years)
    if args.check_only:
        if not args.signed_baseline.is_file():raise FileNotFoundError('Bestaande Psgw/Pssw signed-CSV ontbreekt: '+str(args.signed_baseline))
        if args.check_et and not args.check_et.is_file():raise FileNotFoundError('ETact referentie-CSV ontbreekt: '+str(args.check_et))
        print(f'OK {len(ids)} SVATs, {36*len(years)} decades, {len(VARS)} bronnen, {36*len(years)*len(VARS)} IDFs');return
    args.out.mkdir(parents=True,exist_ok=True)
    area_sha=digest(args.area)
    sums={k:np.zeros(len(ids),dtype=np.float64) for k in VARS}
    complete=np.ones(len(ids),dtype=bool)
    for yr in years:
        annual_sums,valid=annual(yr,index,ids,xs,ys,area_sha,args.out)
        for k in VARS:sums[k]+=annual_sums[k]
        complete &= valid
    scale=1000/len(years) # m3/m2 per decade -> average mm/year
    raw={k:sums[k]*scale for k in VARS}
    irrigation=prior_irrigation(args.signed_baseline,ids)
    complete &= np.isfinite(irrigation)
    derived={
        'Verdamping_gewas_mm_j':-raw['msw_Tact'],
        'Verdamping_interceptie_mm_j':-(raw['msw_Eic']+raw['msw_Esp']),
        'Verdamping_bodem_en_plas_mm_j':-(raw['msw_Ebs']+raw['msw_Epd']),
        'Beregening_mm_j':irrigation,
        'ET_componentensom_mm_j':-(raw['msw_Tact']+raw['msw_Eic']+raw['msw_Ebs']+raw['msw_Epd']+raw['msw_Esp']),
    }
    if args.check_et:
        # Existing MetaSWAP total ETact should be compared without re-reading
        # source rasters. Input is the existing 1991-2020 Frank source CSV.
        et={}
        with args.check_et.open(newline='',encoding='utf-8-sig') as f:
            rd=csv.DictReader(f)
            if not {'SVAT','Evapotranspiratie'}<=set(rd.fieldnames or []):raise ValueError('ET check file columns missing')
            for row in rd:
                key=int(row['SVAT'])
                if key in et:raise ValueError('Dubbele SVAT in ET referentie')
                et[key]=float(row['Evapotranspiratie']) if row['Evapotranspiratie'] else np.nan
        if len(et)!=len(ids) or set(et)!=set(ids.tolist()):raise ValueError('ET reference SVAT set differs')
        ref=np.asarray([et[int(i)] for i in ids])
        derived['ET_verschil_tov_bdgETact_mm_j']=derived['ET_componentensom_mm_j']-ref
    headers=['SVAT','Opp_svat_m2','X_RD','Y_RD','volledig',
             *[f'{k}_signed_mm_j' for k in VARS],*derived.keys()]
    file=args.out/f'FRANK_SVAT_MSW_AANVULLING_{args.start}_{args.end}.csv'
    with file.open('w',newline='',encoding='utf-8') as f:
        wr=csv.writer(f);wr.writerow(headers)
        for i,id_ in enumerate(ids):
            wr.writerow([int(id_),format(float(areas[i]),'.12g'),format(float(xs[i]),'.12g'),format(float(ys[i]),'.12g'),int(complete[i]),
                         *[(format(float(raw[k][i]),'.12g') if complete[i] else '') for k in VARS],
                         *[(format(float(v[i]),'.12g') if complete[i] and np.isfinite(v[i]) else '') for v in derived.values()]])
    qa={'version':VER,'period':[args.start,args.end],'decades':36*len(years),'sources':list(VARS),'svats':len(ids),'complete_svats':int(complete.sum()),'incomplete_svats':int((~complete).sum()),'area_sha256':area_sha,'output_sha256':digest(file),'source_sign':'original signed MetaSWAP; evaporation source values generally negative; irrigation positive','unit':'mm/year mean; original m3/m2 per decade multiplied by 1000/Nyears','grouping':{'Verdamping_gewas':'-Tact','Verdamping_interceptie':'-(Eic+Esp)','Verdamping_bodem_en_plas':'-(Ebs+Epd)','Beregening':'Psgw+Pssw'},'et_reference':str(args.check_et) if args.check_et else None,'irrigation_source':str(args.signed_baseline),'irrigation_source_sha256':digest(args.signed_baseline),'warning':'NoData never replaced with zero. Output rows with incomplete source are blank for hydrological values.'}
    if args.check_et:
        dev=derived['ET_verschil_tov_bdgETact_mm_j']
        mask=complete&np.isfinite(dev)
        qa['et_diagnostic']={'valid':int(mask.sum()),'mae_mm_y':float(np.mean(np.abs(dev[mask]))) if mask.any() else None,'max_abs_mm_y':float(np.max(np.abs(dev[mask]))) if mask.any() else None,'gt_1_mm_y':int((np.abs(dev[mask])>1).sum())}
    atomic_json(args.out/f'MANIFEST_MSW_AANVULLING_{args.start}_{args.end}.json',qa)
    print('GEREED:',file,'aantal SVAT:',len(ids),'volledig:',int(complete.sum()),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--area',type=Path,default=AREA)
    p.add_argument('--out',type=Path,default=OUT)
    p.add_argument('--start',type=int,default=1991)
    p.add_argument('--end',type=int,default=2020)
    p.add_argument('--check-only',action='store_true')
    p.add_argument('--check-et',type=Path,default=None,help='Existing FRANK_LHM_SVAT_BASE_1991_2020.csv')
    p.add_argument('--signed-baseline',type=Path,default=SIGNED,help='Already exported Psgw and Pssw, signed mm/year; required')
    try:run(p.parse_args())
    except Exception as e:print('STOP:',str(e),file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
