from pathlib import Path
import sys,unittest,tempfile,subprocess,os,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent));from support import *
import results,common
class DeliveryTests(unittest.TestCase):
 def test_package_manifest_current(self):common.verify_package()
 def test_cli_from_other_directory(self):
  with tempfile.TemporaryDirectory() as d:
   x=subprocess.run([sys.executable,str(ROOT/'batch.py'),'verify'],cwd=d,capture_output=True,text=True)
   self.assertEqual(x.returncode,0,x.stderr);self.assertIn('PACKAGE_HASHES_OK',x.stdout)
 def test_real_four_day_excerpt_prefix(self):
  text=(FROOT/'run_00001/result_output.csv.excerpt.txt').read_text().splitlines();head=[]
  for line in text:
   if not line.strip():break
   head.append(line)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'actual.csv';p.write_text('\n'.join(head)+'\n')
   s=results.inspect_csv(p,'1970-01-01','1970-01-04');self.assertEqual(s['rows'],5)
   self.assertAlmostEqual(s['statistics']['RAIN_sum_cm'],.11269+.40526+.02569)
 @unittest.skipUnless(os.name=='nt','CMD wrapper requires Windows')
 def test_windows_cmd_starters_other_directory(self):
  with tempfile.TemporaryDirectory(prefix='LWKM cmd ') as d:
   cfg=fixture(Path(d)/'fixture',n=2,initial=2);env=dict(os.environ,LWKM_BATCH_PYTHON=sys.executable)
   for starter in ('01_BEREID_REFERENTIERUN_VOOR.cmd','02_START_REFERENTIEBATCH_100.cmd'):
    command='call "'+str(ROOT/starter)+'" --config "'+str(Path(d)/'fixture/config.json')+'"'
    x=subprocess.run(['cmd','/d','/c',command],cwd=d,env=env,capture_output=True,text=True,timeout=60)
    self.assertEqual(x.returncode,0,x.stdout+x.stderr)
   states=list((Path(cfg['campaign_root'])/'states').glob('*.json'))
   self.assertEqual(len(states),2);self.assertTrue(all(read_json(p)['state']=='completed' for p in states))
if __name__=='__main__':unittest.main(verbosity=2)
