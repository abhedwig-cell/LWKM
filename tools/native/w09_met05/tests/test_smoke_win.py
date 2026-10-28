from pathlib import Path
import subprocess,tempfile
import sys
base=Path(sys.argv[1]).resolve().parent
with tempfile.TemporaryDirectory() as d:
 p=Path(d)
 header='ncols 4\nnrows 4\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n'
 (p/'weights.csv').write_text('hru_id,grid_id,area_m2,weight\n'+''.join(f'{i},0,1,1\n' for i in range(1,10243)))
 for day in ['19700101','19700102']:
  for v in ['RD1','EV24','TN','TX','Q','FG','WIND','WET_RAW']:
   a={'RD1':2,'EV24':1,'TN':3,'TX':6,'Q':100,'FG':0.6,'WIND':2,'WET_RAW':0.5}[v]
   vals=[-9999,a,a,a]+[a]*12
   (p/f'{v}_{day}.asc').write_text(header+' '.join(map(str,vals))+'\n')
 cfg=['weights=weights.csv','template=RD1_19700101.asc','output_met=out','start_year=1970','end_year=1970','start_date=19700101','end_date=19700102']
 for v in ['RD1','EV24','TN','TX','Q','FG','WIND','WET_RAW']:
  cfg+= [f'path_{v}={v}_{{date}}.asc',f'scale_{v}=1']
 (p/'config.ini').write_text('\n'.join(cfg)+'\n')
 x=subprocess.run([str(Path(sys.argv[1]).resolve()),str(p/'config.ini')],capture_output=True,text=True)
 print('RETURN',x.returncode,x.stdout,x.stderr)
 assert x.returncode==0
 outputs=list((p/'out').glob('HRU_*.met'))
 assert len(outputs)==10242,len(outputs)
 data=(p/'out'/'HRU_00001.met').read_text().splitlines()
 assert len(data)==3,data
 assert data[1].endswith('100.000000 3.000000 6.000000 0.600000 2.000000 2.000000 1.000000 0.500000'),data
 assert all('.' in token for token in data[1].split()[4:]),data
 print('PASSED',len(outputs),'files,',len(data)-1,'days, values:',data[1])
 # A new release may have sparse, nonsequential HRU IDs, not 1..N.
 (p/'weights.csv').write_text('hru_id,grid_id,area_m2,weight\n101,0,1,1\n205,0,1,1\n9001,0,1,1\n')
 (p/'config.ini').write_text(('\n'.join(cfg)+'\n'+'release_binding_sha256='+('a'*64)+'\n').replace('output_met=out','output_met=out_sparse'))
 x=subprocess.run([str(Path(sys.argv[1]).resolve()),str(p/'config.ini')],capture_output=True,text=True)
 assert x.returncode==0,(x.stdout,x.stderr)
 sparse=list((p/'out_sparse').glob('HRU_*.met'))
 assert sorted(q.name for q in sparse)==['HRU_00101.met','HRU_00205.met','HRU_09001.met'],sparse
 assert 'HRUs=3' in (p/'out_sparse'/'MANIFEST.txt').read_text()
 assert 'release_binding_sha256='+('a'*64) in (p/'out_sparse'/'MANIFEST.txt').read_text()
 print('PASSED sparse nonconsecutive HRUs')
