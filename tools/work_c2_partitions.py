"""Diagnose minimum protected level count, without relaxing physical error limits."""
from pathlib import Path
import json
from tools.dra_level_compression import PhysicalDrainageSystem
from tools.dra_protected_compression import select_protected_candidate
import argparse
p=argparse.ArgumentParser();p.add_argument('--drainage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
out=[]
for p in (args.drainage/'hrus').glob('*.json'):
 r=json.loads(p.read_text())
 if r['status']!='BLOCKED':continue
 systems=[PhysicalDrainageSystem(**{**x,'source_ids':tuple(x['source_ids']),'merge_history':tuple(x['merge_history'])}) for x in r['retained_physical']]
 row=dict(hru=r['hru'],error=r['error'],retained=systems and [dict(source=s.source_ids,hydraulic_class=s.hydraulic_class,drnres=s.drnres,infres=s.infres,allow_infiltration=s.allow_infiltration,summer=s.peil_sum,winter=s.peil_win) for s in systems])
 for n in [6,7]:
  try:
   lev,a=select_protected_candidate(systems,max_levels=n,require_swap_interface=True);row['minimum_tested_level_count']=len(lev);row['diagnostic_audit']=a;break
  except ValueError:pass
 out.append(row)
args.output.write_text(json.dumps(out,indent=2)+'\n')
print('remaining',len(out))
