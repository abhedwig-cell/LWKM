import csv
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from tools.server.produce_dra_from_nhi import generate,months,ROOT
from tools.server.check_swp_source_values import sha


def fixture(tmp_path,monkeypatch):
    source=json.loads((ROOT/'config/dra/server_sources_20261030.json').read_text())
    def raster(name,value):
        p=tmp_path/(name+'.asc')
        p.write_text('ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n'+str(value)+'\n')
        return dict(path=str(p),sha256=sha(p))
    for role in source['sources']:
        value=1000 if role.endswith('_cdr') else .5 if role.endswith('_inf') else 200 if role=='glk' else 1 if role.endswith('_sum') else .5 if role.endswith('_win') else 0
        source['sources'][role]=raster(role,value)
    source['stages']={day:raster(day,1+j*.01) for j,day in enumerate(months('1971-01-01','1971-12-31'))}
    dq=raster('dqsat',13);source['dqsat_grid']=dq
    for module in ('tools.server.dqsat_source','tools.server.produce_dra_from_nhi'):
        monkeypatch.setattr(module+'.DQSAT_SHA256',dq['sha256'])
    binding=tmp_path/'binding.json';binding.write_text(json.dumps(source))
    hru=tmp_path/'hru.csv';hru.write_text('HRU,svat_repr,bodem370,lu4\n1,10,261,3\n')
    membership=tmp_path/'members.csv.gz'
    with gzip.open(membership,'wt') as f:f.write('svat,HRU,x,y\n10,1,125,125\n')
    return (binding,hru,membership,ROOT/'config/swp/lookup_catalog.json.gz',tmp_path/'output','1971-01-01','1971-12-31',1)


def test_actual_month_axis_and_direct_render_resume(tmp_path,monkeypatch):
    args=fixture(tmp_path,monkeypatch)
    report=generate(*args)
    assert report['generated']==1 and report['failed']==0
    text=(tmp_path/'output/dra/1.dra').read_text()
    assert '01-jan-1971' in text and '01-jan-1972' in text
    with gzip.open(tmp_path/'output/hrus/1.json.gz','rt') as f:rec=json.load(f)
    assert rec['dqsat']['positive_median']==13
    assert all(level['dd']==52 for level in rec['levels'])
    assert any(level['medium']=='drain_tube' for level in rec['levels'])
    assert all(len(level['source_ids'])==1 for level in rec['levels'] if level['medium']=='drain_tube')
    h1=next(s for s in rec['physical'] if s['source_ids']==['H1'])
    assert len(h1['level_series'])==13
    assert h1['level_series'][0][1]!=h1['level_series'][-1][1]
    repeated=generate(*args)
    assert repeated['reused_hrus']==1 and repeated['reused_h1_months']==13
    assert (tmp_path/'output/dra/1.dra').read_text()==text


def test_missing_month_and_changed_source_stop(tmp_path,monkeypatch):
    args=fixture(tmp_path,monkeypatch);binding=args[0]
    source=json.loads(binding.read_text());source['stages'].pop('1971-07-01')
    binding.write_text(json.dumps(source))
    with pytest.raises(ValueError,match='missing H1 source months'):generate(*args)
    source['stages']['1971-07-01']=source['stages']['1971-06-01']
    binding.write_text(json.dumps(source))
    Path(source['sources']['P_cdr']['path']).write_text('changed')
    with pytest.raises(ValueError,match='changed source'):generate(*args)


def test_damaged_month_cache_cannot_be_reused(tmp_path,monkeypatch):
    args=fixture(tmp_path,monkeypatch);generate(*args)
    path=next((tmp_path/'output/cache').glob('*/1971-01-01.json'))
    rec=json.loads(path.read_text());rec['depths']=[99.]
    path.write_text(json.dumps(rec))
    with pytest.raises(ValueError,match='month cache changed'):generate(*args)


def test_national_period_includes_endpoint_without_extending_simulation():
    axis=months('1970-01-01','2022-12-31')
    assert len(axis)==637 and axis[0]=='1970-01-01' and axis[-1]=='2023-01-01'
