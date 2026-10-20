"""Restore required fields verbatim from normalized source-bound test records."""
import csv,gzip,sys
from pathlib import Path
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
with gzip.open(src,'rt',newline='') as f,(out/'area.inp').open('w') as a,(out/'mapping.csv').open('w',newline='') as m:
 w=csv.writer(m);w.writerow(['svat_orig','HRU','x','y'])
 for r in csv.DictReader(f):
  a.write(f"{r['svat_orig']} {r['area_m2']} 0 0 0 0 0 0 0 {r['x']} {r['y']} 0 0 0\n")
  w.writerow([r['svat_orig'],r['HRU'],r['x'],r['y']])
