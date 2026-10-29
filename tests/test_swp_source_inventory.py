import json
from pathlib import Path
import zipfile
from tools.server.swp_source_inventory import inventory,read_references,discover_controls


def test_reuses_original_alias_resolver_and_records_units(tmp_path):
    source=tmp_path/'ahn_f250_cm.asc';source.write_text('payload must not be read')
    control=tmp_path/'control_run_1970_1979.ini'
    control.write_text(f'%model% = {tmp_path}\nmaaiveld_asc = %(%model%)s/ahn_f250_cm.asc\n')
    r=read_references(control,'CURRENT_SERVER_RUN_CONFIG')[0]
    assert r['role']=='ground_surface'
    assert r['locations'][0]['status']=='FILE_EXISTS'
    assert r['units_hint']=='cm_from_filename_UNVERIFIED'
    assert r['line']==2
    assert source.read_text()=='payload must not be read'


def test_relative_and_unresolved_are_not_admitted(tmp_path):
    p=tmp_path/'control_run_1970_1979.ini'
    (tmp_path/'soil.asc').write_text('x')
    p.write_text('bodem_asc=soil.asc\nrootzone_asc=%(%missing%)s/rootzone.asc\n')
    a,b=read_references(p,'test')
    assert a['status']=='RELATIVE_REFERENCE_REQUIRES_RUN_CONTEXT'
    assert a['locations'][0]['status']=='FILE_EXISTS'
    assert b['status']=='UNRESOLVED_ALIAS'


def test_bounded_discovery_keeps_overlap_alternatives(tmp_path):
    runs=tmp_path/'runs';runs.mkdir()
    controls=[]
    for name in ['run_2010_2019','run_2010_2021_MS_daily']:
        d=runs/name/'nhi_py';d.mkdir(parents=True)
        c=d/'control_run_2010_2019.ini';c.write_text('x=1');controls.append(c)
    deep=runs/'LWKM_run_resultaten_totaal'/'modflow';deep.mkdir(parents=True)
    (deep/'control_run_2000_2009.ini').write_text('x=1')
    found,_,_=discover_controls(runs,tmp_path/'missing')
    assert set(found)==set(controls)


def test_current_and_prior_and_small_report_zip(tmp_path):
    runs=tmp_path/'runs';current=runs/'run_1970_1979'/'nhi_py';current.mkdir(parents=True)
    prior=tmp_path/'prior';prior.mkdir()
    for directory,value in [(current,'current.asc'),(prior,'old.asc')]:
        (directory/'control_run_1970_1979.ini').write_text(f'rootzone_asc={value}\n')
    report,archive=inventory(runs,tmp_path/'model',prior,tmp_path/'report')
    assert len(report['controls'])==2
    assert len(report['key_comparison']['rootzone_asc']['configured_values'])==2
    assert report['status']=='SOURCE_LOCATION_INVENTORY_NOT_PRODUCTION_BINDING'
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())=={'source_inventory.json','source_references.csv','LEESMIJ.txt'}
        assert len(json.loads(z.read('source_inventory.json'))['references'])==2
