from dataclasses import replace
import pytest
from tools.p12_met_producer import DistrictDay,compose

@pytest.mark.parametrize("day,month,year",[(29,2,2023),(31,4,2024),(0,1,2024)])
def test_invalid_met_date(day,month,year):
    with pytest.raises(ValueError):
        compose(1,day,month,year,1,1,DistrictDay(100,0,5,.8,2,2),4)

@pytest.mark.parametrize("field,value",[
    ("rad",-1.),("hum",1.2),("wind",-1.),("wet",25.),
    ("tmin",float("nan")),
])
def test_met_rejects_invalid_district_data(field,value):
    d=replace(DistrictDay(100,0,5,.8,2,2),**{field:value})
    with pytest.raises(ValueError):
        compose(1,1,1,2024,1,1,d,4)

def test_met_rejects_reversed_temperature():
    with pytest.raises(ValueError,match="Tmin"):
        compose(1,1,1,2024,1,1,DistrictDay(100,10,5,.8,2,2),4)

def test_valid_leap_day():
    x=compose(1,29,2,2024,1,1,DistrictDay(100,0,5,.8,2,2),4)
    assert (x.day,x.month,x.year)==(29,2,2024)
