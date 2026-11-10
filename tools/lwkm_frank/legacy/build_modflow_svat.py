#!/usr/bin/env python3
"""Frank LWKM: originele MODFLOW-laag-1-budgetten per SVAT-locatie.

Bronnen zijn originele DAG-budgetten, geen afgeleide MetaSWAP-qmodf. Alle
volumes komen uit een VOLLEDIGE MODFLOW-cel van 250x250 m. Aantal mm/jaar
betreft CEL-equivalent; niet delen door area_svat en niet optellen bij een
SVAT-specifieke waterbalans zonder gespecificeerde systeemgrens.
"""
from __future__ import annotations
import argparse, calendar, csv, datetime as dt, hashlib, json, sys
from pathlib import Path
import numpy as np
import wb10_reader as msw
import wb03_balance as mf
from wb01 import read_idf

BASE=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
ROOT=BASE/'LWKM_run_resultaten_totaal'/'modflow'
AREA=Path(r'E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp')
MASK=Path(r'E:\LHM_4.3.3\Data\2_Model_Input\modflow\bnd\ibound_l1.idf')
ROLES=('flf','qlat','wel','ghb', 'drn_sys1','drn_sys2','drn_sys3', 'riv_sys1','riv_sys2','riv_sys3','riv_sys4')
# Exact 16 hydrological values: 13 gross directional plus 3 signed terms.
FLUX_COLS=(
    *(f'RIV_SYS{i}_ONTWATERING_m3' for i in range(1,5)),
    *(f'RIV_SYS{i}_INFILTRATIE_m3' for i in range(1,5)),
    *(f'DRN_SYS{i}_ONTWATERING_m3' for i in range(1,4)),
    'FLF_KWEL_m3', 'FLF_WEGZIJGING_m3',
    'LAT_NETTO_m3','WEL_NETTO_m3','GHB_NETTO_m3',
)
SPLIT_ROLES=(
    *(f'riv_sys{i}_ontwatering' for i in range(1,5)),
    *(f'riv_sys{i}_infiltratie' for i in range(1,5)),
    *(f'drn_sys{i}_ontwatering' for i in range(1,4)),
    'flf_kwel','flf_wegzijging',
)
CACHE_FORMAT='v07_drn_positive_zero_with_audit_16_flux'

TOL=1e-6

def emit_json(p,value):
 p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_suffix(p.suffix+'.partial')
 temp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')
 temp.replace(p)

def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for buf in iter(lambda:f.read(4*1024*1024),b''):h.update(buf)
 return h.hexdigest()

def grid_indexes(geo,x,y):
 nx,ny,xmin,xmax,ymin,ymax,dx,dy=geo
 colf=(x-xmin)/dx-.5
 rowf=(ymax-y)/dy-.5
 col=np.rint(colf).astype(np.int64)
 row=np.rint(rowf).astype(np.int64)
 good=(abs(colf-col)<.001)&(abs(rowf-row)<.001)&(col>=0)&(col<nx)&(row>=0)&(row<ny)
 if not good.all():raise ValueError(f'{(~good).sum()} SVAT-centra vallen buiten of naast het MODFLOW-raster')
 return row,col

def _system_path(root, role, stamp):
 kind, number = role.split('_sys')
 if kind not in ('drn','riv') or not number.isdigit():
  raise ValueError(f'Onbekende systeemterm: {role}')
 i=int(number)
 if not (1 <= i <= (3 if kind=='drn' else 4)):
  raise ValueError(f'Onjuist systeemnummer: {role}')
 return root / ('bdg'+kind) / f'bdg{kind}_sys{i}_{stamp}000000_l1.IDF'

def get_one(root,role,stamp,geo):
 if role in ('qlat','flf','wel','ghb'):
  return mf.get_merged(root,role,stamp,geo)
 if role.startswith(('drn_sys','riv_sys')):
  return mf.get_mosaic([_system_path(root,role,stamp)],geo)
 raise ValueError(role)

def source_paths(root,role,stamp):
 if role in ('qlat','flf','wel','ghb'):
  return [mf.source(root,role,stamp)]
 if role.startswith(('drn_sys','riv_sys')):
  return [_system_path(root,role,stamp)]
 raise ValueError(role)

def all_days(year):
 d=dt.date(year,1,1)
 while d.year==year:
  yield d.strftime('%Y%m%d')
  d+=dt.timedelta(days=1)

def source_signature(root,year,roles):
 h=hashlib.sha256(); count=0
 for stamp in all_days(year):
  for role in roles:
   paths=source_paths(root,role,stamp)
   for p in paths:
    if not p.is_file():raise FileNotFoundError(f'{role} {stamp}: {p}')
    st=p.stat()
    h.update(f'{role}|{p}|{st.st_size}|{st.st_mtime_ns}\n'.encode('utf8'))
    count+=1
 return h.hexdigest(),count

def annual(year,root,roles,ids,rr,cc,geo,out,area_sha,ibound_sha):
 cache=out/'cache'/f'MF_{year}.npz'
 receipt=cache.with_suffix('.json')
 if cache.exists() != receipt.exists():raise RuntimeError(f'Onvolledig checkpoint voor {year}; gebruik nieuwe uitvoermap')
 sig,num=source_signature(root,year,roles)
 if receipt.exists():
  meta=json.loads(receipt.read_text(encoding='utf8'))
  if (meta.get('cache_format'),meta['source_signature'],meta['area_sha256'],meta['ibound_sha256'],meta['roles']) != (CACHE_FORMAT,sig,area_sha,ibound_sha,list(roles)):
   raise RuntimeError(f'Bron gewijzigd sinds checkpoint {year}; gebruik nieuwe uitvoermap')
  if hashfile(cache)!=meta['cache_sha256']:
   raise RuntimeError(f'Checkpoint hash gewijzigd voor {year}')
  with np.load(cache) as z:
   if not np.array_equal(z['SVAT'],ids):raise RuntimeError('SVAT-populatie gewijzigd sinds checkpoint')
   result={r:z[r].copy() for r in (*roles,*SPLIT_ROLES)}
   coverage={r:int(z['coverage_'+r]) for r in roles}
  print('HERGEBRUIK',year,flush=True)
  anomalies=meta.get('drn_positive_anomalies',[])
  return result,coverage,anomalies
 sums={role:np.zeros(len(ids),np.float64) for role in (*roles,*SPLIT_ROLES)}
 coverage={role:0 for role in roles}
 anomalies=[]
 for index,stamp in enumerate(all_days(year),1):
  for role in roles:
   field,available=get_one(root,role,stamp,geo)
   sampled=np.asarray(field[rr,cc],np.float64)
   valid=np.asarray(available[rr,cc],bool)&np.isfinite(sampled)
   if role in ('flf','qlat') and not valid.all():
    raise ValueError(f'{stamp}: {role.upper()} mist {int((~valid).sum())} SVAT-cellen')
   # For WEL/GHB and DRN/RIV, missing package cells mean zero stress, subject to source coverage reporting.
   # FLF and QLAT must have valid data at every SVAT cell.
   coverage[role]+=int(valid.sum())
   values=np.where(valid,sampled,0.)
   if role.startswith('drn_sys'):
    positive=values>0.
    if np.any(positive):
     # Audit physical cells as well as sampled SVATs (multiple SVATs may map to same cell).
     cell_ids=rr[positive].astype(np.int64)*int(geo[0])+cc[positive].astype(np.int64)
     uniq, first=np.unique(cell_ids,return_index=True)
     vpos=values[positive]
     anomalies.append(dict(year=year,date=stamp,role=role,
       positive_svat_count=int(len(vpos)),positive_cell_count=int(len(uniq)),
       positive_svat_sum_m3=float(vpos.sum()),
       positive_unique_cell_sum_m3=float(vpos[first].sum()),
       positive_max_m3=float(vpos.max()),
       first_svat=int(ids[np.flatnonzero(positive)[0]]),
       first_row=int(rr[np.flatnonzero(positive)[0]]),
       first_col=int(cc[np.flatnonzero(positive)[0]])))
     values=np.where(positive,0.,values)
   sums[role]+=values
   # Classify each system and each cell *before* time aggregation.
   # A signed RIV value is at one timestep either drainage or infiltration.
   if role=='flf':
    # Positive original FLF is supply to layer 1 (kwel), negative is wegzijging.
    sums['flf_kwel']+=np.maximum(values,0.)
    sums['flf_wegzijging']+=np.maximum(-values,0.)
   elif role.startswith('riv_sys'):
    sums[role+'_ontwatering']+=np.maximum(-values,0.)
    sums[role+'_infiltratie']+=np.maximum(values,0.)
   elif role.startswith('drn_sys'):
    # Drain outflow only. Positive source anomalies were logged above and set to zero.
    sums[role+'_ontwatering']+=np.maximum(-values,0.)
  if index%60==0:print(f'MODFLOW {year}: {index} dagen van {366 if calendar.isleap(year) else 365}',flush=True)
 cache.parent.mkdir(parents=True,exist_ok=True)
 tmp=cache.with_suffix('.partial.npz')
 np.savez_compressed(tmp,SVAT=ids,**sums,**{'coverage_'+r:coverage[r] for r in roles})
 tmp.replace(cache)
 emit_json(receipt,dict(year=year,roles=list(roles),cache_format=CACHE_FORMAT,source_signature=sig,
   source_count=num,area_sha256=area_sha,ibound_sha256=ibound_sha,
   cache_sha256=hashfile(cache),coverage_counts=coverage,drn_positive_anomalies=anomalies,
   signature_limit='name/path/size/mtime, not per-IDF cryptographic hashes'))
 return sums,coverage,anomalies

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--from-year',type=int,default=2020)
 p.add_argument('--to-year',type=int,default=2020)
 p.add_argument('--root',type=Path,default=ROOT)
 p.add_argument('--area',type=Path,default=AREA)
 p.add_argument('--mask',type=Path,default=MASK)
 p.add_argument('--out',type=Path,default=BASE/'LWKM_run_resultaten_totaal'/'frank_export_modflow_bruto_v07')
 p.add_argument('--check-only',action='store_true')
 p.add_argument('--join-metaswap',type=Path,default=None,help='Optioneel, eerder geproduceerde CSV met dezelfde SVAT-ID volgorde')
 a=p.parse_args()
 if a.from_year<1970 or a.to_year>2022 or a.from_year>a.to_year:raise ValueError('Ongeldige periode')
 roles=ROLES
 ids,area,x,y=msw.read_area(a.area)
 geo,mask,cov=read_idf(a.mask)
 if not np.isclose(geo[6]*geo[7],62500):raise ValueError('MODFLOW celoppervlak is niet 62500 m2')
 rr,cc=grid_indexes(geo,x,y)
 if not np.all(cov[rr,cc] & (np.asarray(mask[rr,cc])!=0)):
  raise ValueError('SVAT gekoppeld aan inactieve MODFLOW-laag-1-cel; diagnoseer eerst de koppeling')
 area_sha=hashfile(a.area); ibound_sha=hashfile(a.mask)
 if a.check_only:
  for yr in range(a.from_year,a.to_year+1):
   signature,n=source_signature(a.root,yr,roles)
   print(f'BRONCHECK {yr} OK: {n} IDFs; signature {signature[:16]}')
  print('SVATs:',len(ids),'MODFLOW cell m2:',geo[6]*geo[7]);return
 a.out.mkdir(parents=True,exist_ok=True)
 totals={r:np.zeros(len(ids),np.float64) for r in (*roles,*SPLIT_ROLES)}
 cover={r:0 for r in roles}
 audit=[]
 for yr in range(a.from_year,a.to_year+1):
  year_sums,year_cover,year_audit=annual(yr,a.root,roles,ids,rr,cc,geo,a.out,area_sha,ibound_sha)
  audit.extend(year_audit)
  for role in (*roles,*SPLIT_ROLES):
   totals[role]+=year_sums[role]
  for role in roles:
   cover[role]+=year_cover[role]
 years=a.to_year-a.from_year+1
 # Save anomaly audit even if there are no positive DRN stresses.
 audit_path=a.out/f'MF_DRN_POSITIVE_ZERO_AUDIT_{a.from_year}_{a.to_year}.csv'
 audit_columns=['year','date','role','positive_svat_count','positive_cell_count','positive_svat_sum_m3','positive_unique_cell_sum_m3','positive_max_m3','first_svat','first_row','first_col']
 with audit_path.open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=audit_columns)
  writer.writeheader();writer.writerows(audit)
 # Write 13 gross directional values plus 3 signed QLAT/WEL/GHB values.
 # Each value is a cumulative m3 volume over the selected calendar period,
 # sampled at the MODFLOW cell corresponding to the SVAT coordinate.
 result=a.out/f'MF_SVAT_BRUTO_16_{a.from_year}_{a.to_year}.csv'
 with result.open('w',newline='',encoding='utf8') as f:
  writer=csv.writer(f)
  writer.writerow(['SVAT','Opp_svat_m2','X_RD','Y_RD',*FLUX_COLS])
  for i,sv in enumerate(ids):
   fluxes=[float(totals[role][i]) for role in (*SPLIT_ROLES,'qlat','wel','ghb')]
   # Check no silently duplicated or missing signed transport during splitting.
   for k in range(1,5):
    signed=totals[f'riv_sys{k}'][i]
    if abs(signed-(totals[f'riv_sys{k}_infiltratie'][i]-totals[f'riv_sys{k}_ontwatering'][i]))>TOL*max(1.,abs(signed)):
     raise ValueError(f'RIV direction mismatch for SVAT {sv}, sys{k}')
   for k in range(1,4):
    signed=totals[f'drn_sys{k}'][i]
    if abs(signed+totals[f'drn_sys{k}_ontwatering'][i])>TOL*max(1.,abs(signed)):
     raise ValueError(f'DRN direction mismatch for SVAT {sv}, sys{k}')
   if abs(totals['flf'][i]-(totals['flf_kwel'][i]-totals['flf_wegzijging'][i]))>TOL*max(1.,abs(totals['flf'][i])):
    raise ValueError(f'FLF direction mismatch for SVAT {sv}')
   writer.writerow([int(sv),format(float(area[i]),'.12g'),format(float(x[i]),'.12g'),format(float(y[i]),'.12g'),
                    *(format(v,'.12g') for v in fluxes)])
 if a.join_metaswap is not None:
  raise ValueError('v0.6 schrijft uitsluitend de 16 MODFLOW-fluxen. Geen automatische join. Gebruik SVAT als sleutel voor vervolgstappen.')
 manifest=dict(status='DIAGNOSTIC_MODFLOW_DAILY_GROSS_16_DRN_POSITIVE_ZEROED',period=f'{a.from_year}-{a.to_year}',
  years=years,rows=len(ids),flux_columns=list(FLUX_COLS),roles=list(roles),cache_format=CACHE_FORMAT,
  source_root=str(a.root),source_area=str(a.area),source_mask=str(a.mask),
  area_sha256=area_sha,ibound_sha256=ibound_sha,
  sign='Original MODFLOW budget: positive supply to groundwater layer 1',
  split='Daily per cell: RIV positive=infiltration negative=drainage; DRN negative=drainage and ALL positive DRN values are set to zero with audit; FLF positive=kwel negative=wegzijging. Split BEFORE summing.',
  drn_positive_handling='positive daily DRN source values clipped to zero (also if less than tolerance); audit separately by date, system and cell',
  drn_positive_events=len(audit),drn_positive_svat_observations=sum(a['positive_svat_count'] for a in audit),
  drn_positive_unique_cell_observations=sum(a['positive_cell_count'] for a in audit),
  drn_positive_unique_cell_m3=sum(a['positive_unique_cell_sum_m3'] for a in audit),
  drn_positive_audit_csv=str(audit_path),
  units='m3 accumulated over entire specified period, for the full 250x250m MODFLOW cell; not per SVAT area; no normalization',
  active_roles='DRN 1..3 RIV 1..4 original FLF QLAT WEL GHB; no STO BND qmodf',
  caveat='Cell flux sampled at SVAT location, repeated for SVATs sharing cells. Not area-weighted; do not sum across SVATs without a spatial allocation scheme.',
  coverage_counts=cover,source_grid_nodata_policy='DRN/RIV/WEL/GHB no stress outside active package coverage = 0; FLF and QLAT must be available at each SVAT cell',
  source_csv=str(result))
 emit_json(a.out/f'MF_BRUTO_16_manifest_{a.from_year}_{a.to_year}.json',manifest)
 print('GEREED',result,'SVAT',len(ids),'years',years,flush=True)

if __name__=='__main__':
 try:main()
 except Exception as e:
  print('STOP_MODFLOW_FRANK:',e,file=sys.stderr);sys.exit(2)
