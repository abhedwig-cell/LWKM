import json
import numpy as np
import pandas as pd
import pytest
from tools.hru_source_chain import sample_raster,cache_valid,seal,fingerprint
from tools.lhm_postprocess import AsciiGrid
from tools.hru_incremental import impacted,row_fingerprints,reconcile_component
from tools.hru_context_cache import update
from tools.build_svat_from_rasters import build
from tools.hru_source_chain import sha


def test_dependency_closure_crosses_old_and_new_cluster_districts():
    a=pd.DataFrame({'svat':[1,2,3,4,5],'LDGB':[10,11,11,12,90],'LDGBclus':[1,1,2,2,9],'value':[0]*5})
    b=a.copy();b.loc[0,'value']=1
    m=pd.DataFrame({'svat':[1,2,3,4,5],'HRU':[1,1,2,2,3]})
    r=impacted(a,b,m)
    assert r['changed_svats']==[1]
    assert r['recompute_svats']==[1,2,3,4]
    assert r['affected_existing_hrus']==[1,2] and r['reusable_existing_hrus']==[3]
    assert impacted(a,b,m,algorithm_changed=True)['recompute_svats']==[1,2,3,4,5]


def test_removed_member_and_lookup_changes_invalidate():
    a=pd.DataFrame({'svat':[1,2],'LDGB':[10,10],'LDGBclus':[1,1]})
    m=pd.DataFrame({'svat':[1,2],'HRU':[1,2]})
    r=impacted(a,a.iloc[:1],m)
    assert r['changed_svats']==[2] and r['affected_existing_hrus']==[1,2]
    assert impacted(a,a,m,global_lookup_changed=True)['recompute_svats']==[1,2]


def test_component_id_reconciliation_preserves_outside_and_tombstones():
    old=pd.DataFrame({'svat':[1,2,3,4,5],'HRU':[10,10,11,11,99]})
    c=pd.DataFrame({'svat':[1,2,3,4],'HRU':[1,1,2,2]})
    out,report=reconcile_component(old,c)
    assert out.HRU.tolist()==old.HRU.tolist() and report['untouched_hrus']==1
    c.loc[c.svat.eq(2),'HRU']=2
    out,report=reconcile_component(old,c)
    assert out.loc[out.svat.eq(5),'HRU'].item()==99
    assert report['new_hru_ids']==[100,101] and report['retired_hru_ids']==[10,11]
    with pytest.raises(ValueError,match='cuts through'):reconcile_component(old,c.iloc[:1])


def test_identity_is_required_for_incremental_cache():
    with pytest.raises(ValueError):row_fingerprints(pd.DataFrame({'svat':[1,1]}))


def test_stage_reuse_checks_bytes_and_identity(tmp_path):
    (tmp_path/'data').write_text('exact')
    seal(tmp_path,'abc',{},'RESEARCH')
    assert cache_valid(tmp_path,'abc')
    with pytest.raises(ValueError,match='Changed stage'):cache_valid(tmp_path,'new')
    (tmp_path/'data').write_text('modified')
    with pytest.raises(ValueError,match='Corrupt'):cache_valid(tmp_path,'abc')


def test_pixel_centres_nodata_and_domain_extent():
    g=AsciiGrid(np.array([[1.,-9999.],[3.,4.]]),2,2,0,0,250)
    f=pd.DataFrame({'xc(m)':[125,375],'yc(m)':[375,125]})
    assert sample_raster(g,f).tolist()==[1,4]
    f.loc[0,'xc(m)']=126
    with pytest.raises(ValueError,match='aligned'):sample_raster(g,f)
    with pytest.raises(ValueError,match='Missing'):sample_raster(g,pd.DataFrame({'xc(m)':[375],'yc(m)':[375]}))
    with pytest.raises(ValueError,match='Outside'):sample_raster(g,pd.DataFrame({'xc(m)':[625],'yc(m)':[375]}))
    # Default numpy relative tolerance must not admit metre-scale offsets at
    # high national-grid column numbers.
    large=AsciiGrid(np.ones((1,1200)),1200,1,0,0,250)
    with pytest.raises(ValueError,match='aligned'):sample_raster(large,pd.DataFrame({'xc(m)':[250126.],'yc(m)':[125.]}))


def test_incremental_assets_do_not_render_unchanged_and_rollback(tmp_path):
    calls=[]
    def render(c):calls.append(c);return str(c['value'])
    records=[dict(run_id=i,context={'value':i}) for i in [1,2,3]]
    db=tmp_path/'cache.sqlite'
    first=update(records,db,'v1',render);assert first['written']==3
    calls.clear();second=update(records,db,'v1',render)
    assert second['reused']==3 and calls==[]
    changed=[dict(r) for r in records];changed[1]=dict(run_id=2,context={'value':20})
    third=update(changed,db,'v1',render)
    assert third['written']==1 and third['reused']==2 and calls==[{'value':20}]
    assert update(changed,db,'v2',render)['written']==3
    import sqlite3
    with sqlite3.connect(db) as con:con.execute('update assets set sha256=? where run_id=1',('bad',))
    with pytest.raises(ValueError,match='Corrupt'):update(changed,db,'v2',render)


def test_raster_producer_rejects_missing_and_misaligned_sources(tmp_path):
    def raster(name,values,cell=250):
        p=tmp_path/name
        p.write_text(f'ncols 2\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize {cell}\nNODATA_value -9999\n{values}\n')
        return dict(path=str(p),sha256=sha(p),logical_id=name,units='category',semantic_role=name)
    ids=raster('ids.asc','101 102');lu=raster('lu.asc','1 2')
    plan=dict(svat_raster=ids,columns={'lu2':lu},required_columns=['svat','lu2'])
    p=tmp_path/'plan.json';p.write_text(json.dumps(plan))
    frame=build(p,tmp_path/'ok');assert len(frame)==2 and frame.is_lwkm_domain.all()
    plan['columns']['lu2']=raster('lu.asc','1 -9999');p.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='Missing required'):build(p,tmp_path/'missing')
    assert json.loads((tmp_path/'missing/blocker.json').read_text())['missing_by_field']=={'lu2':1}
    plan['columns']['lu2']=raster('lu.asc','1 2',500);p.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='geometry'):build(p,tmp_path/'geometry')
