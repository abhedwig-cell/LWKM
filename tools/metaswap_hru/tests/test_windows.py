"""Execute the actual PE32+ binary under Wine, independently verify arithmetic.
Python/numpy are development dependencies only, never server dependencies.
Usage: python test_windows.py EXE WORKDIR AREA_SVAT SVAT_HRU
WINE defaults to wine64. Keep WINEPREFIX outside source checkout.
"""
import csv, hashlib, json, os, shutil, struct, subprocess, sys, time
from pathlib import Path
import numpy as np

EXE, WORK, AREA, MAP = map(lambda x: Path(x).resolve(), sys.argv[1:])
WORK.mkdir(parents=True, exist_ok=True)
NAMES=['MSW_EBS','MSW_EIC','MSW_EPD','MSW_ESP','MSW_TACT','MSW_TPOT','PSSW','PSGW','BDGETACT']
RESULTS=[]
WINE=os.environ.get('WINE','wine64')

def win(p): return str(Path(p).resolve()) if os.name=='nt' else 'Z:'+str(Path(p).resolve()).replace('/','\\')
def run(a,m,s,root,out,n=2,success=True):
    t=time.monotonic()
    p=subprocess.run((([str(EXE)] if os.name=='nt' else [WINE,str(EXE)])+[win(a),win(m),win(s),win(root),win(out),str(n)]),capture_output=True,text=True,timeout=240)
    assert (p.returncode==0)==success, (p.returncode,p.stdout,p.stderr)
    return p.stdout+p.stderr,time.monotonic()-t

def record(name,**kw):
    RESULTS.append(dict(test=name,status='PASS',**kw)); print(name,'PASS',flush=True)

def writeidf(p,v,xmin=0,ymin=0,dx=250):
    v=np.asarray(v,dtype='<f4'); nr,nc=v.shape
    h=struct.pack('<3i7fBBH2f',1271,nc,nr,xmin,xmin+nc*dx,ymin,ymin+nr*dx,float(v.min()),float(v.max()),-9999.,0,0,0,dx,dx)
    p.write_bytes(h+v.tobytes())

def sources(root,dates):
    p=root/'sources.csv'
    with p.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['date','variable','relative_path'])
        for d in dates:
            for j,name in enumerate(NAMES): w.writerow([d,name,f'{d}_{name}.idf'])
    return p

def rows(p): return list(csv.DictReader(p.open()))

small=WORK/'small';small.mkdir(exist_ok=True)
a=small/'area.inp';m=small/'mapping.csv'
# Four SVATs, unequal weights, two HRUs, two members share one raster cell.
a.write_text('1 100 0 0 0 0 0 0 0 125 375 0 0 0\n2 300 0 0 0 0 0 0 0 375 375 0 0 0\n3 50 0 0 0 0 0 0 0 125 125 0 0 0\n4 150 0 0 0 0 0 0 0 125 375 0 0 0\n')
m.write_text('svat_orig,HRU,x,y\n1,1,125,375\n2,1,375,375\n3,2,125,125\n4,2,125,375\n')
coeff=np.array([-.001,-.002,-.003,-.004,-.005,-.006,.007,.008,-.015])
for date in ['20200220','20200229']:
    for j,name in enumerate(NAMES): writeidf(small/f'{date}_{name}.idf',np.array([[1,3],[5,7]])*coeff[j])
s=sources(small,['20200220','20200229']);out=small/'out'
text,secs=run(a,m,s,small,out)
r=rows(out/'20200229.csv');assert len(r)==2 and r[0]['days']=='9'
for k,factor in enumerate([2.5,2.]):
    for j,name in enumerate(NAMES): assert abs(float(r[k][name])-coeff[j]*factor*1000)<2e-6
    assert abs(float(r[k]['ET_ACTUAL'])+15*factor)<2e-6
    assert abs(float(r[k]['BDGETACT_MINUS_ET']))<2e-6
record('weighted_aggregation_orientation_shared_cell_leap_decade',runtime_seconds=secs)
identity=(out/'20200229.sha256').read_text();assert 'output='+hashlib.sha256((out/'20200229.csv').read_bytes()).hexdigest() in identity
assert 'area='+hashlib.sha256(a.read_bytes()).hexdigest() in identity
record('sha256_matches_independent_python')
mt=(out/'20200229.csv').stat().st_mtime_ns
text,_=run(a,m,s,small,out);assert 'verified_existing=2' in text and (out/'20200229.csv').stat().st_mtime_ns==mt
record('resume_verifies_and_skips_unchanged')
(out/'20200229.csv').write_text('damaged\n');text,_=run(a,m,s,small,out);assert 'new=1' in text and len(rows(out/'20200229.csv'))==2
record('resume_repairs_corrupt_output')
(out/'20200229_qc.csv').unlink();text,_=run(a,m,s,small,out);assert 'new=1' in text and (out/'20200229_qc.csv').exists()
record('resume_repairs_missing_quality_file')
p=small/'20200229_MSW_EBS.idf';v=np.array([[1,3],[5,7]])*coeff[0];v[0,1]=-9999.;writeidf(p,v)
text,_=run(a,m,s,small,out);r=rows(out/'20200229.csv');assert r[0]['MSW_EBS']=='' and r[0]['E_SOIL_POND']=='' and r[0]['ET_ACTUAL']=='' and r[0]['BDGETACT_MINUS_ET']==''
assert r[0]['complete']=='0' and abs(float(r[0]['coverage_MSW_EBS'])-.25)<1e-12 and r[0]['MSW_EIC']!='' and r[1]['complete']=='1'
record('changed_source_hash_recomputes_and_nodata_propagates_per_variable')
v[0,1]=np.nan;writeidf(p,v);run(a,m,s,small,out);assert rows(out/'20200229.csv')[0]['MSW_EBS']==''
record('nan_remains_missing')
# Interrupted CSV without committed hash is recomputed.
(out/'20200229.sha256').unlink();(out/'20200229.csv.partial').write_text('interrupted');text,_=run(a,m,s,small,out);assert 'new=1' in text
record('restart_after_uncommitted_partial')
for test,content in [('duplicate_svat','svat_orig,HRU,x,y\n1,1,125,375\n1,2,125,375\n'),('coordinate_mismatch','svat_orig,HRU,x,y\n1,1,126,375\n2,2,375,375\n'),('unknown_svat','svat_orig,HRU,x,y\n999,1,125,375\n2,2,375,375\n')]:
    bad=small/'bad.csv';bad.write_text(content);run(a,bad,s,small,out,success=False);record('reject_'+test)
# No lock is left behind by a failed operation.
assert not (out/'.running').exists();record('failed_run_releases_exclusive_lock')
backup=p.read_bytes();p.unlink();run(a,m,s,small,out,success=False);p.write_bytes(backup);record('reject_missing_source_file')
p.write_bytes(struct.pack('<i',2295)+backup[4:]);run(a,m,s,small,out,success=False);p.write_bytes(backup);record('reject_unsupported_idf_precision')
p.write_bytes(backup[:60]);run(a,m,s,small,out,success=False);p.write_bytes(backup);record('reject_truncated_idf')
p.write_bytes(backup+struct.pack('<ii',1,2)+b'TEST    ');run(a,m,s,small,out);record('accept_documented_text_idf_footer')
p.write_bytes(backup+struct.pack('<ii',1,2)+b'\xffEST    ');run(a,m,s,small,out,success=False);p.write_bytes(backup);record('reject_invalid_idf_footer')
# Shift extent while keeping valid dimensions. Original coordinates now outside/offset.
b=bytearray(backup);struct.pack_into('<f',b,12,250.);struct.pack_into('<f',b,16,750.);p.write_bytes(b);run(a,m,s,small,out,success=False);p.write_bytes(backup);record('reject_shifted_or_outside_raster')
# Full supplied mapping, full actual SVAT areas. Independently sum by HRU.
full=WORK/'full';full.mkdir(exist_ok=True)
area={}
for line in AREA.open():
    z=line.split();area[int(z[0])]=(float(z[1]),float(z[9]),float(z[10]))
mm=rows(MAP);ids=np.array([int(z['svat_orig']) for z in mm]);hrus=np.array([int(z['HRU']) for z in mm]);aa=np.array([area[i][0] for i in ids]);xx=np.array([area[i][1] for i in ids]);yy=np.array([area[i][2] for i in ids])
xmin=float(xx.min()-125);ymin=float(yy.min()-125);nc=int((xx.max()-xx.min())/250)+1;nr=int((yy.max()-yy.min())/250)+1
cc=((xx-xmin)/250).astype(int);rr=((ymin+nr*250-yy)/250).astype(int)
grid=1+(np.arange(nc)[None,:]+3*np.arange(nr)[:,None])%17/20.
expected=[];den=np.bincount(hrus,weights=aa,minlength=10243)
for j,name in enumerate(NAMES):
    data=np.asarray(grid*coeff[j],dtype='<f4');writeidf(full/f'20240110_{name}.idf',data,xmin,ymin)
    expected.append(np.bincount(hrus,weights=data[rr,cc].astype(float)*aa*1000,minlength=10243)[1:]/den[1:])
ss=sources(full,['20240110']);ff=full/'out';text,secs=run(AREA,MAP,ss,full,ff,n=10242)
actual=rows(ff/'20240110.csv');assert len(actual)==10242
maxerr=0
for i,r in enumerate(actual):
    assert int(r['hru_id'])==i+1 and r['complete']=='1'
    vals=[expected[j][i] for j in range(9)]
    for j,name in enumerate(NAMES):
        maxerr=max(maxerr,abs(float(r[name])-vals[j]));assert abs(float(r[name])-vals[j])<5e-8
        assert r['coverage_'+name]=='1'
    derived={'E_SOIL_POND':vals[0]+vals[2],'E_INTERCEPTION_SPRINKLING':vals[1]+vals[3],'T_ACTUAL':vals[4],'ET_ACTUAL':sum(vals[:5]),'IRR_TOTAL':sum(vals[6:8]),'BDGETACT_MINUS_ET':vals[8]-sum(vals[:5])}
    for name,x in derived.items(): assert abs(float(r[name])-x)<5e-8
record('all_427656_supplied_svats_all_10242_hrus_vs_independent_numpy',runtime_seconds=secs,max_abs_csv_rounding_error_mm=maxerr,raster_rows=nr,raster_columns=nc)
# Artefacts with spatial geometry are copied without synthetic rasters (reproducible).
report={'binary_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'windows_execution':'native Windows x64' if os.name=='nt' else 'actual PE32+ x64 executable under Wine; not native Windows host','tests':RESULTS,'passed':len(RESULTS)}
(WORK/'test_results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
