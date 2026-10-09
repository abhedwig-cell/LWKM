import pytest
from tools.validate_daily_series import validate_daily_series

def test_leap_year():
    x=validate_daily_series(['2024-02-28','2024-02-29','2024-03-01'],[1,2,3],start='2024-02-28',end='2024-03-01',label='MET')
    assert len(x)==3

@pytest.mark.parametrize('dates,values',[
    (['2024-02-28','2024-03-01'],[1,2]),
    (['2024-02-28','2024-02-28','2024-03-01'],[1,2,3]),
    (['2024-03-01','2024-02-29','2024-02-28'],[1,2,3]),
    (['2024-02-28','2024-02-29','2024-03-01'],[1,float('nan'),3]),
])
def test_rejects_incomplete(dates,values):
    with pytest.raises(ValueError):
        validate_daily_series(dates,values,start='2024-02-28',end='2024-03-01',label='BBC')

def test_reversed_window():
    with pytest.raises(ValueError,match='reversed'):
        validate_daily_series([],[],start='2024-03-01',end='2024-02-28',label='MET')
