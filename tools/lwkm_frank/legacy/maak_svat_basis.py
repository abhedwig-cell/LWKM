#!/usr/bin/env python3
"""Make Frank's ORIGINAL/UNCORRECTED 1991–2020 SVAT baseline on the NHI server.

Strict one-to-one SVAT joins. FLF and RIV1 are ALWAYS from the ORIGINAL v0.7
MODFLOW export. No Flevoland, donor replacement, HRU or SWAP inputs.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sqlite3,sys,tempfile
from pathlib import Path
from collections import Counter

ROOT=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal')
DEFAULTS={
 'metaswap':ROOT/'frank_export'/'FRANK_LHM_SVAT_BASE_1991_2020.csv',
 'signed':ROOT/'frank_export'/'MSW_SOURCE_SIGNED_1991_2020.csv',
 'gxg':ROOT/'frank_export_heads'/'percentielen_v01'/'FRANK_LHM_SVAT_GXG_GG_GW5_GW95_1991_2020.csv',
 'mf':ROOT/'frank_export_modflow_bruto_v07'/'MF_SVAT_BRUTO_16_1991_2020.csv',
 'et':ROOT/'frank_export_aanvulling_v01'/'FRANK_SVAT_MSW_AANVULLING_1991_2020.csv',
 'static':ROOT/'frank_export_aanvulling_v04'/'FRANK_SVAT_STATISCH_GT_1991_2020.csv',
 'gebied':ROOT/'frank_export_aanvulling_v01'/'FRANK_SVAT_GEBIED_N_1991_2020.csv',
 'qmodf':ROOT/'frank_export_qmodf_v01'/'FRANK_SVAT_QMODF_1991_2020.csv',
 'out':ROOT/'frank_export_eindtabel'/'svat_basis_ongecorrigeerd_v01',
}
MF=[*(f'RIV_SYS{i}_ONTWATERING_m3' for i in range(1,5)),*(f'RIV_SYS{i}_INFILTRATIE_m3' for i in range(1,5)),*(f'DRN_SYS{i}_ONTWATERING_m3' for i in range(1,4)),'FLF_KWEL_m3','FLF_WEGZIJGING_m3','LAT_NETTO_m3','WEL_NETTO_m3','GHB_NETTO_m3']
MSW=['bdgdecstot','bdgpm','bdgpssw','bdgpsgw','bdgetact','bdgqrun']
SIGNED=[f'{v}_signed_mm_per_year' for v in MSW]
SCHEMA=['SVAT/HRU','Gebied','N','Opp_svat/hru','Landuse LHM (22)','Landuse ANIMO (4 tekst)','LU4','LU2','Bodem370','Bodem79','Pawn21','Grondsoort4','Grondsoort2','Gtnr','GLG','GHG','GG','Dynamiek','GW5','GW95','Kwelklasse4','Neerslag','Beregening','Evapotranspiratie','Verdamping gewas','Verdamping interceptie','Verdamping bodem','Oppervlakkige afstroming','Ontwatering','Fldrou1','Fldrou2','Fldrou3','Fldrou4','Fldrou5','Infiltratie','Fldrin1','Fldrin2','Fldrin345','Netto kwel/wegzijging','Laterale stroming (netto)','Onttrekkingen (laag 1)','General head boundary','Wegzijging','Kwel','QModF','Bergingsverandering (MetaSWAP)','Waterbalansafwijking MetaSWAP','Waterbalansafwijking overall (excl. MODFLOW storage)','Indicator gecorrigeerd/vervangen SVAT']
AUDIT=['SVAT','Opp_svat_m2','X_RD','Y_RD','GG_14_28_gemiddeld_cm_mv','GVG_cm_mv','GW5_cm_mv','GW95_cm_mv','LU7','Meteoregio_nm','MetaSWAP_signed_som6_mm_j','MetaSWAP_QModF_signed_mm_j','MSW_7term_afwijking_mm_j','Overall_onverklaard_volume_m3_per_j_cel','Flux_ruimtebasis','Balans_interpretatie',*MF,*SIGNED,'MSW_ET_componentensom_mm_j','MSW_ET_verschil_mm_j']
REQ={
 'signed':['SVAT','Opp_svat_m2','X_RD_m','Y_RD_m','complete_source',*SIGNED],
 'gxg':['SVAT','GHG_cm_mv','GLG_cm_mv','GW5','GW95'],
 'mf':['SVAT',*MF],
 'et':['SVAT','Verdamping_gewas_mm_j','Verdamping_interceptie_mm_j','Verdamping_bodem_en_plas_mm_j','Beregening_mm_j'],
 'static':['SVAT','landgebruik22','LU7','LU4','LU2','bodem370','BOFEK79','Pawn21','Grondsoort4','Grondsoort2','Gtnr'],
 'gebied':['SVAT','Gebied','N'],
 'qmodf':['SVAT','QModF_signed_mm_j','QModF_volledig']
}
ANIMO={1:'gras',2:'maïs',3:'akkerbouw',4:'natuur'}

def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def number(s,label,sv,required=True):
 if s is None or str(s).strip()=='':
  if required:raise ValueError(f'SVAT {sv}: leeg veld {label}')
  return None
 try:r=float(s)
 except ValueError as e:raise ValueError(f'SVAT {sv}: ongeldig getal {label}={s!r}') from e
 if not math.isfinite(r):raise ValueError(f'SVAT {sv}: niet eindig {label}')
 return r

def fmt(x):return '' if x is None else format(float(x),'.12g')

def near(a,b,sv,label,abs_tol=.03,rel_tol=1e-7):
 if abs(a-b)>max(abs_tol,rel_tol*max(abs(a),abs(b))):raise ValueError(f'SVAT {sv}: {label} {a} vs {b}')

def kwelklass(q):
 if q<=-.25:return 1
 if q<.25:return 2
 if q<=.75:return 3
 return 4

def import_csv(db,name,path,required,expected):
 with path.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f)
  miss=set(required)-set(r.fieldnames or [])
  if miss:raise ValueError(f'{name}: ontbrekende kolommen: {sorted(miss)}')
  db.execute(f'CREATE TABLE {name}(svat INTEGER PRIMARY KEY,data TEXT NOT NULL)')
  rows=[];count=0
  for x in r:
   sv=int(x['SVAT']);rows.append((sv,json.dumps(x,ensure_ascii=False)))
   if len(rows)==10000:
    db.executemany(f'INSERT INTO {name} VALUES (?,?)',rows);rows=[]
   count+=1
  if rows:db.executemany(f'INSERT INTO {name} VALUES (?,?)',rows)
  db.commit()
  if count!=expected:raise ValueError(f'{name}: {count} rijen, verwacht {expected}')
  print('GEKOPPELD',name,count,flush=True)

def get(db,name,sv):
 x=db.execute(f'SELECT data FROM {name} WHERE svat=?',(sv,)).fetchone()
 if not x:raise ValueError(f'SVAT {sv} ontbreekt in {name}')
 return json.loads(x[0])

def validate_gxg(g,sv):
 ghg=number(g['GHG_cm_mv'],'GHG',sv);glg=number(g['GLG_cm_mv'],'GLG',sv)
 if ghg>glg+.0001:raise ValueError(f'SVAT {sv}: GHG dieper dan GLG')
 if g.get('GW5') and g.get('GW95') and float(g['GW5'])>float(g['GW95'])+.0001:raise ValueError('GW5 > GW95')
 return ghg,glg

def row_calc(sv,b,sg,g,m,e,st,geo,q):
 if sg['complete_source']!='1' or e.get('volledig')!='1' or q['QModF_volledig']!='1':raise ValueError(f'SVAT {sv}: onvolledige MetaSWAP/QModF bron')
 if geo['N']!='1':raise ValueError(f'SVAT {sv}: N moet exact 1 zijn')
 area=number(b['Opp_svat'],'Opp_svat',sv)
 near(area,number(sg['Opp_svat_m2'],'area_signed',sv),sv,'oppervlakte')
 for name,obj in [('MF',m),('ET',e)]:
  if 'Opp_svat_m2' in obj:near(area,number(obj['Opp_svat_m2'],'area_'+name,sv),sv,'oppervlakte '+name)
 ghg,glg=validate_gxg(g,sv);mf=lambda key:number(m[key],key,sv)
 signed={k:number(sg[f'{k}_signed_mm_per_year'],k,sv) for k in MSW}
 qvalue=number(q['QModF_signed_mm_j'],'QModF',sv)
 factor=1000/(62500*30)
 dr=[mf('RIV_SYS1_ONTWATERING_m3')+mf('RIV_SYS4_ONTWATERING_m3'),mf('RIV_SYS2_ONTWATERING_m3'),mf('RIV_SYS3_ONTWATERING_m3'),mf('DRN_SYS1_ONTWATERING_m3'),mf('DRN_SYS2_ONTWATERING_m3')+mf('DRN_SYS3_ONTWATERING_m3')]
 infil=[mf('RIV_SYS1_INFILTRATIE_m3')+mf('RIV_SYS4_INFILTRATIE_m3'),mf('RIV_SYS2_INFILTRATIE_m3'),mf('RIV_SYS3_INFILTRATIE_m3')]
 kwel=mf('FLF_KWEL_m3');weg=mf('FLF_WEGZIJGING_m3');net=kwel-weg
 qnet_mmd=net*1000/(62500*10958)
 signed_six=sum(signed.values());msw_seven=signed_six+qvalue
 # True common-support *cell volume*: MetaSWAP signed depth over active SVAT area;
 # MODFLOW signed volume is native full-cell m3. Never multiply the MF volume by SVAT fraction.
 msw_six_volume_year=signed_six/1000*area
 mf_signed_30y=(sum(infil)-sum(dr)+net+mf('LAT_NETTO_m3')+mf('WEL_NETTO_m3')+mf('GHB_NETTO_m3'))
 overall_m3_y=msw_six_volume_year+mf_signed_30y/30
 overall_mm_y=overall_m3_y*1000/62500
 # This is explicitly the WB23 R0 available-term accounting diagnostic, no MODFLOW storage.
 out={
 'SVAT/HRU':str(sv),'Gebied':geo['Gebied'],'N':'1','Opp_svat/hru':fmt(area),
 'Landuse LHM (22)':st['landgebruik22'],'LU4':st['LU4'],'LU2':st['LU2'],
 'Bodem370':st['bodem370'],'Bodem79':st['BOFEK79'],'Pawn21':st['Pawn21'],'Grondsoort4':st['Grondsoort4'],'Grondsoort2':st['Grondsoort2'],'Gtnr':st['Gtnr'],
 'GLG':fmt(glg/100),'GHG':fmt(ghg/100),'GG':fmt((ghg+glg)/200),'Dynamiek':fmt((glg-ghg)/100),
 'GW5':fmt(number(g['GW5'],'GW5',sv)/100),'GW95':fmt(number(g['GW95'],'GW95',sv)/100),'Kwelklasse4':str(kwelklass(qnet_mmd)),
 'Neerslag':b['Neerslag'],'Beregening':e['Beregening_mm_j'],'Evapotranspiratie':b['Evapotranspiratie'],
 'Verdamping gewas':e['Verdamping_gewas_mm_j'],'Verdamping interceptie':e['Verdamping_interceptie_mm_j'],'Verdamping bodem':e['Verdamping_bodem_en_plas_mm_j'],
 'Oppervlakkige afstroming':b['Oppervlakkige afstroming'],'Ontwatering':fmt(sum(dr)*factor),
 'Fldrou1':fmt(dr[0]*factor),'Fldrou2':fmt(dr[1]*factor),'Fldrou3':fmt(dr[2]*factor),'Fldrou4':fmt(dr[3]*factor),'Fldrou5':fmt(dr[4]*factor),
 'Infiltratie':fmt(sum(infil)*factor),'Fldrin1':fmt(infil[0]*factor),'Fldrin2':fmt(infil[1]*factor),'Fldrin345':fmt(infil[2]*factor),
 'Netto kwel/wegzijging':fmt(net*factor),'Laterale stroming (netto)':fmt(mf('LAT_NETTO_m3')*factor),
 'Onttrekkingen (laag 1)':fmt(mf('WEL_NETTO_m3')*factor),'General head boundary':fmt(mf('GHB_NETTO_m3')*factor),
 'Wegzijging':fmt(weg*factor),'Kwel':fmt(kwel*factor),'QModF':fmt(qvalue),
 'Bergingsverandering (MetaSWAP)':fmt(signed['bdgdecstot']),
 'Waterbalansafwijking MetaSWAP':fmt(msw_seven),
 'Waterbalansafwijking overall (excl. MODFLOW storage)':fmt(overall_mm_y),
 'Indicator gecorrigeerd/vervangen SVAT':'',
 }
 lu=int(st['LU4'])
 out['Landuse ANIMO (4 tekst)']=ANIMO.get(lu,'') if lu!=0 else ''
 audit={'SVAT':sv,'Opp_svat_m2':fmt(area),'X_RD':sg['X_RD_m'],'Y_RD':sg['Y_RD_m'],
 'GG_14_28_gemiddeld_cm_mv':g.get('GG_cm_mv',''),'GVG_cm_mv':g.get('GVG_cm_mv',''),'GW5_cm_mv':g['GW5'],'GW95_cm_mv':g['GW95'],'LU7':st['LU7'],'Meteoregio_nm':st.get('Meteoregio_nm',''),
 'MetaSWAP_signed_som6_mm_j':fmt(signed_six),'MetaSWAP_QModF_signed_mm_j':fmt(qvalue),'MSW_7term_afwijking_mm_j':fmt(msw_seven),
 'Overall_onverklaard_volume_m3_per_j_cel':fmt(overall_m3_y),'Flux_ruimtebasis':'MF_FUL_62500m2_plus_MSW_ARK',
 'Balans_interpretatie':'DIAGNOSTISCH_ZONDER_MODFLOW_STORAGE_OF_BND',
 'MSW_ET_componentensom_mm_j':e.get('ET_componentensom_mm_j',''),'MSW_ET_verschil_mm_j':e.get('ET_verschil_tov_bdgETact_mm_j','')}
 audit.update({k:m[k] for k in MF});audit.update({k:sg[k] for k in SIGNED})
 return out,audit

def execute(a):
 paths={k:getattr(a,k) for k in ('metaswap','signed','gxg','mf','et','static','gebied','qmodf')}
 for k,p in paths.items():
  if not p.is_file():raise FileNotFoundError(f'{k}: {p}')
 a.out.mkdir(parents=True,exist_ok=True)
 manifest={'status':'IN_PROGRESS','period':'1991-2020','expected_svats':a.expected,'sources':{k:{'path':str(v),'sha256':hashfile(v)} for k,v in paths.items()},'missing_gebied':0,'animo_unmapped':Counter(),'kwelklassen':Counter(),'gt':Counter(),'count':0}
 with tempfile.TemporaryDirectory(prefix='frank_join_',dir=a.out) as td:
  db=sqlite3.connect(str(Path(td)/'join.sqlite'));db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF')
  for k in REQ:import_csv(db,k,paths[k],REQ[k],a.expected)
  out=a.out/'FRANK_SVAT_BASIS_ONGECORRIGEERD_1991_2020.csv'
  auditpath=a.out/'FRANK_SVAT_BASIS_CONTROLE_1991_2020.csv'
  tmp=out.with_suffix('.partial');audit_tmp=auditpath.with_suffix('.partial')
  with a.metaswap.open(newline='',encoding='utf-8-sig') as f,tmp.open('w',newline='',encoding='utf8') as fo,audit_tmp.open('w',newline='',encoding='utf8') as fa:
   reader=csv.DictReader(f)
   if not {'SVAT','Opp_svat','Neerslag','Evapotranspiratie','Oppervlakkige afstroming'}<=set(reader.fieldnames or []):raise ValueError('Basis mist verplichte velden')
   writer=csv.DictWriter(fo,fieldnames=SCHEMA,extrasaction='ignore');writer.writeheader()
   qa=csv.DictWriter(fa,fieldnames=AUDIT,extrasaction='ignore');qa.writeheader()
   seen=set()
   for base in reader:
    sv=int(base['SVAT'])
    if sv in seen:raise ValueError(f'Dubbele basis SVAT {sv}')
    seen.add(sv)
    r1,r2=row_calc(sv,base,*[get(db,k,sv) for k in ('signed','gxg','mf','et','static','gebied','qmodf')])
    writer.writerow(r1);qa.writerow(r2)
    manifest['count']+=1;manifest['missing_gebied']+=int(not r1['Gebied'])
    manifest['kwelklassen'][r1['Kwelklasse4']]+=1;manifest['gt'][str(r1['Gtnr'])]+=1
    if not r1['Landuse ANIMO (4 tekst)']:manifest['animo_unmapped'][str(r1['Landuse LHM (22)'])]+=1
    if manifest['count']%100000==0:print('SVAT BASIS',manifest['count'],flush=True)
   if len(seen)!=a.expected:raise ValueError(f'Basis bevat {len(seen)} SVATs; verwacht {a.expected}')
  db.close()
  tmp.replace(out);audit_tmp.replace(auditpath)
 manifest['status']='COMPLETED_DIAGNOSTIC_BALANCE_NOT_PHYSICAL_CLOSURE'
 for key in ('kwelklassen','gt','animo_unmapped'):manifest[key]=dict(manifest[key])
 manifest['outputs']={'table':str(out),'table_sha256':hashfile(out),'audit':str(auditpath),'audit_sha256':hashfile(auditpath)}
 manifest['units']={'GG_GHG_GLG_GW5_GW95_dynamiek':'m below ground level, positive downward','MSW':'mm/year over SVAT active area','MODFLOW':'mm/year equivalent over full cell 62500m2','overall_balance':'signed residual mm/year equivalent over full 62500m2 cell; MetaSWAP source terms converted using Opp_svat'}
 manifest['formulas']={'GG':'(GHG+GLG)/2','MSW7':'sum(original signed bdgdecstot,bdgpm,bdgpssw,bdgpsgw,bdgetact,bdgqrun,bdgqmodf)','OVERALL':'signed MetaSWAP 6 source terms (area m2 * mm/year /1000) + signed MODFLOW LAT,FLF,WEL,GHB,DRN,RIV (30-year m3 /30), then 1000/62500; NO QMODF, NO MODFLOW STO/BND'}
 manifest['limitations']=['MSW7 is a seven-term balance diagnostic, not demonstrated complete physical closure','Overall unaccounted term excludes MODFLOW storage and possible other terms','QModF is internal/derived and excluded from overall external sum','MODFLOW full-cell equivalent values cannot be added over multiple SVATs of one cell to obtain national volumes','no Flevoland correction applied','no donor changes, no HRU or SWAP data','Gebied NoData blank approved','Indicator gecorrigeerd/vervangen remains empty because stage not yet performed','date-specific original flux directions are already gross-split in v07']
 (a.out/'MANIFEST_FRANK_SVAT_BASIS.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 print('GEREED:',out,'SVAT:',manifest['count'],'Gebied leeg:',manifest['missing_gebied'])

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k,v in DEFAULTS.items():p.add_argument('--'+k,type=Path,default=v)
 p.add_argument('--expected',type=int,default=645582)
 try:execute(p.parse_args())
 except Exception as e:print('STOP SVAT BASIS:',str(e),file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
