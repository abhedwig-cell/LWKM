import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile
import pandas as pd
from tools.work_d1 import build_packages
from tools.daily_forcing import modern_met,effective_bbc,MET_COLUMNS
from tools.assemble_swap_package import sha256

def fixture(tmp_path):
    evidence=Path('docs/evidence')
    with gzip.open(evidence/'2026-10-19-work-b/interfaces/HRU_CONTEXT_10242.jsonl.gz','rt') as f:row=json.loads(next(f))
    ctx=tmp_path/'contexts.gz'
    with gzip.open(ctx,'wt') as f:f.write(json.dumps(row)+'\n')
    with gzip.open(evidence/'2026-10-19-work-c2/all-dra-files.jsonl.gz','rt') as f:dra=next(json.loads(line) for line in f if json.loads(line)['hru']==1)
    dp=tmp_path/'dras.gz'
    with gzip.open(dp,'wt') as f:f.write(json.dumps(dra)+'\n')
    with zipfile.ZipFile(evidence/'2026-10-19-work-c2/execution-evidence.zip') as z:
        index=json.loads(z.read('file-index.json'));member=index['packages/catalogue-executions/7870/fictief.crp'];data=z.read(member)
        assert hashlib.sha256(data).hexdigest()==member.split('/')[-1]
    crop=tmp_path/'fictief.crp';crop.write_bytes(data)
    asset=tmp_path/'assets.json';asset.write_text(json.dumps({'runs':{'1':{'is_nature':True,'assets':{'fictief.crp':{'path':str(crop),'sha256':sha256(crop)}}}}}))
    dates=['2020-02-28','2020-02-29'];weather=pd.DataFrame([dict(date=d,**dict(zip(MET_COLUMNS,[10000,10,20,1,3,0,1,0]))) for d in dates])
    met=tmp_path/'1.met';met.write_text(modern_met(weather,start=dates[0],end=dates[-1],station=1))
    bbc=tmp_path/'1.bbc';bbc.write_text(effective_bbc(pd.DataFrame(dict(date=dates,q_ext_mm_d=[1.,-1.])),start=dates[0],end=dates[-1]))
    pairs=dict(start=dates[0],end=dates[-1],source_manifests=['a'*64,'b'*64],runs=[dict(hru_id=1,assets={p.name:dict(path=str(p),sha256=sha256(p)) for p in [met,bbc]})])
    return ctx,Path('tests/fixtures/d1/wwl.swp'),dp,asset,pairs

def test_complete_real_source_package_with_synthetic_daily_forcing_and_reuse(tmp_path):
    args=fixture(tmp_path);checkpoints=Path('docs/evidence/2026-10-19-work-c2/drainage-checkpoints.jsonl.gz')
    first=build_packages(*args,tmp_path/'packages',expected_population=1,dra_checkpoints=checkpoints)
    assert first['complete_packages']==1,first
    second=build_packages(*args,tmp_path/'packages',expected_population=1,dra_checkpoints=checkpoints)
    assert second['reused_packages']==1
    package=Path(second['runs'][0]['package'])
    assert 'ALTW = 10.0' in (package/'swap.swp').read_text()
    assert 'LWKM_OWNER_DAILY_MEAN' in (package/'1.bbc').read_text()

def test_nature_automatic_irrigation_is_rejected(tmp_path):
    args=fixture(tmp_path);catalogue=json.loads(args[3].read_text());crop=tmp_path/'fictief.crp'
    crop.write_text(re.sub(r'(SCHEDULE\s*=\s*)0',r'\g<1>1',crop.read_text()))
    catalogue['runs']['1']['assets']['fictief.crp']['sha256']=sha256(crop);args[3].write_text(json.dumps(catalogue))
    result=build_packages(*args,tmp_path/'packages',expected_population=1)
    assert result['complete_packages']==0 and 'nature automatic irrigation forbidden' in result['runs'][0]['error']

def test_drainage_exception_has_no_historical_fallback(tmp_path):
    args=fixture(tmp_path)
    with gzip.open(args[2],'wt') as f:f.write('')
    r=build_packages(*args,tmp_path/'packages',expected_population=1)
    assert r['runs'][0]['error']=='C2_PROTECTED_DRAINAGE_EXCEPTION'
