#!/usr/bin/env python3
"""LWKM/Frank: controlled direct LHM MetaSWAP->SVAT hydrology export.

Only variables with a verified source are populated. The scope is a time-window
mean of *original* MetaSWAP decade IDFs, not a SWAP water balance closure.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, sys
from pathlib import Path
import numpy as np
import wb10_reader as w

BASE=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
ROOT=BASE/'LWKM_run_resultaten_totaal'/'metaswap'
AREA=Path(r'E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp')
ROLES=('bdgpm','bdgetact','bdgqrun','bdgdecstot','bdgpssw','bdgpsgw')
# Verified source sign: ET and qrun are negative outflows in the original budgets.
# Positive output magnitudes are derived only when records respect this contract.
FRANK_FIELDS=['SVAT','Opp_svat','Landuse','LU4','LU2','Bodem370','Pawn21','Grondsoort4','Grondsoort2',
 'Neerslag','Beregening','Evapotranspiratie','Verdamping gewas','Verdamping interceptie','Verdamping bodem',
 'Oppervlakkige afstroming','Ontwatering','Fldrou1','Fldrou2','Fldrou3','Fldrou4','Fldrou5',
 'Infiltratie','Fldrin1','Fldrin2','Fldrin345','Netto kwel/wegzijging','Wegzijging','Kwel',
 'Bergingsverandering','Gtnr','GLG','GHG','GG','Dynamiek','Kwelklasse 4',
 'Indicator vervangen Svats','N ???','Gebied']
# Source names are *explicit*: no inference from partly matching or historical names.
# This is an extensible list of optional static ASCII grids with exact semantic approvals.
STATIC_FIELDS={'Infiltratie':'LHM_uitvoer/filter/Riv_infiltratie_1991-2020_sum.asc'}

def checksum(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for buf in iter(lambda:f.read(4*1024*1024),b''):h.update(buf)
 return h.hexdigest()

def write_json(path,content):
 tmp=path.with_suffix(path.suffix+'.partial')
 tmp.write_text(json.dumps(content,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 tmp.replace(path)

def period_index(root,years):
 # Unlike original WB10 requiring 7 variables, only open the 6 needed fields.
 result={}
 for role in ROLES:
  folder=root/role
  if not folder.is_dir():raise FileNotFoundError(f'MetaSWAP directory ontbreekt: {folder}')
  import re
  pat=re.compile(r'^'+re.escape(role)+r'_((?:19|20)\d{6})(?:\d{6})?_l1\.idf$',re.I)
  seen={}
  for p in folder.iterdir():
   m=pat.fullmatch(p.name) if p.is_file() else None
   if m:
    if m[1] in seen:raise ValueError(f'Dubbele IDF {role} {m[1]}: {p} en {seen[m[1]]}')
    seen[m[1]]=p
  result[role]=seen
 for year in years:
  missing=[]
  for d in w.decades(year,year):
   for role in ROLES:
    if d['date_end'] not in result[role]:missing.append(f'{role}:{d["date_end"]}')
  if missing:raise FileNotFoundError(f'{year}: {len(missing)} ontbrekende decade-IDFs, eerste {missing[:8]}')
 return result

def scan_rasters(paths, xs,ys, expected_n):
 # Raster can be different from LHM domain; strict spatial matching.
 totals={role:np.zeros(expected_n,np.float64) for role in ROLES}
 mask=np.ones(expected_n,dtype=bool)
 for role,path in paths.items():
  geo,nodata,grid=w.raster(path)
  rr,cc=w.sample_xy(geo,xs,ys)
  raw=np.asarray(grid[rr,cc],dtype=np.float64)
  valid=np.isfinite(raw)&(raw!=nodata)&(np.abs(raw)<1e35)
  mask &= valid
  totals[role]+=np.where(valid,raw,0.)
 return totals,mask

def accumulate(year, catalog, xs,ys, outdir, ids):
 cache=outdir/'cache'/f'MSW_{year}.npz'
 receipt=outdir/'cache'/f'MSW_{year}.json'
 if cache.exists() or receipt.exists():
  if not cache.exists() or not receipt.exists():raise RuntimeError(f'Incompleet checkpoint {year}; kies nieuwe uitvoermap')
  info=json.loads(receipt.read_text(encoding='utf-8'))
  if info.get('sha256')!=checksum(cache):raise RuntimeError(f'Checkpoint gewijzigd: {cache}')
  if info.get('year')!=year or info.get('svats')!=len(ids):raise RuntimeError('Checkpoint heeft ander jaar of populatie')
  # Cache reuse allowed only for unchanged sources: names, sizes and mtime are a cheap fingerprint,
  # *not* cryptographic source verification. Strict source checks optional below.
  current=year_inputs(year,catalog)
  if info.get('input_signature')!=signature(current):raise RuntimeError(f'Bronbestanden voor {year} gewijzigd; nieuwe uitvoermap nodig')
  with np.load(cache) as z:
   if not np.array_equal(z['svat_id'],ids):raise RuntimeError('SVAT IDs verschillen van cached jaar')
   return ({r:z[r].copy() for r in ROLES},z['complete'].astype(bool))
 files=year_inputs(year,catalog)
 sums={r:np.zeros(len(ids),np.float64) for r in ROLES}
 complete=np.ones(len(ids),bool)
 for ix,d in enumerate(w.decades(year,year),1):
  for role in ROLES:
   src=files[f'{role}:{d["date_end"]}']
   geo,nodata,grid=w.raster(src)
   rr,cc=w.sample_xy(geo,xs,ys)
   raw=np.asarray(grid[rr,cc],dtype=np.float64)
   valid=np.isfinite(raw)&(raw!=nodata)&(np.abs(raw)<1e35)
   complete &= valid
   sums[role] += np.where(valid,raw,0.)
  if ix%12==0:print(f'{year}: {ix}/36 decades',flush=True)
 cache.parent.mkdir(parents=True,exist_ok=True)
 tmp=cache.with_suffix('.partial.npz')
 np.savez_compressed(tmp,svat_id=ids,complete=complete.astype(np.uint8),**sums)
 tmp.replace(cache)
 write_json(receipt,dict(year=year,svats=len(ids),input_signature=signature(files),sha256=checksum(cache),
                         complete_svats=int(complete.sum()),source_count=len(files),
                         source_signature_note='name+size+mtime; geen cryptografisch per-IDF receipt'))
 return sums,complete

def year_inputs(year,catalog):
 return {f'{role}:{d["date_end"]}':catalog[role][d['date_end']]
         for d in w.decades(year,year) for role in ROLES}

def signature(files):
 items=[]
 for k,p in sorted(files.items()):
  st=p.stat();items.append((k,str(p),st.st_size,st.st_mtime_ns))
 return hashlib.sha256(json.dumps(items).encode()).hexdigest()

def read_ascii_grid(path,xs,ys):
 # ESRI ASCII grid in RD; no spatial interpolation. Unknown cells remain null.
 with path.open(encoding='utf-8-sig') as f:
  header={}
  while len(header)<6:
   line=f.readline()
   if not line:raise ValueError('ASCII header truncated')
   a=line.split()
   if len(a)!=2:raise ValueError('Malformed ASCII header')
   header[a[0].lower()]=float(a[1])
  if not {'ncols','nrows','cellsize','nodata_value'}<=header.keys():raise ValueError('ASC missing required headers')
  ncols=int(header['ncols']);nrows=int(header['nrows']);cell=header['cellsize']
  if not (1<=ncols<=10000 and 1<=nrows<=10000 and cell>0):raise ValueError('ASC geometry invalid')
  left=header.get('xllcorner',header.get('xllcenter',float('nan') )-cell/2)
  bottom=header.get('yllcorner',header.get('yllcenter',float('nan'))-cell/2)
  if not np.isfinite(left+bottom):raise ValueError('ASC missing origin')
  data=np.loadtxt(f,dtype=np.float64)
  if data.shape!=(nrows,ncols):raise ValueError('ASC data dimensions mismatch')
  col=np.rint((xs-left)/cell-.5).astype(np.int64)
  row=np.rint((bottom+nrows*cell-ys)/cell-.5).astype(np.int64)
  if ((col<0)|(col>=ncols)|(row<0)|(row>=nrows)).any():
   raise ValueError('ASC does not cover all SVAT positions')
  sampled=data[row,col];nodata=header['nodata_value']
  return np.where((sampled==nodata)|(~np.isfinite(sampled)),np.nan,sampled)

def execute(args):
 if args.from_year>args.to_year or args.from_year<1970 or args.to_year>2022:
  raise ValueError('Jaartal buiten LHM 1970–2022')
 years=list(range(args.from_year,args.to_year+1))
 args.out.mkdir(parents=True,exist_ok=True)
 ids,areas,xs,ys=w.read_area(args.area)
 catalog=period_index(args.root,years)
 all_sums={role:np.zeros(len(ids),np.float64) for role in ROLES}
 complete=np.ones(len(ids),bool)
 for yr in years:
  arr,valid=accumulate(yr,catalog,xs,ys,args.out,ids)
  for role in ROLES:all_sums[role]+=arr[role]
  complete &= valid
 n_years=len(years)
 scale=1000.0/n_years
 # Source sign conventions are explicit. Leave original signed terms in a separate audit CSV.
 positive={
  'Neerslag': all_sums['bdgpm']*scale,
  'Evapotranspiratie':-all_sums['bdgetact']*scale,
  'Oppervlakkige afstroming':-all_sums['bdgqrun']*scale,
 }
 # No automatically invented GHG, GLG, mean GW, drainage or irrigation.
 # River infiltration optional but only for 1991–2020, since source period is fixed.
 river=None;river_path=args.lhm_workspace/'LHM_uitvoer'/'filter'/'Riv_infiltratie_1991-2020_sum.asc'
 if args.from_year==1991 and args.to_year==2020 and river_path.is_file():
  river=read_ascii_grid(river_path,xs,ys)
 out=args.out/f'FRANK_LHM_SVAT_BASE_{args.from_year}_{args.to_year}.csv'
 aud=args.out/f'MSW_SOURCE_SIGNED_{args.from_year}_{args.to_year}.csv'
 missing={name:0 for name in FRANK_FIELDS}
 valid_counter=int(complete.sum())
 with out.open('w',encoding='utf-8',newline='') as f, aud.open('w',encoding='utf-8',newline='') as fa:
  wr=csv.DictWriter(f,fieldnames=FRANK_FIELDS,extrasaction='ignore');wr.writeheader()
  wa=csv.writer(fa);wa.writerow(['SVAT','Opp_svat_m2','X_RD_m','Y_RD_m','complete_source',*[r+'_signed_mm_per_year' for r in ROLES]])
  for i,sv in enumerate(ids):
   row={k:'' for k in FRANK_FIELDS};row['SVAT']=int(sv);row['Opp_svat']=format(float(areas[i]),'.12g')
   if complete[i]:
    for name,array in positive.items():row[name]=format(float(array[i]),'.12g')
    if river is not None and np.isfinite(river[i]):row['Infiltratie']=format(float(river[i]),'.12g')
   wr.writerow(row)
   wa.writerow([int(sv),float(areas[i]),float(xs[i]),float(ys[i]),int(complete[i]),
                *[format(float(all_sums[r][i]*scale),'.12g') if complete[i] else '' for r in ROLES]])
   for name in FRANK_FIELDS:
    if row[name]=='':missing[name]+=1
  
 manifest={
  'status':'SOURCE_BASELINE_NOT_ALL_FIELDS_AVAILABLE',
  'period':f'{args.from_year}-{args.to_year}', 'years':n_years,
  'expected_decades':36*n_years,'source_roles':list(ROLES),'qmodf_used':False,
  'original_svat_count':len(ids),'complete_source_svats':valid_counter,
  'area_file':str(args.area),'area_sha256':checksum(args.area),
  'metaswap_dir':str(args.root),'river_infiltration_path':str(river_path) if river is not None else None,
  'river_infiltration_semantics':'originele Riv_infiltratie_1991-2020_sum.asc, historische alias wegzijgingz',
  'unit_filled_hydro':'mm/jaar; gemiddelde over gekozen kalenderjaren',
  'signs':{'Neerslag':'+bdgpm','Evapotranspiratie':'-bdgetact','Oppervlakkige afstroming':'-bdgqrun',
           'source_audit':'originele modeltekens'},
  'not_derived':['GLG','GHG','GG','Dynamiek','Fldrou','Fldrin','beregening','ontwatering','kwel','grondsoorten','landgebruik'],
  'blank_count_by_field':missing,
  'source_sign_not_independent_balance':['bdgdecstot','bdgpssw','bdgpsgw'],
  'important':'Deels gevulde SVAT_BASE, geen zeven-term waterbalans, geen gekwalificeerde correctie/HRU selectie. NoData nooit nul.',
 }
 write_json(args.out/f'manifest_{args.from_year}_{args.to_year}.json',manifest)
 with (args.out/f'dekking_per_veld_{args.from_year}_{args.to_year}.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.writer(f);writer.writerow(['veld','gevuld','ontbrekend','populatie']);writer.writerows((name,len(ids)-missing[name],missing[name],len(ids)) for name in FRANK_FIELDS)
 print(f'GEREED {out}: {len(ids)} SVAT, complete bron {valid_counter}, {n_years} jaar')

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=ROOT)
 p.add_argument('--area',type=Path,default=AREA)
 p.add_argument('--lhm-workspace',type=Path,default=BASE)
 p.add_argument('--out',type=Path,default=BASE/'LWKM_run_resultaten_totaal'/'frank_export')
 p.add_argument('--from-year',type=int,default=2020)
 p.add_argument('--to-year',type=int,default=2020)
 p.add_argument('--check-only',action='store_true',help='Controleer 14-koloms area_svat en alle benodigde decade-IDF namen zonder hydrologische rasterberekening')
 args=p.parse_args(argv)
 if args.check_only:
  ids,areas,xs,ys=w.read_area(args.area)
  catalog=period_index(args.root,range(args.from_year,args.to_year+1))
  print(f'BRONCHECK OK: {len(ids)} SVATs, {36*(args.to_year-args.from_year+1)} decades, {len(ROLES)} MetaSWAP-variabelen, {sum(len(v) for v in catalog.values())} mogelijke IDFs in broncatalogus')
  return
 execute(args)
if __name__=='__main__':
 try:main()
 except Exception as e:
  print('STOP_FRANK_LHM:',e,file=sys.stderr);sys.exit(2)
