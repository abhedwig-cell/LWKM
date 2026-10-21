"""Qualification of native exporter. EXE WORK [REAL_UPLOAD_DIRECTORY]."""
import csv, hashlib, io, json, os, shutil, subprocess, sys, time, zipfile
from pathlib import Path
EXE=Path(sys.argv[1]).resolve(); WORK=Path(sys.argv[2]).resolve(); WORK.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
PILOT=HERE/'pilot-hrus.csv'
IDS={int(r['hru_id']) for r in csv.DictReader(PILOT.open())}
NAMES='MSW_EBS MSW_EIC MSW_EPD MSW_ESP MSW_TACT MSW_TPOT PSSW PSGW BDGETACT'.split()
DERIVED='E_SOIL_POND E_INTERCEPTION_SPRINKLING T_ACTUAL ET_ACTUAL IRR_TOTAL BDGETACT_MINUS_ET'.split()
HEADER=['hru_id','days','complete']+NAMES+DERIVED+['coverage_'+n for n in NAMES]
IDENTITY='LWKM-MSW-HRU-1.0.0\n'+''.join(k+'='+'a'*64+'\n' for k in ['exe','area','mapping','sources'])+'units=m3/m2_per_decade;factor=1000;sign=source;missing=blank_strict_support\n'
RESULTS=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fixmarker(src,d):
    (src/(d+'.sha256')).write_text(IDENTITY+'date='+d+'\n'+''.join(n+',G:/source.idf,1,'+'b'*64+'\n' for n in NAMES)+'output='+sha(src/(d+'.csv'))+'\nqc='+sha(src/(d+'_qc.csv'))+'\n')
def fixture(src,dates):
    src.mkdir(parents=True);(src/'run_identity.txt').write_text(IDENTITY)
    (src/'hru_support.csv').write_text('hru_id,svats,area_m2\n'+''.join(f'{i},1,100\n' for i in sorted(IDS|{1})))
    for d in dates:
        with (src/(d+'.csv')).open('w',newline='') as f:
            w=csv.writer(f);w.writerow(HEADER)
            for i in sorted(IDS|{1}): w.writerow([i,10 if d[-2:] in ['10','20'] else int(d[-2:])-20,1]+['-1.0000000000']*6+['0','0','-5']+['-2','-2','-1','-5','0','0']+['1']*9)
        (src/(d+'_qc.csv')).write_text('diagnostic,value\nincomplete,0\n');fixmarker(src,d)
def run(src,dst,first,last,ok=True):
    win=lambda p: 'Z:'+str(p).replace('/','\\')
    args=[str(src),str(dst),str(PILOT),first,last]
    if os.name!='nt' and EXE.suffix=='.exe':args=[os.environ['WINE'],str(EXE)]+[win(Path(p)) for p in args[:3]]+args[3:]
    else:args=[str(EXE)]+args
    existed=(dst/'COMPLETE.txt').exists()
    t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True,timeout=120)
    assert (p.returncode==0)==ok,(p.returncode,p.stdout,p.stderr)
    assert (dst/'COMPLETE.txt').exists()==(ok or existed)
    return time.monotonic()-t

def record(name,**kw):RESULTS.append(dict(test=name,status='PASS',**kw));print(name,'PASS',flush=True)
src=WORK/'source with spaces';fixture(src,['20200220','20200229','20200310']);out=WORK/'valid'
before={p.name:sha(p) for p in src.iterdir()}
secs=run(src,out,'20200220','20200310')
rows=list(csv.DictReader((out/'HRU21_reference.csv').open()));assert len(rows)==63 and rows[21]['days']=='9'
assert {int(r['hru_id']) for r in rows}==IDS and all(r['MSW_EBS']=='-1.0000000000' for r in rows)
assert before=={p.name:sha(p) for p in src.iterdir()}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1);assert sha(out/n)==h
record('three_decades_leap_day_raw_text_hashes_read_only_spaces',seconds=secs)
run(src,out,'20200220','20200310',False);record('reject_existing_destination')
for name,mutation in [
 ('hash_mismatch',lambda s:(s/'20200220.csv').write_text('corrupt')),
 ('missing_period',lambda s:(s/'20200229.csv').unlink()),
 ('duplicate_hru',lambda s:(s/'20200220.csv').write_text((s/'20200220.csv').read_text()+(s/'20200220.csv').read_text().splitlines()[1]+'\n')),
 ('missing_hru',lambda s:(s/'20200220.csv').write_text('\n'.join((s/'20200220.csv').read_text().splitlines()[:-1])+'\n')),
 ('wrong_days',lambda s:(s/'20200220.csv').write_text((s/'20200220.csv').read_text().replace(',10,1,',',9,1,'))),
 ('coverage_contradiction',lambda s:(s/'20200220.csv').write_text((s/'20200220.csv').read_text().replace(',1,1,1,1,1,1,1,1,1',',0.5,1,1,1,1,1,1,1,1'))),
 ('qc_hash_mismatch',lambda s:(s/'20200220_qc.csv').write_text('corrupt'))]:
    bad=WORK/name;shutil.copytree(src,bad);mutation(bad)
    if name not in ['hash_mismatch','qc_hash_mismatch','missing_period']:fixmarker(bad,'20200220')
    run(bad,WORK/(name+'_out'),'20200220','20200310',False);record('reject_'+name)
bad=WORK/'incomplete';shutil.copytree(src,bad)
p=bad/'20200220.csv';r=list(csv.reader(p.open()));r[2][2]='0';r[2][3]='';r[2][18]='0.5';r[2][12]='';r[2][15]='';r[2][17]=''
with p.open('w',newline='') as f:csv.writer(f).writerows(r)
fixmarker(bad,'20200220');run(bad,WORK/'incomplete_out','20200220','20200310')
r=list(csv.DictReader((WORK/'incomplete_out/reference/20200220.csv').open()));assert r[0]['MSW_EBS']=='' and r[0]['coverage_MSW_EBS']=='0.5'
record('preserve_incomplete_no_renormalization')
if len(sys.argv)>3:
    upload=Path(sys.argv[3]);real=WORK/'real';real.mkdir()
    with zipfile.ZipFile(upload/'20241210.zip') as z:
        for n in ['run_identity.txt','hru_support.csv','20241210.sha256','20241210_qc.csv']:(real/n).write_bytes(z.read(n))
    shutil.copyfile(upload/'20241210.csv',real/'20241210.csv')
    secs=run(real,WORK/'real_out','20241210','20241210')
    originals={int(r['hru_id']):r for r in csv.DictReader((real/'20241210.csv').open())}
    selected=list(csv.DictReader((WORK/'real_out/reference/20241210.csv').open()));assert len(selected)==21
    assert all(r==originals[int(r['hru_id'])] for r in selected)
    record('real_10242_hrus_21_exact_values',seconds=secs,source_sha256=sha(real/'20241210.csv'),selected_bytes=(WORK/'real_out/reference/20241210.csv').stat().st_size)
# Native Windows verifies the actual PowerShell wrapper and ZIP content, too.
if os.name=='nt':
    bundle=WORK/'wrapper';bundle.mkdir()
    for n in ['export_hru21.ps1','pilot-hrus.csv']:shutil.copyfile(HERE/n,bundle/n)
    shutil.copyfile(EXE,bundle/'export_hru21.exe')
    subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(bundle/'export_hru21.ps1'),str(src),'20200220','20200310'],check=True)
    zips=list(bundle.glob('*.zip'));assert len(zips)==1
    with zipfile.ZipFile(zips[0]) as z:assert any(n.endswith('/COMPLETE.txt') for n in z.namelist())
    record('native_windows_powershell_zip_wrapper')
(WORK/'qualification.json').write_text(json.dumps({'platform':sys.platform,'binary_sha256':sha(EXE),'results':RESULTS},indent=2)+'\n')
