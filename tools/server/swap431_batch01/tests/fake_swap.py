"""Synthetic subprocess for controller tests. Never a SWAP scientific model."""
import csv,json,os,re,sys,time
from datetime import date,timedelta
from pathlib import Path
COLUMNS='DATE RAIN IRRIG RUNOFF EIC EPD EPOT EACT TPOT TACT TREDDRY TREDWET DRN SSDI BOT GWL PD_VOL IC_VOL WTOT DSTOR BALDEV'.split()
def setting(text,key):return re.search(r'^'+key+r'\s*=\s*([^\n]+)',text,re.M).group(1).strip().strip("'\"")
def main():
 text=Path('swap.swp').read_text();hid=int(setting(text,'PROJECT'))
 scenario=json.loads(Path('case.crp').read_text().split('!TEST_JSON=',1)[1].splitlines()[0])
 mode=scenario.get('mode','ok');wait=scenario.get('sleep',0.05)
 Path('fake_started.json').write_text(json.dumps({'pid':os.getpid(),'start':time.time(),'hru':hid}))
 if scenario.get('external_marker'):
  with open(scenario['external_marker'],'a') as f:f.write(str(hid)+'\n')
 time.sleep(wait)
 if mode=='fatal':
  Path('swap.err').write_text('ERROR in TEST: synthetic failure\nFatal execution error\n');return 0
 if mode=='change_input':Path('case.dra').write_text('CHANGED')
 if mode=='no_normal':return 0
 start=date.fromisoformat(setting(text,'TSTART'));end=date.fromisoformat(setting(text,'TEND'))
 out=setting(text,'OUTFIL')+'_output.csv'
 with open(out,'w',newline='') as f:
  f.write('* Model version: Swap 4.3.1\n* '+','.join(['(yyyy-mm-dd)']+['(cm)']*20)+'\n')
  w=csv.writer(f);w.writerow(COLUMNS);day=start-timedelta(days=1)
  while day<=end:
   if not (mode=='gap' and day==start):
    values=[0.0 if day<start else 1.0 for _ in range(20)]
    values[COLUMNS.index('GWL')-1]=-100.0;values[-1]=0.00001
    if mode=='nan' and day==end:values[-1]=float('nan')
    w.writerow([str(day)]+values)
   day+=timedelta(days=1)
 Path('swap.log').write_text('Swap simulation okay!\n')
 print('Swap normal completion!',flush=True)
 return scenario.get('returncode',100)
if __name__=='__main__':sys.exit(main())
