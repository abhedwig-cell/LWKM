"""Exact MET07/W11 schema, synthetic bytes, short calendar, real subprocess."""
from pathlib import Path
import sys,json,shutil,tempfile,zipfile,gzip,base64,io
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
_fixture_tmp=tempfile.TemporaryDirectory(prefix='LWKM received fixtures ')
FROOT=Path(_fixture_tmp.name)
_extracts=json.loads((ROOT/'tests/fixtures.json').read_text(encoding='utf-8'))
for _name,_text in _extracts.items():
 _target=FROOT/_name;_target.parent.mkdir(parents=True,exist_ok=True);_target.write_text(_text,encoding='utf-8')
sys.path.insert(0,str(ROOT))
from common import *
from results import COLUMNS

def fixture(base,n=4,initial=3,start='2000-02-27',end='2000-03-02',scenarios=None):
 base=Path(base);base.mkdir(parents=True,exist_ok=True);scenarios=scenarios or {}
 src=base/'MET07 input with spaces';rep=base/'MET07 reports';camp=base/'campaign';out=base/'reports'
 for d in (src,src/'catalogue',rep):d.mkdir(parents=True,exist_ok=True)
 ex=base/('python.exe' if sys.platform=='win32' else 'python')
 # Copy the interpreter avoids production executable dependence and supports hash mutation tests.
 # On Windows Python requires its installed DLLs, so use the existing interpreter there.
 if sys.platform=='win32':ex=Path(sys.executable)
 else:shutil.copyfile(sys.executable,ex);ex.chmod(0o755)
 cfg=dict(schema_version=1,source_root=str(src),met07_reports=str(rep),campaign_root=str(camp),report_root=str(out),executable=str(ex),executable_sha256=file_sha(ex),executable_prefix_args=[str(ROOT/'tests/fake_swap.py')],expected_population=n,initial_count=initial,start=start,end=end,timeout_seconds=5,min_free_bytes=0,per_run_reserve_bytes=0,anchors={},import_previous_trials=False,protected_roots=[])
 bc=dict(output_root=str(src),expected_population=n,start=start,end=end,hum=dict(quantity='actual_vapour_pressure',unit='kPa',scale=1))
 binding=dict(schema_version=1,config=bc,rule='SYNTHETIC_FIXTURE_ONLY')
 bs=object_sha(binding);cfg['expected_met07_binding_sha256']=bs
 atomic_json(src/'BINDING.json',binding);atomic_json(rep/'BINDING.json',binding)
 ledger=rep/'HUM_SOURCE_LEDGER.csv';ledger.write_text('SYNTHETIC_LEDGER\n')
 records=[]
 for hid in range(1,n+1):
  d=src/('run_%05d'%hid);d.mkdir()
  swp=f"""PROJECT = '{hid}'
TSTART = '{start}'
TEND = '{end}'
PATHWORK = ''
PATHATM = ''
PATHCROP = ''
PATHDRAIN = ''
METFIL = 'case.met'
BBCFIL = 'case'
DRFIL = 'case'
SWCSV = 1
NPRINTDAY = 1
PERIOD = 1
SWMONTH = 0
OUTFIL = 'result'
SWBOTB = {2 if hid%2 else 7}
SWDRA = 1
CROPSTART CROPEND CROPNAME CROPFIL CROPTYPE
'{start}' '{end}' 'case' 'case' 1
* End of table
ORES OSAT ALFA NPAR KSATFIT LEXP H_ENPR KSATEXM BDENS ELAS
0.01 0.4 0.01 1.5 {hid} 0.5 0 1 1 0
* End of table
ISUBLAY ISOILLAY HSUBLAY NCOMP
1 1 1.0 10
* End of table
"""
  (d/'swap.swp').write_text(swp);(d/'case.crp').write_text('SCHEDULE = '+str(hid%2)+'\n!TEST_JSON='+json.dumps(scenarios.get(hid,{}))+'\n')
  for ext in ('met','bbc','dra','co2'):(d/('case.'+ext)).write_text('synthetic '+str(hid)+' '+ext+'\n')
  assets={p.name:dict(path=str(p),sha256=file_sha(p),bytes=p.stat().st_size,qualification_id='SYNTHETIC') for p in d.iterdir()}
  ms=assets['case.met']['sha256'];old='a'*64;os='b'*64;days=(date.fromisoformat(end)-date.fromisoformat(start)).days+1
  corr=dict(correction=dict(hru=hid,corrected_sha256=ms,source_sha256=old,days=days,non_hum_bytes_verified_equal=True),inputs=dict(hru=hid,binding_sha256=bs,original_catalogue_sha256=os,start=start,end=end))
  cat=dict(hru=hid,profile_id=PROFILE,w11_source_commit=W11_COMMIT,status='MET07_HUM_CORRECTED_SOURCE_CATALOGUE_NOT_ADMITTED',assets=assets,swp_start_literal=start,swp_end_literal=end,derived_input_changed='case.met',hum_correction=corr,binder_code_sha256=bs,original_catalogue_sha256=os)
  cp=src/'catalogue'/('run_%05d.json'%hid);atomic_json(cp,cat)
  manifest=dict(schema_version=1,status='PACKAGE_CANDIDATE_NOT_ADMITTED',run_id=hid,profile_id=PROFILE,code_commit=W11_COMMIT,assets={k:{x:v[x] for x in ('sha256','qualification_id')} for k,v in assets.items()})
  atomic_json(d/'manifest.json',manifest)
  records.append(dict(hru=hid,status='MET07_REBOUND_HASH_VERIFIED',non_hum_bytes_verified_equal=True,unchanged_other_assets=True,days=days,run_directory=str(d),catalogue_sha256=file_sha(cp),corrected_met_sha256=ms,original_met_sha256=old,original_catalogue_sha256=os,assets=len(assets),bytes=sum(v['bytes'] for v in assets.values())))
 cfg['anchors']={'1':records[0]['corrected_met_sha256']}
 atomic_json(rep/'HRU_MET07_RESULTS.json',records);atomic_json(rep/'ANCHOR_MET_CHECKS.json',[dict(hru=1,matched=True,expected=cfg['anchors']['1'],actual=cfg['anchors']['1'])])
 status=dict(status=MET07_SUCCESS,completed=n,failed=0,errors=[],regression_anchors_matched=1,results_sha256=file_sha(rep/'HRU_MET07_RESULTS.json'),expected_population=n,requested_hrus=n,production_enabled=False,swap_executed=False,output_root=str(src),simulation_start=start,simulation_end=end,binding_sha256=bs,source_ledger_sha256=file_sha(ledger))
 atomic_json(rep/'STATUS_MET07_LANDELIJK.json',status);atomic_json(base/'config.json',cfg)
 return cfg

def update_report(cfg,name,fn):
 p=Path(cfg['met07_reports'])/name;v=read_json(p);fn(v);atomic_json(p,v)

def csv_file(path,start,end,transform=None):
 import csv
 from datetime import timedelta
 path=Path(path)
 with path.open('w',newline='') as f:
  f.write('* Model version: Swap 4.3.1\n* '+','.join(['(yyyy-mm-dd)']+['(cm)']*20)+'\n')
  w=csv.writer(f);w.writerow(COLUMNS);d=date.fromisoformat(start)-timedelta(days=1);e=date.fromisoformat(end)
  while d<=e:
   row=[str(d)]+[1.0]*20;row[COLUMNS.index('GWL')]=-123.0
   if transform:row=transform(d,row)
   if row is not None:w.writerow(row)
   d+=timedelta(days=1)
 return path
