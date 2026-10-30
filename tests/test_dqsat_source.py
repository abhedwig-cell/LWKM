import json
import pytest
from tools.server.dqsat_source import locate, NAME
from tools.server.check_swp_source_values import sha


def test_discovers_existing_source_by_identity_without_relocation(tmp_path,monkeypatch):
    static=tmp_path/'model/Data/2_Model_Input/metaswap/grid'
    static.mkdir(parents=True)
    raster=static/NAME;raster.write_text('identified source')
    monkeypatch.setattr('tools.server.dqsat_source.DQSAT_SHA256',sha(raster))
    report=tmp_path/'report.json'
    found=locate({'glk':{'path':str(static/'ground.asc')}},tmp_path/'runs',report)
    assert found==raster
    assert json.loads(report.read_text())['selected']==str(raster)
    raster.write_text('different source')
    with pytest.raises(ValueError,match='not found'):
        locate({'glk':{'path':str(static/'ground.asc')}},tmp_path/'runs',report)
    assert json.loads(report.read_text())['candidates'][0]['status']=='DIFFERENT_SOURCE_REJECTED'
