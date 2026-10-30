from pathlib import Path
import pytest
from tools.swp_direct_render import Catalog
from tools.swp_local_assets import local_assets, CO2_NAME, CROPS, ROOT
from tests.test_swp_run_parameters import ParameterTests


@pytest.mark.parametrize('crop_id', sorted(CROPS))
@pytest.mark.parametrize('irrigation', [0, 1, 2])
def test_four_templates_schedule_local_co2_and_preserved_rotation(crop_id, irrigation):
    fixture=ParameterTests();fixture.setUp();run,_=fixture.derive()
    run.update(crop_id=crop_id, irrigation_id=irrigation)
    context=Catalog(ROOT/'config/swp/lookup_catalog.json.gz').context(run)
    original=[dict(row) for row in context['TABLE_CROPROTATION']]
    assets=local_assets(run, context)
    assert context['TABLE_CROPROTATION']==original
    assert assets[CO2_NAME]==(ROOT/'templates/atmosphere'/CO2_NAME).read_bytes()
    for name,data in assets.items():
        if name.endswith('.crp'):
            text=data.decode()
            assert '{{' not in text
            assert f'SCHEDULE = {int(irrigation != 0)}' in text
            assert f"ATMOFIL = '{Path(CO2_NAME).stem}'" in text


def test_missing_co2_year_fails():
    fixture=ParameterTests();fixture.setUp();run,_=fixture.derive()
    run['TEND']='2026-12-31'
    with pytest.raises(ValueError, match='missing CO2 year 2026'):
        local_assets(run, {'TABLE_CROPROTATION': []})
