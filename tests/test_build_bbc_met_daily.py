import pandas as pd
import pytest
from tools.build_bbc_met_daily import build_bbc_daily,build_met_daily
from tools.p12_met_producer import DistrictDay

def test_bbc_complete_daily_qq():
    m=pd.DataFrame({"issvatwb":[True],"c1":[10.]},index=[1])
    h1={"2024-02-28":pd.Series({1:1.}),"2024-02-29":pd.Series({1:2.})}
    h2={"2024-02-28":pd.Series({1:2.}),"2024-02-29":pd.Series({1:3.})}
    result=build_bbc_daily(m,h1,h2,start="2024-02-28",end="2024-02-29")
    assert result.count("10.0000")==2
    assert "QBOT2" in result

def test_bbc_rejects_missing_day():
    m=pd.DataFrame({"issvatwb":[True],"c1":[10.]},index=[1])
    h={"2024-02-28":pd.Series({1:1.})}
    with pytest.raises(ValueError,match="expected"):
        build_bbc_daily(m,h,h,start="2024-02-28",end="2024-02-29")

def test_met_complete_daily_leap():
    d=DistrictDay(100,1,5,.8,2,2)
    records=[("2024-02-28",12,1.,1.,d,3.),("2024-02-29",12,0.,1.,d,3.)]
    text=build_met_daily(records,start="2024-02-28",end="2024-02-29")
    assert len(text.strip().splitlines())==2
    assert "'12'" in text

def test_met_rejects_duplicate_day():
    d=DistrictDay(100,1,5,.8,2,2)
    records=[("2024-02-28",12,1.,1.,d,3.),("2024-02-28",12,1.,1.,d,3.)]
    with pytest.raises(ValueError,match="missing, duplicate"):
        build_met_daily(records,start="2024-02-28",end="2024-02-29")
