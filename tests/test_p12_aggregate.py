import pytest
from tools.p12_aggregate import qbot2_cm_day,area_weighted

def test_qbot2_units_and_selection():
    # dh=[1,2] m, c=[100,100] d => [1,2] cm/d
    assert qbot2_cm_day([0,0],[1,2],[100,100],[True,False])==pytest.approx(1.0)
    assert qbot2_cm_day([0,0],[1,2],[100,100],[True,True])==pytest.approx(1.5)

def test_surface_area_weight():
    assert area_weighted([1,3],[1,3],[True,True])==pytest.approx(2.5)

def test_empty_fails():
    with pytest.raises(ValueError): qbot2_cm_day([0],[1],[100],[False])
