import csv
import gzip
import json
from pathlib import Path
import pytest
from tools.server.check_swp_source_values import sha
from tools.server.produce_swp_from_nhi import generate,read_svat_values
from tools.swp_direct_render import Catalog
from tools.modern_swp import render

ROOT=Path(__file__).resolve().parents[1]
DQ_GRID='ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n13\n'


@pytest.fixture(autouse=True)
def source_identity(monkeypatch):
    import hashlib
    digest=hashlib.sha256(DQ_GRID.encode()).hexdigest()
    monkeypatch.setattr('tools.server.dqsat_source.DQSAT_SHA256',digest)
    monkeypatch.setattr('tools.server.produce_swp_from_nhi.DQSAT_SHA256',digest)



def table(path,records):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    return path


def fixture(tmp_path):
    sources={};digests={}
    for role,value in [('glk',200),('rds',120),('lgn',5),('bfe',261),('meteo',280),('irr_switch',0),('head',1)]:
        p=tmp_path/(role+'.asc');p.write_text(f'ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n{value}\n')
        sources[role]=dict(path=str(p));digests[role]=dict(sha256=sha(p))
    dqsat=tmp_path/'grensvlak_NHIWQ_v2_fill.asc';dqsat.write_text(DQ_GRID);sources['dqsat_grid']=dict(path=str(dqsat))
    # Deliberately unusable area raster: it must never be used as an area source.
    sources['area']=dict(path=str(tmp_path/'missing_UOPP.asc'))
    area=tmp_path/'area_svat.inp';area.write_text('10 45000 1 2 3 4 5 6 7 125 125 8 9 10\n')
    sources['area_svat']=dict(path=str(area))
    binding=tmp_path/'sources.json';binding.write_text(json.dumps(dict(sources=sources)))
    members=tmp_path/'members.csv.gz'
    with gzip.open(members,'wt') as f:
        w=csv.DictWriter(f,fieldnames=['svat','HRU','x','y','svat_area_m2']);w.writeheader();w.writerow(dict(svat=10,HRU=1,x=125,y=125,svat_area_m2=50000))
    hru=table(tmp_path/'hrus.csv',[dict(HRU=1,svat_repr=10,bodem370=261,lu4=3)])
    report=tmp_path/'values.json';report.write_text(json.dumps(dict(source_binding_sha256=sha(binding),membership_sha256=sha(members),sources=digests)))
    return binding,report,hru,members


def test_confirmed_sources_to_rendered_swp_uses_actual_area_and_correct_units(tmp_path):
    paths=fixture(tmp_path);output=tmp_path/'out'
    result=generate(*paths,ROOT/'config/swp/soil_classification_and_profile.csv',ROOT/'config/swp/four_landuse_crop_candidate.csv',output,'1970-01-01','2022-12-31',1)
    assert result['hrus']==1 and result['failed_hrus']==0
    with (output/'runs_candidate.csv').open() as f:row=next(csv.DictReader(f))
    assert (float(row['RDS']),float(row['GWLI']),float(row['area']),float(row['glk']))==(120,-100,45000,2)
    assert row['SWBOTB']=='2' and row['SWBBCFILE']=='1'
    diagnostics=json.loads((output/'diagnostics.json').read_text())
    assert 'ROOTZONE' in diagnostics[0]['root_source']
    context=Catalog(ROOT/'config/swp/lookup_catalog.json.gz').context(row)
    text=render((ROOT/'tests/fixtures/d1/wwl.swp').read_bytes(),context)
    assert '{{' not in text and '2022' in text


def test_changed_source_is_rejected(tmp_path):
    paths=fixture(tmp_path)
    p=tmp_path/'glk.asc';p.write_text(p.read_text().replace('\n200\n','\n201\n'))
    with pytest.raises(ValueError,match='changed since server check'):
        generate(*paths,ROOT/'config/swp/soil_classification_and_profile.csv',ROOT/'config/swp/four_landuse_crop_candidate.csv',tmp_path/'out','1970-01-01','2022-12-31',1)


def test_svat_values_not_row_order_and_duplicate_fails(tmp_path):
    p=tmp_path/'table.inp';p.write_text('20 8\n10 13\n')
    assert read_svat_values(p,{10})=={10:13}
    p.write_text('10 13\n10 8\n')
    with pytest.raises(ValueError,match='duplicate'):read_svat_values(p,{10})


def test_parameter_phase_reuse_requires_complete_unchanged_output(tmp_path):
    paths=fixture(tmp_path);out=tmp_path/'out'
    args=(*paths,ROOT/'config/swp/soil_classification_and_profile.csv',ROOT/'config/swp/four_landuse_crop_candidate.csv',out,'1970-01-01','2022-12-31',1)
    result=generate(*args)
    result['status']='SWP_INPUTS_GENERATED_NOT_SWAP_VALIDATED'
    (out/'production_manifest.json').write_text(json.dumps(result))
    assert generate(*args)['reused_parameter_phase']
    (out/'runs_candidate.csv').write_text('damaged')
    assert not generate(*args).get('reused_parameter_phase',False)


def test_zero_path_cli_generates_and_resumes_without_inventory_step(tmp_path,monkeypatch):
    import shutil
    import sys
    import zipfile
    import tools.server.produce_swp_from_nhi as producer
    paths=fixture(tmp_path)
    config=tmp_path/'config/swp';config.mkdir(parents=True)
    data=tmp_path/'source_data';data.mkdir()
    shutil.copyfile(paths[0],config/'server_locations_20261029.json')
    shutil.copyfile(paths[1],data/'source_values.json')
    shutil.copyfile(paths[2],data/'hrus.csv')
    shutil.copyfile(paths[3],data/'membership.csv.gz')
    for name in ('soil_classification_and_profile.csv','four_landuse_crop_candidate.csv','lookup_catalog.json.gz'):
        shutil.copyfile(ROOT/'config/swp'/name,config/name)
    template=tmp_path/'tests/fixtures/d1';template.mkdir(parents=True)
    shutil.copyfile(ROOT/'tests/fixtures/d1/wwl.swp',template/'wwl.swp')
    monkeypatch.setattr(producer,'ROOT',tmp_path)
    out=tmp_path/'production'
    monkeypatch.setattr(sys,'argv',['producer','--expected-hrus','1','--output',str(out)])
    assert producer.main()==0
    assert (out/'swp/1/1.swp').is_file()
    assert producer.main()==0
    manifest=json.loads((out/'production_manifest.json').read_text())
    assert manifest['reused_parameter_phase']
    rendered=json.loads((out/'swp/manifest.json').read_text())
    assert rendered['hrus'][0]['status']=='REUSED'
    with zipfile.ZipFile(out/'controle.zip') as z:
        assert set(z.namelist())=={'production_manifest.json','parameter_errors.json','diagnostics.json','swp/manifest.json','area_source_manifest.json','dqsat_source_manifest.json','dqsat_hru.csv','irrigation_allocation.json'}


def test_changed_area_file_invalidates_cached_parameters(tmp_path):
    paths=fixture(tmp_path);out=tmp_path/'out'
    args=(*paths,ROOT/'config/swp/soil_classification_and_profile.csv',ROOT/'config/swp/four_landuse_crop_candidate.csv',out,'1970-01-01','2022-12-31',1)
    result=generate(*args);result['status']='SWP_INPUTS_GENERATED_NOT_SWAP_VALIDATED'
    (out/'production_manifest.json').write_text(json.dumps(result))
    p=tmp_path/'area_svat.inp';p.write_text(p.read_text().replace('45000','42000'))
    updated=generate(*args)
    assert not updated.get('reused_parameter_phase',False)
    with (out/'runs_candidate.csv').open() as f:assert float(next(csv.DictReader(f))['area'])==42000


def test_missing_authoritative_raster_cannot_fall_back_to_svat_table(tmp_path):
    paths=fixture(tmp_path)
    (tmp_path/'grensvlak_NHIWQ_v2_fill.asc').unlink()
    (tmp_path/'dqsat_svat.inp').write_text('10 13\n')
    with pytest.raises(ValueError,match='not an approved substitute'):
        generate(*paths,ROOT/'config/swp/soil_classification_and_profile.csv',ROOT/'config/swp/four_landuse_crop_candidate.csv',tmp_path/'out','1970-01-01','2022-12-31',1)
    assert json.loads((tmp_path/'out/dqsat_source_manifest.json').read_text())['selected'] is None


def test_changed_dqsat_is_not_reused(tmp_path):
    paths=fixture(tmp_path);out=tmp_path/'out'
    args=(*paths,ROOT/'config/swp/soil_classification_and_profile.csv',ROOT/'config/swp/four_landuse_crop_candidate.csv',out,'1970-01-01','2022-12-31',1)
    result=generate(*args);result['status']='SWP_INPUTS_GENERATED_NOT_SWAP_VALIDATED'
    (out/'production_manifest.json').write_text(json.dumps(result))
    (tmp_path/'grensvlak_NHIWQ_v2_fill.asc').write_text(DQ_GRID.replace('\n13\n','\n14\n'))
    with pytest.raises(ValueError,match='not found'):
        generate(*args)
