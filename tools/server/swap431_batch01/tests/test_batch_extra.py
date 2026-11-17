from pathlib import Path
import sys,tempfile,unittest,subprocess,time,os,shutil,json
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent));from support import *
import batch,common,met07_adapter as adapter,results

class AdvancedTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='LWKM extra ');self.base=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_parallel_sequential_same_numeric_output(self):
  cfgs=[fixture(self.base/str(i),n=3,initial=3) for i in range(2)]
  hashes=[]
  for i,c in enumerate(cfgs):
   batch.prepare(c);s=batch.run_batch(c,workers=i+1);self.assertEqual(s['requested_counts'],{'completed':3})
   hashes.append(sorted(file_sha(p) for p in Path(c['campaign_root']).rglob('result_output.csv')))
  self.assertEqual(*hashes)
 def test_summary_mutation_refused(self):
  c=fixture(self.base);batch.prepare(c);batch.run_batch(c)
  p=next(Path(c['campaign_root']).rglob('YEAR.csv'));p.write_text(p.read_text()+'\n')
  self.assertEqual(batch.run_batch(c)['status'],'STOPPED_SHARED_PROBLEM')
 def test_code_identity_mutation_refused(self):
  c=fixture(self.base);batch.prepare(c)
  with patch('batch.code_identity',return_value={'changed':'changed'}):
   with self.assertRaises(common.IntegrityError):batch.open_campaign(c)
 def test_executable_hash_refused(self):
  c=fixture(self.base);c['executable_sha256']='0'*64
  with self.assertRaises(common.IntegrityError):batch.prepare(c)
 def test_source_snapshot_not_changed_by_campaign(self):
  c=fixture(self.base);src=Path(c['source_root']);before={str(p):file_sha(p) for p in src.rglob('*') if p.is_file()}
  batch.prepare(c);batch.run_batch(c);after={str(p):file_sha(p) for p in src.rglob('*') if p.is_file()};self.assertEqual(before,after)
 def test_actual_trial_import_requires_full_output_and_correct_hashes(self):
  c=fixture(self.base,n=1,initial=1);batch.prepare(c);batch.run_batch(c)
  camp=Path(c['campaign_root']);s=batch.read_states(camp,[1])[1];ex=read_json(s['result_path']);w=Path(ex['work_directory'])
  old=dict(ex);old.pop('executable_sha256',None);atomic_json(w/'execution.json',old)
  item=dict(work_directory=str(w),input_sha256=ex['input_sha256'],executable_sha256=c['executable_sha256'],execution_sha256=file_sha(w/'execution.json'),output_sha256=ex['output_validation']['sha256'])
  working,records,binding=batch.open_campaign(c);original=batch.read_json
  def reader(p):return {'1':item} if Path(p).name=='trial_imports.json' else original(p)
  with patch('batch.read_json',side_effect=reader):
   imp=batch.import_trial(working,records[1],binding);self.assertTrue(imp['imported'])
   batch.validate_completed(working,records[1],imp,binding)
   p=w/'result_output.csv';p.write_text('\n'.join(p.read_text().splitlines()[:4])+'\n')
   item['output_sha256']=file_sha(p)
   with self.assertRaises(ValueError):batch.import_trial(working,records[1],binding)
 def test_lost_controller_kills_model_and_can_resume(self):
  c=fixture(self.base,n=2,initial=2,scenarios={1:{'sleep':20},2:{'sleep':.1}});batch.prepare(c)
  code="import sys;sys.path.insert(0,sys.argv[1]);import batch;batch.run_batch(batch.load_config(sys.argv[2]),workers=1)"
  log=(self.base/'controller.log').open('w')
  p=subprocess.Popen([sys.executable,'-c',code,str(ROOT),str(self.base/'config.json')],stdout=log,stderr=subprocess.STDOUT)
  camp=Path(c['campaign_root']);deadline=time.monotonic()+10;started=[]
  try:
   while time.monotonic()<deadline:
    started=list(camp.rglob('MODEL_STARTED.json'))
    if started:break
    time.sleep(.05)
   self.assertTrue(started,'No model launched: '+(self.base/'controller.log').read_text())
   model_pid=read_json(started[0])['pid'];p.kill();p.wait(timeout=10);log.close()
   # Windows controller-owned job ends worker and SWAP. POSIX lease EOF kills SWAP.
   deadline=time.monotonic()+10
   def alive(pid):
    if os.name=='nt':
     import ctypes
     k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.restype=ctypes.c_void_p
     h=k.OpenProcess(0x1000,False,pid)
     if not h:return False
     value=ctypes.c_ulong();k.GetExitCodeProcess(ctypes.c_void_p(h),ctypes.byref(value));k.CloseHandle(ctypes.c_void_p(h));return value.value==259
    try:
     # A reaped/zombie process is no longer an executing model.
     return Path('/proc/%d/stat'%pid).read_text().split()[2]!='Z'
    except FileNotFoundError:return False
   while alive(model_pid) and time.monotonic()<deadline:time.sleep(.05)
   self.assertFalse(alive(model_pid),'Orphan model still executing')
   with common.FileLock(camp/'CONTROLLER.lock'):pass
   # Use short explicit time-out to avoid waiting for the synthetic slow HRU.
   s=batch.run_batch(c,workers=1,timeout=.2);self.assertNotEqual(s['status'],'STOPPED_SHARED_PROBLEM')
   self.assertEqual(batch.read_states(camp,[1])[1]['attempts'],2)
  finally:
   if p.poll() is None:p.kill();p.wait()
   if not log.closed:log.close()
 def test_duplicate_controller_rejected(self):
  c=fixture(self.base);batch.prepare(c)
  with common.FileLock(Path(c['campaign_root'])/'CONTROLLER.lock'):
   with self.assertRaises(common.IntegrityError):batch.run_batch(c)
 def test_national_selection_10242_deterministic_100(self):
  data={i:dict(values={'crop':str(i%4),'soil':str(i%370),'bottom':str(i%2),'irrigation':str(i%3),'drainage':'1','combination':str(i%24)},missing=[]) for i in range(1,10243)}
  s=adapter.select_initial(data,100,[1,3,181,7870,7871,7929]);self.assertEqual(len(set(s['selected_hrus'])),100)
  self.assertGreater(len(s['uncovered_categories']),0);self.assertTrue(set([1,3,181,7870,7871,7929])<=set(s['selected_hrus']))
if __name__=='__main__':unittest.main(verbosity=2)
