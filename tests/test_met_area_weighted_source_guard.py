import pandas as pd
import pytest
from tools.generate_met import area_weighted_grid

def test_met_area_weighted_positive_support():
    m=pd.DataFrame({"issvatwb":[True,True,False],"area_m2":[1,3,100]},index=[1,2,3])
    v=pd.Series({1:2.,2:6.,3:99.})
    assert area_weighted_grid(m,v)==pytest.approx(5.)

def test_met_negative_source_clipped_after_finite_validation():
    m=pd.DataFrame({"issvatwb":[True,True],"area_m2":[1,1]},index=[1,2])
    assert area_weighted_grid(m,pd.Series({1:-1.,2:4.}))==pytest.approx(2.)

@pytest.mark.parametrize("areas",[[0.,1.],[-1.,1.],[float("nan"),1.]])
def test_met_rejects_bad_area(areas):
    m=pd.DataFrame({"issvatwb":[True,True],"area_m2":areas},index=[1,2])
    with pytest.raises(ValueError,match="areas"):
        area_weighted_grid(m,pd.Series({1:1.,2:2.}))

def test_met_rejects_missing_member_value():
    m=pd.DataFrame({"issvatwb":[True,True],"area_m2":[1,1]},index=[1,2])
    with pytest.raises(ValueError,match="index"):
        area_weighted_grid(m,pd.Series({1:1.}))

def test_met_rejects_nonfinite_value():
    m=pd.DataFrame({"issvatwb":[True],"area_m2":[1.]},index=[1])
    with pytest.raises(ValueError,match="finite"):
        area_weighted_grid(m,pd.Series({1:float("nan")}))
