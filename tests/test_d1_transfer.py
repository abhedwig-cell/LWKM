import json
from pathlib import Path
import pandas as pd
import pytest
from tools.production_transfer import receive
from tools.assemble_swap_package import sha256
from tools.work_d1 import forcing
from tests.test_d1_met_consumer import write_plan
from tools.met_grid_consumer import run

def groundwater(root):
    root.mkdir();p=root/'2020-02-29.csv'
    f=pd.DataFrame({'hru_id':[1,2],'date':['2020-02-29']*2,'flf_mm_d':[1.,2.],'frf_mm_d':[2.,3.],
                    'fff_mm_d':[3.,-3.],'ghb_mm_d':[4.,0.],'wel_mm_d':[-5.,-1.],'q_ext_mm_d':[5.,1.]})
    f.to_csv(p,index=False);source=root/'source.json';source.write_text('{"identity":"synthetic five-component fixture"}')
    cfg=dict(schema_version=1,product_kind='BBC',dataset_id='TEST',population_sha256='a'*64,source_manifest_sha256=sha256(source),source_manifest_path=source.name,
             producer_sha256='b'*64,units='mm/day_positive_into_L1',start='2020-02-29',end='2020-02-29',
             files=[dict(date='2020-02-29',path=p.name,sha256=sha256(p))],hru_ids=[1,2],status='RESEARCH_CANDIDATE')
    manifest=root/'transfer.json';manifest.write_text(json.dumps(cfg));return manifest

def test_received_met_bbc_join_and_unchanged_restart(tmp_path):
    metroot=tmp_path/'met';run(write_plan(tmp_path/'grid'),metroot)
    bbcroot=tmp_path/'bbc';manifest=groundwater(bbcroot)
    mdir=tmp_path/'import-met';bdir=tmp_path/'import-bbc'
    assert receive(metroot/'transfer.json',metroot,mdir)['errors']==[]
    assert receive(manifest,bbcroot,bdir)['errors']==[]
    assert receive(manifest,bbcroot,bdir)['files'][0]['reused']
    accepted=[json.loads((p/'accepted-manifest.json').read_text()) for p in [mdir,bdir]]
    first=forcing(accepted,tmp_path/'daily.sqlite',tmp_path/'forcing')
    second=forcing(accepted,tmp_path/'daily.sqlite',tmp_path/'forcing')
    assert first['changed_shards_indexed']==2 and second['changed_shards_indexed']==0
    assert all(x['reused'] for x in second['runs'])
    assert '2020-02-29 0.5' in (tmp_path/'forcing/1.bbc').read_text()
    assert not first['production_admitted']

@pytest.mark.parametrize('damage',['hash','missing','sum','ids','date','duplicate','traversal','source_manifest'])
def test_import_fails_closed_and_clears_old_acceptance(tmp_path,damage):
    root=tmp_path/'bbc';manifest=groundwater(root);dest=tmp_path/'import';receive(manifest,root,dest)
    cfg=json.loads(manifest.read_text());p=root/'2020-02-29.csv'
    if damage=='hash':cfg['files'][0]['sha256']='0'*64
    elif damage=='missing':p.unlink()
    elif damage=='traversal':cfg['files'][0]['path']='../escape'
    elif damage=='source_manifest':(root/'source.json').write_text('changed')
    else:
        f=pd.read_csv(p)
        if damage=='sum':f.loc[0,'q_ext_mm_d']=99
        if damage=='ids':f.loc[1,'hru_id']=3
        if damage=='date':f['date']='2020-03-01'
        if damage=='duplicate':f=pd.concat([f,f.iloc[:1]])
        f.to_csv(p,index=False);cfg['files'][0]['sha256']=sha256(p)
    manifest.write_text(json.dumps(cfg))
    try:r=receive(manifest,root,dest)
    except ValueError:
        # Top-level identity errors also invalidate a prior success marker.
        assert damage=='source_manifest'
        assert not (dest/'accepted-manifest.json').exists()
    else:
        assert r['status']=='IMPORT_BLOCKED'
        assert not (dest/'accepted-manifest.json').exists()
