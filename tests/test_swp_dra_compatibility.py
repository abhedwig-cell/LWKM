from pathlib import Path
import pytest
from tools.check_swp_dra_compatibility import check_pair
from tools.swp_direct_render import Catalog
from tools.modern_swp import render
from tests.test_swp_run_parameters import ParameterTests

ROOT=Path(__file__).resolve().parents[1]


def test_written_swp_and_dra_horizons_must_match(tmp_path):
    fixture=ParameterTests();fixture.setUp();run,_=fixture.derive()
    context=Catalog(ROOT/'config/swp/lookup_catalog.json.gz').context(run)
    swp=tmp_path/'1.swp';swp.write_text(render((ROOT/'tests/fixtures/d1/wwl.swp').read_bytes(),context))
    n=len(context['TABLE_SOILHYDRFUNC']);dra=tmp_path/'1.dra'
    dra.write_text('COFANI = '+' '.join(['1.0']*n)+'\n')
    assert check_pair(swp,dra)==n
    dra.write_text('COFANI = '+' '.join(['1.0']*43)+'\n')
    assert n!=43
    with pytest.raises(ValueError,match='COFANI count'):check_pair(swp,dra)
