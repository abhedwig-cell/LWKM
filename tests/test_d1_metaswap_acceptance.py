import csv
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import pytest

NAMES=['MSW_EBS','MSW_EIC','MSW_EPD','MSW_ESP','MSW_TACT','MSW_TPOT','PSSW','PSGW','BDGETACT']
DERIVED=['E_SOIL_POND','E_INTERCEPTION_SPRINKLING','T_ACTUAL','ET_ACTUAL','IRR_TOTAL','BDGETACT_MINUS_ET']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

@pytest.fixture(scope='session')
def reducer(tmp_path_factory):
    if os.environ.get('LWKM_ACCEPT_EXE'):return Path(os.environ['LWKM_ACCEPT_EXE']).resolve()
    compiler=shutil.which('g++')
    if compiler is None:pytest.skip('C++ compiler absent; use LWKM_ACCEPT_EXE for shipped binary')
    target=tmp_path_factory.mktemp('cpp')/'accept_metaswap'
    subprocess.run([compiler,'-std=c++17','-O2','tools/metaswap_hru/accept_metaswap.cpp','-lcrypto','-o',str(target)],check=True)
    return target

def fixture(root,n=2):
    root.mkdir();src=root/'sources.csv'
    with src.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['date','variable','relative_path'])
        for date in ['20200220','20200229']:
            for name in NAMES:
                path=root/(date+'_'+name+'.idf');path.write_bytes((date+name).encode())
                w.writerow([date,name,path.name])
    data=root.parent/'data';data.mkdir(exist_ok=True)
    (data/'area_svat.inp').write_text(''.join(f'{i*2+j} {50*i} 0 0 0 0 0 0 0 125 125 0 0 0\n' for i in range(1,n+1) for j in [0,1]))
    (data/'svat_hru.csv').write_text('svat_orig,HRU,x,y\n'+''.join(f'{i*2+j},{i},125,125\n' for i in range(1,n+1) for j in [0,1]))
    exe=root.parent/'lwkm_metaswap_hru.exe';exe.write_bytes(b'synthetic producer identity')
    base='LWKM-MSW-HRU-1.0.0\nexe='+sha(exe)+'\narea='+sha(data/'area_svat.inp')+'\nmapping='+sha(data/'svat_hru.csv')+'\nsources='+sha(src)+'\nunits=m3/m2_per_decade;factor=1000;sign=source;missing=blank_strict_support\n'
    (root/'run_identity.txt').write_text(base)
    (root/'hru_support.csv').write_text('hru_id,svats,area_m2\n'+''.join(f'{i},2,{100*i}\n' for i in range(1,n+1)))
    for date,days in [('20200220',10),('20200229',9)]:
        with (root/(date+'.csv')).open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['hru_id','days','complete',*NAMES,*DERIVED,*['coverage_'+s for s in NAMES]])
            for h in range(1,n+1):
                raw=[-1,-2,-3,-4,-5,-6,7,8,-15]
                w.writerow([h,days,1,*raw,-4,-6,-5,-15,15,0,*([1]*9)])
        (root/(date+'_qc.csv')).write_text('variable,positive_svat_values,negative_svat_values\n'+''.join(f'{name},0,{n*2}\n' for name in NAMES))
        sources=''.join(f'{name},{(root/(date+"_"+name+".idf")).as_posix()},{len((date+name).encode())},{sha(root/(date+"_"+name+".idf"))}\n' for name in NAMES)
        (root/(date+'.sha256')).write_text(base+'date='+date+'\n'+sources+'output='+sha(root/(date+'.csv'))+'\nqc='+sha(root/(date+'_qc.csv'))+'\n')
    return src

def execute(binary,root,src,dest,n=2,*args):
    return subprocess.run([str(binary),str(root),str(src),str(dest),str(n),*args],capture_output=True,text=True)

def test_compact_full_population_configured_partial_year(reducer,tmp_path):
    root=tmp_path/'output with spaces';src=fixture(root,10242);dest=tmp_path/'compact'
    r=execute(reducer,root,src,dest,10242);assert r.returncode==0,r.stderr
    rows=list(csv.DictReader((dest/'annual_hru.csv').open()))
    assert len(rows)==10242 and rows[-1]['ET_ACTUAL']=='-30' and rows[-1]['full_calendar_year']=='0'
    assert rows[-1]['configured_decades']=='2'
    seasons=list(csv.DictReader((dest/'seasonal_population.csv').open()))
    assert seasons[0]['ET_ACTUAL']=='-30'
    decades=list(csv.DictReader((dest/'decadal_population.csv').open()))
    assert decades[1]['days']=='9' and decades[0]['MSW_TPOT']=='-6'
    assert 'source_rehash_verified=1' in (dest/'acceptance.txt').read_text()
    from tools.accept_compact_metaswap import verify
    report=verify(dest)
    assert report['production_admitted'] is False and report['decades']==2

@pytest.mark.parametrize('damage',['source','output','missing_hru','duplicate','derived','nan','coverage','period_gap','marker_identity','area_input','mapping_input','producer_input','support'])
def test_reject_corrupt_or_inconsistent_products(reducer,tmp_path,damage):
    root=tmp_path/'out';src=fixture(root);dest=tmp_path/'compact';d='20200229';p=root/(d+'.csv')
    if damage in ['area_input','mapping_input','producer_input']:
        path={'area_input':root.parent/'data/area_svat.inp','mapping_input':root.parent/'data/svat_hru.csv','producer_input':root.parent/'lwkm_metaswap_hru.exe'}[damage]
        path.write_bytes(path.read_bytes()+b'changed')
    elif damage=='support':(root/'hru_support.csv').write_text('hru_id,svats,area_m2\n1,2,101\n2,2,200\n')
    elif damage=='source':(root/(d+'_MSW_EBS.idf')).write_text('changed')
    elif damage=='output':p.write_text(p.read_text()+'corrupted\n')
    elif damage=='period_gap':
        src.write_text(src.read_text().replace('20200229','20200320'))
    elif damage=='marker_identity':
        q=root/(d+'.sha256');q.write_text(q.read_text().replace('area=', 'area=bad'))
    else:
        data=list(csv.reader(p.open()))
        if damage=='missing_hru':data.pop()
        if damage=='duplicate':data[-1][0]='1'
        if damage=='derived':data[-1][15]='-99'
        if damage=='nan':data[-1][3]='nan'
        if damage=='coverage':data[-1][18]='0.5'
        old=sha(p)
        with p.open('w',newline='') as f:csv.writer(f).writerows(data)
        marker=root/(d+'.sha256');marker.write_text(marker.read_text().replace('output='+old,'output='+sha(p)))
    r=execute(reducer,root,src,dest)
    assert r.returncode==1 and not (dest/'COMPLETE.txt').exists(),(r.stdout,r.stderr)

def test_explicit_recorded_hash_mode_does_not_claim_source_rehash(reducer,tmp_path):
    root=tmp_path/'out';src=fixture(root);dest=tmp_path/'compact'
    for p in root.glob('*.idf'):p.unlink()
    r=execute(reducer,root,src,dest,2,'--recorded-sources-only')
    assert r.returncode==0 and 'source_rehash_verified=0' in (dest/'acceptance.txt').read_text()

def test_missing_values_are_retained_not_renormalized(reducer,tmp_path):
    root=tmp_path/'out';src=fixture(root);dest=tmp_path/'compact';p=root/'20200229.csv'
    rows=list(csv.reader(p.open()));r=rows[-1];r[2]='0'
    for ix in [3,12,15,17]:r[ix]=''
    r[18]='0.5';before=sha(p)
    with p.open('w',newline='') as f:csv.writer(f).writerows(rows)
    marker=root/'20200229.sha256';marker.write_text(marker.read_text().replace('output='+before,'output='+sha(p)))
    process=execute(reducer,root,src,dest);assert process.returncode==2,process.stderr
    annual=list(csv.DictReader((dest/'annual_hru.csv').open()))
    assert annual[-1]['ET_ACTUAL']=='' and annual[-1]['MSW_TPOT']=='-12'
    assert 'incomplete_hru_decades=1' in (dest/'acceptance.txt').read_text()
