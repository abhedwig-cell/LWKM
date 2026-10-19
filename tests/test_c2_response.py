import pytest
from tools.work_c2_assess import response
from tools.dra_level_compression import PhysicalDrainageSystem


def test_high_resistance_does_not_imply_negligible_flux_at_large_head_difference():
    s=PhysicalDrainageSystem(('P',),'infiltration_capable_open','open_channel',102289.83716032676,309969.19119907264,
        28.14800128173829,27.698000518798835,27.698000518798835,10.,
        drainage_conductance_raw=9.776142261646412e-6,infiltration_conductance_raw=3.2261270745380833e-6,physical_active=True)
    assert response([s],0.,'1971-01-01','drainage')*1000==pytest.approx(.2707795934349319)
