"""Unit and real-subprocess tests. Model process is synthetic, never actual SWAP."""
from pathlib import Path
import sys,unittest,tempfile,json,time,subprocess,os,shutil,ast
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent));from support import *
import batch,common,met07_adapter as adapter,results

class FixtureCase(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='LWKM batch test ');self.base=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def config(self,**kw):return fixture(self.base,**kw)
 def runall(self,cfg,**kw):batch.prepare(cfg);return batch.run_batch(cfg,**kw)

class GateTests(FixtureCase):
 def test_read_exact_met07_schema(self):
  c=self.config();s,r,h=adapter.load_met07(c);self.assertEqual(len(r),4);self.assertEqual(s['failed'],0)
 def test_missing_status_refused_no_run(self):
  c=self.config();(Path(c['met07_reports'])/'STATUS_MET07_LANDELIJK.json').unlink()
  with self.assertRaises(common.NotReady):batch.prepare(c)
  self.assertFalse((Path(c['campaign_root'])/'CAMPAIGN.json').exists())
 def test_running_met07_refused(self):
  c=self.config();update_report(c,'STATUS_MET07_LANDELIJK.json',lambda v:v.update(status='RUNNING'))
  with self.assertRaises(common.NotReady):adapter.load_met07(c)
 def test_failed_met07_refused(self):
  c=self.config();update_report(c,'STATUS_MET07_LANDELIJK.json',lambda v:v.update(failed=1))
  with self.assertRaises(common.NotReady):adapter.load_met07(c)
 def test_results_hash_rejected(self):
  c=self.config();p=Path(c['met07_reports'])/'HRU_MET07_RESULTS.json';p.write_text(p.read_text()+' ')
  with self.assertRaises(common.IntegrityError):adapter.load_met07(c)
 def test_duplicate_population_rejected(self):
  c=self.config();rep=Path(c['met07_reports']);rows=read_json(rep/'HRU_MET07_RESULTS.json');rows[1]=rows[0]
  atomic_json(rep/'HRU_MET07_RESULTS.json',rows)
  update_report(c,'STATUS_MET07_LANDELIJK.json',lambda v:v.update(results_sha256=file_sha(rep/'HRU_MET07_RESULTS.json')))
  with self.assertRaises(common.IntegrityError):adapter.load_met07(c)
 def test_anchor_rejected(self):
  c=self.config();update_report(c,'ANCHOR_MET_CHECKS.json',lambda v:v[0].update(actual='0'*64))
  with self.assertRaises(common.IntegrityError):adapter.load_met07(c)
 def test_wrong_bound_software_rejected(self):
  c=self.config();c['expected_met07_binding_sha256']='0'*64
  with self.assertRaises(common.IntegrityError):adapter.load_met07(c)
 def test_changed_ledger_rejected(self):
  c=self.config();(Path(c['met07_reports'])/'HUM_SOURCE_LEDGER.csv').write_text('changed')
  with self.assertRaises(common.IntegrityError):adapter.load_met07(c)
 def test_changed_manifest_rejected(self):
  c=self.config();w,r,h=batch.gate(c);p=Path(c['source_root'])/'run_00001/manifest.json';m=read_json(p);m['run_id']=2;atomic_json(p,m)
  with self.assertRaises(common.IntegrityError):adapter.package(w,r[1])
 def test_changed_asset_rejected(self):
  c=self.config();w,r,h=batch.gate(c);(Path(c['source_root'])/'run_00001/case.met').write_text('changed')
  with self.assertRaises(common.IntegrityError):adapter.package(w,r[1])
 def test_extra_input_file_rejected(self):
  c=self.config();w,r,h=batch.gate(c);(Path(c['source_root'])/'run_00001/old_output.csv').write_text('old')
  with self.assertRaises(common.IntegrityError):adapter.package(w,r[1])
 def test_protected_source_overlap(self):
  c=self.config();c['campaign_root']=c['source_root'];atomic_json(self.base/'config.json',c)
  with self.assertRaises(common.IntegrityError):batch.load_config(self.base/'config.json')
 def test_prepare_reuse_and_no_execution(self):
  c=self.config();b=batch.prepare(c);b2=batch.prepare(c);self.assertEqual(b,b2)
  self.assertFalse((Path(c['campaign_root'])/'runs').exists())
 def test_config_mutation_refused(self):
  c=self.config();batch.prepare(c);c['start']='1999-01-01'
  with self.assertRaises(common.IntegrityError):batch.open_campaign(c)
 def test_selection_deterministic_and_covers_settings(self):
  c=self.config(n=12,initial=5);batch.prepare(c);sel=read_json(Path(c['campaign_root'])/'SELECTION_100.json')
  self.assertIn(1,sel['selected_hrus']);self.assertEqual(len(set(sel['selected_hrus'])),5)
  m=read_json(Path(c['campaign_root'])/'FEATURES.json');sel2=adapter.select_initial({int(k):v for k,v in m.items()},5,[1]);self.assertEqual(sel,sel2)
  self.assertFalse(sel['statistical_representativeness_claimed'])
 def test_six_real_swps_features(self):
  dirs=sorted(FROOT.glob('run_*'));self.assertEqual(len(dirs),6)
  for d in dirs:
   f=adapter.features(d,{'assets':{p.name:{} for p in d.iterdir()}},(d/'swap.swp').read_text())
   self.assertNotEqual(f['values']['soil'],'UNKNOWN');self.assertNotEqual(f['values']['crop'],'UNKNOWN');self.assertEqual(f['missing'],[])
 def test_safe_basenames(self):
  for s in ('../bad','C:\\bad','a/b','NUL','CON.txt','x..y','x.'):
   with self.assertRaises(common.IntegrityError):common.basename(s)
 def test_os_lock(self):
  p=self.base/'test.lock'
  with common.FileLock(p):
   with self.assertRaises(common.IntegrityError):
    with common.FileLock(p):pass
  with common.FileLock(p):pass
 def test_daily_table_parser_quotes_comments(self):
  a=common.assignments("PATHWORK = '' ! comment\nOUTFIL='result'\n* x = 7\n")
  self.assertEqual(common.one(a,'PATHWORK'),'');self.assertEqual(common.one(a,'OUTFIL'),'result')

class OutputTests(FixtureCase):
 def test_leap_day_and_year_decade_aggregation(self):
  p=csv_file(self.base/'x.csv','1999-12-29','2000-03-02');s=results.inspect_csv(p,'1999-12-29','2000-03-02',self.base/'a')
  self.assertEqual(s['statistics']['days'],65);self.assertEqual(s['statistics']['RAIN_sum_cm'],65)
  self.assertEqual(s['statistics']['GWL_mean_cm'],-123);self.assertNotIn('GWL_sum_cm',s['statistics'])
  self.assertNotIn('ETACT_sum_cm',s['statistics']);self.assertIsNone(s['scientific_balance_tolerance'])
 def test_missing_day(self):
  p=csv_file(self.base/'x.csv','2000-02-28','2000-03-01',lambda d,r:None if str(d)=='2000-02-29' else r)
  with self.assertRaisesRegex(ValueError,'DATE_GAP'):results.inspect_csv(p,'2000-02-28','2000-03-01')
 def test_missing_initial_state(self):
  p=csv_file(self.base/'x.csv','2000-01-01','2000-01-02',lambda d,r:None if str(d)=='1999-12-31' else r)
  with self.assertRaises(ValueError):results.inspect_csv(p,'2000-01-01','2000-01-02')
 def test_nonfinite(self):
  p=csv_file(self.base/'x.csv','2000-01-01','2000-01-02',lambda d,r:r[:-1]+['NaN'])
  with self.assertRaisesRegex(ValueError,'NONFINITE'):results.inspect_csv(p,'2000-01-01','2000-01-02')
 def test_wrong_units(self):
  p=csv_file(self.base/'x.csv','2000-01-01','2000-01-02');p.write_text(p.read_text().replace('(cm)','(mm)'))
  with self.assertRaisesRegex(ValueError,'UNITS'):results.inspect_csv(p,'2000-01-01','2000-01-02')
 def test_extra_day(self):
  p=csv_file(self.base/'x.csv','2000-01-01','2000-01-03')
  with self.assertRaises(ValueError):results.inspect_csv(p,'2000-01-01','2000-01-02')
 def test_actual_excerpts_not_full_output(self):
  for p in FROOT.glob('run_*/result_output.csv.excerpt.txt'):
   with self.assertRaises(ValueError):results.inspect_csv(p,'1970-01-01','2022-12-31')
 def test_fatal_even_with_normal_marker(self):
  (self.base/'runtime.log').write_text('Swap normal completion!\n');(self.base/'swap.err').write_text('ERROR in RDFDOR:\nFatal execution error\n')
  r=results.inspect_logs(self.base);self.assertTrue(r['normal_completion']);self.assertEqual(r['fatal_messages'],2)

class ExecutionTests(FixtureCase):
 def test_parallel_actual_processes_complete_resume_no_repeat(self):
  c=self.config(scenarios={i:{'sleep':.4} for i in range(1,5)});s=self.runall(c,workers=2)
  self.assertEqual(s['requested_counts'],{'completed':3})
  camp=Path(c['campaign_root']);before=sorted(p.as_posix() for p in camp.rglob('MODEL_STARTED.json'))
  s2=batch.run_batch(c,workers=2);self.assertEqual(s2['reused_this_invocation'],3)
  self.assertEqual(before,sorted(p.as_posix() for p in camp.rglob('MODEL_STARTED.json')))
  tasks=[read_json(p) for p in camp.rglob('EXECUTION.json')];self.assertEqual(len(tasks),3)
  if (os.cpu_count() or 1)>1:
   starts=sorted(read_json(p)['start'] for p in camp.rglob('fake_started.json'));self.assertLess(starts[1]-starts[0],.4)
 def test_individual_fatal_isolated(self):
  c=self.config(scenarios={1:{'mode':'fatal'}});s=self.runall(c,workers=2)
  self.assertEqual(s['requested_counts']['failed'],1);self.assertEqual(s['requested_counts']['completed'],2)
  states=batch.read_states(Path(c['campaign_root']),range(1,5));self.assertFalse(states[1]['shared_failure'])
 def test_no_automatic_failed_retry(self):
  c=self.config(scenarios={1:{'mode':'fatal'}});self.runall(c);camp=Path(c['campaign_root'])
  before=len(list(camp.rglob('MODEL_STARTED.json')));batch.run_batch(c);self.assertEqual(len(list(camp.rglob('MODEL_STARTED.json'))),before)
  batch.run_batch(c,retry_failed=True);self.assertEqual(len(list(camp.rglob('MODEL_STARTED.json'))),before+1)
 def test_timeout_is_failed_not_success(self):
  c=self.config(scenarios={1:{'sleep':2}});s=self.runall(c,timeout=.2)
  st=batch.read_states(Path(c['campaign_root']),[1]);r=read_json(st[1]['result_path']);self.assertTrue(r['timed_out']);self.assertEqual(r['state'],'failed')
 def test_changed_work_input_shared_stop(self):
  c=self.config(scenarios={1:{'mode':'change_input'}});s=self.runall(c,workers=1)
  self.assertEqual(s['status'],'STOPPED_SHARED_PROBLEM');self.assertEqual(len(list(Path(c['campaign_root']).rglob('MODEL_STARTED.json'))),1)
 def test_no_normal_marker_rejected(self):
  c=self.config(scenarios={1:{'mode':'no_normal'}});s=self.runall(c);self.assertEqual(s['requested_counts']['failed'],1)
 def test_nonfinite_model_output_isolated(self):
  c=self.config(scenarios={1:{'mode':'nan'}});s=self.runall(c);self.assertEqual(s['requested_counts']['failed'],1)
 def test_changed_output_cannot_be_reused(self):
  c=self.config();self.runall(c);p=next(Path(c['campaign_root']).rglob('result_output.csv'));p.write_text(p.read_text()+'\n')
  s=batch.run_batch(c);self.assertEqual(s['status'],'STOPPED_SHARED_PROBLEM');self.assertIn('blocked',s['requested_counts'])
 def test_changed_source_cannot_be_reused(self):
  c=self.config();self.runall(c);(Path(c['source_root'])/'run_00001/case.met').write_text('changed')
  s=batch.run_batch(c);self.assertEqual(s['status'],'STOPPED_SHARED_PROBLEM')
 def test_extending_same_campaign_requires_review(self):
  c=self.config(n=5,initial=2);self.runall(c);camp=Path(c['campaign_root'])
  with self.assertRaises((FileNotFoundError,common.IntegrityError)):batch.run_batch(c,'all')
  with self.assertRaises(common.IntegrityError):batch.approve_all(c)
  batch.approve_all(c,True);s=batch.run_batch(c,'all');self.assertEqual(s['counts'],{'completed':5})
  self.assertEqual(len(list(camp.rglob('MODEL_STARTED.json'))),5)
 def test_failed_startbatch_cannot_expand(self):
  c=self.config(scenarios={1:{'mode':'fatal'}});self.runall(c)
  with self.assertRaises(common.IntegrityError):batch.approve_all(c,True)
 def test_low_disk_stops_before_model(self):
  c=self.config();c['min_free_bytes']=10**20;s=self.runall(c)
  self.assertEqual(s['status'],'STOPPED_SHARED_PROBLEM');self.assertFalse(list(Path(c['campaign_root']).rglob('MODEL_STARTED.json')))
 def test_pause_drains_and_resume(self):
  c=self.config(n=5,initial=5,scenarios={i:{'sleep':.4} for i in range(1,6)});batch.prepare(c)
  import threading
  def pause():
   time.sleep(.2);atomic_json(Path(c['campaign_root'])/'PAUSE.json',{'reason':'test'})
  t=threading.Thread(target=pause);t.start();s=batch.run_batch(c);t.join()
  self.assertEqual(s['status'],'PAUSED_AFTER_RUNNING_HRUS');self.assertLess(s['counts']['completed'],5)
  s2=batch.run_batch(c);self.assertEqual(s2['counts'],{'completed':5})
 def test_stale_running_retry_whole_hru(self):
  c=self.config();batch.prepare(c);camp=Path(c['campaign_root']);a=camp/'runs/old';a.mkdir(parents=True)
  batch.save_state(camp,dict(hru=1,state='running',attempts=1,attempt_directory=str(a)))
  s=batch.run_batch(c);self.assertEqual(s['requested_counts'],{'completed':3})
  self.assertEqual(batch.read_states(camp,[1])[1]['attempts'],2)
 def test_return_zip_exists_on_failure(self):
  c=self.config(scenarios={1:{'mode':'fatal'}});self.runall(c)
  import zipfile
  with zipfile.ZipFile(Path(c['report_root'])/'SWAP_BATCH_TERUG.zip') as z:
   self.assertIsNone(z.testzip());self.assertIn('STATUS_BATCH.json',z.namelist());self.assertTrue(any(x.startswith('failures/') for x in z.namelist()))

class PackagingTests(unittest.TestCase):
 def test_python38_syntax(self):
  for p in ROOT.rglob('*.py'):ast.parse(p.read_text(),filename=str(p),feature_version=(3,8))
 def test_production_config_fixed_path_and_exe(self):
  c=read_json(ROOT/'batch_config.json');self.assertEqual(c['expected_population'],10242);self.assertEqual(c['initial_count'],100)
  self.assertIn('Server06_MET07_',c['source_root']);self.assertEqual(c['executable_prefix_args'],[]);self.assertEqual(len(c['anchors']),6)
  self.assertEqual(object_sha(read_json(ROOT/'evidence/met07_expected_binding.json')),c['expected_met07_binding_sha256'])

if __name__=='__main__':unittest.main(verbosity=2)
