#!/usr/bin/env python3
"""Produce 1991-2020 original MetaSWAP BDGQMODF mean depth per SVAT.

Read the already validated signed source CSV for IDs/coords; never reparse
area_svat.inp. Standalone run with yearly checkpoints and source fingerprints.
"""
import argparse,csv,hashlib,json,re,sys
from pathlib import Path
import numpy as np
import wb10_reader as w
BASE=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')/'LWKM_run_resultaten_totaal'
VERSION='FRANK_QMODF_V01_SIGNED_20261106'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def load_coordinates(path):
 ids=[];areas=[];xx=[];yy=[]
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f);required={'SVAT','Opp_svat_m2','X_RD_m','Y_RD_m'}
  if not required<=set(r.fieldnames or []):raise ValueError('Signed CSV mist: '+str(required-set(r.fieldnames or [])))
  for row in r:
   ids.append(int(row['SVAT']));areas.append(float(row['Opp_svat_m2']));xx.append(float(row['X_RD_m']));yy.append(float(row['Y_RD_m']))
 ids=np.array(ids,dtype=np.int64);area=np.array(areas);x=np.array(xx);y=np.array(yy)
 if len(ids)!=645582 or len(set(ids.tolist()))!=len(ids):raise ValueError('SVAT-ID dekking of uniciteit onjuist')
 if not (np.isfinite(area).all() and np.isfinite(x).all() and np.isfinite(y).all() and (area>0).all()):raise ValueError('Ongeldige ruimtelijke velden')
 return ids,area,x,y

def index(root):
 folders=[p for p in root.iterdir() if p.is_dir() and p.name.lower()=='bdgqmodf']
 if len(folders)!=1:raise ValueError('bdgqmodf map ontbreekt of is dubbel: '+str(root))
 pattern=re.compile(r'bdgqmodf_((?:19|20)\d{6})(?:\d{6})?_l1\.idf',re.I)
 files={}
 for p in folders[0].iterdir():
  m=pattern.fullmatch(p.name)
  if m:
   if m[1] in files:raise ValueError('Dubbele qmodf datum '+m[1])
   files[m[1]]=p
 for d in w.decades(1991,2020):
  if d['date_end'] not in files:raise FileNotFoundError('QModF-IDF ontbreekt: '+d['date_end'])
 return files

def annual(year,files,ids,x,y,out,signed_hash):
 sources=[files[d['date_end']] for d in w.decades(year,year)]
 meta=[]
 for p in sources:
  s=p.stat();meta.append([str(p),s.st_size,s.st_mtime_ns])
 signature=hashlib.sha256(json.dumps([VERSION,signed_hash,meta]).encode()).hexdigest()
 cache=out/'cache'/f'QMODF_{year}.npz';receipt=out/'cache'/f'QMODF_{year}.json'
 if cache.exists() or receipt.exists():
  if not (cache.exists() and receipt.exists()):raise ValueError('Onvolledige cache '+str(cache))
  info=json.loads(receipt.read_text(encoding='utf8'))
  if info.get('signature')!=signature or info.get('sha256')!=sha(cache):raise ValueError('Bron/cache gewijzigd: '+str(cache))
  with np.load(cache) as data:
   if not np.array_equal(data['svat'],ids):raise ValueError('Cache verkeerde SVAT-populatie')
   return data['totals'].copy(),data['valid'].astype(bool)
 vals=np.zeros(len(ids),dtype=np.float64);valid=np.ones(len(ids),bool)
 for date,p in zip(w.decades(year,year),sources):
  geo,nodata,grid=w.raster(p);rr,cc=w.sample_xy(geo,x,y)
  v=np.asarray(grid[rr,cc],dtype=np.float64)
  ok=np.isfinite(v)&(v!=nodata)&(np.abs(v)<1e35)
  valid &= ok;vals+=np.where(ok,v,0)
 out.joinpath('cache').mkdir(parents=True,exist_ok=True)
 tmp=cache.with_suffix('.partial.npz');np.savez_compressed(tmp,svat=ids,totals=vals,valid=valid.astype(np.uint8));tmp.replace(cache)
 receipt.write_text(json.dumps({'year':year,'signature':signature,'sha256':sha(cache),'valid_svats':int(valid.sum())},indent=2),encoding='utf8')
 print('QMODF JAAR',year,'dekking',int(valid.sum()),flush=True)
 return vals,valid

def run(a):
 for p in (a.signed,a.root):
  if not p.exists():raise FileNotFoundError(str(p))
 ids,area,x,y=load_coordinates(a.signed);files=index(a.root)
 if a.check_only:
  print('OK QMODF 1080 bron-IDF, 645582 SVATs; gereed voor extractie');return
 a.out.mkdir(parents=True,exist_ok=True)
 src_hash=sha(a.signed);total=np.zeros(len(ids));valid=np.ones(len(ids),bool)
 for year in range(1991,2021):
  v,mask=annual(year,files,ids,x,y,a.out,src_hash);total+=v;valid &=mask
 output=a.out/'FRANK_SVAT_QMODF_1991_2020.csv';part=output.with_suffix('.partial')
 with part.open('w',newline='',encoding='utf8') as f:
  wr=csv.writer(f);wr.writerow(['SVAT','QModF_signed_mm_j','QModF_volledig'])
  for i,sv in enumerate(ids):wr.writerow([int(sv),format(float(total[i]*1000/30),'.12g') if valid[i] else '',int(valid[i])])
 part.replace(output)
 manifest={'status':'COMPLETE' if valid.all() else 'INCOMPLETE','svats':len(ids),'valid_svats':int(valid.sum()),'period':'1991-2020','source':'bdgqmodf signed m3/m2 per decade','unit':'mm/year average','not_an_independent_overall_flux':True,'file':str(output),'sha256':sha(output)}
 (a.out/'MANIFEST_QMODF.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
 print('GEREED',output,manifest['valid_svats'],'volledig')

def main():
 p=argparse.ArgumentParser();p.add_argument('--signed',type=Path,default=BASE/'frank_export'/'MSW_SOURCE_SIGNED_1991_2020.csv');p.add_argument('--root',type=Path,default=BASE/'metaswap');p.add_argument('--out',type=Path,default=BASE/'frank_export_qmodf_v01');p.add_argument('--check-only',action='store_true')
 try:run(p.parse_args())
 except Exception as exc:print('STOP QMODF:',exc,file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
