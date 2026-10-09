import pandas as pd
import pytest
from tools.generate_bbc import aggregate_qbot2,render_bbc

def test_qq_uses_selected_water_boundary_members_and_cm_per_day():
    members=pd.DataFrame({"issvatwb":[True,False,True],"c1":[10.,1.,20.]},index=[11,12,13])
    h1=pd.Series({11:1.,12:0.,13:2.})
    h2=pd.Series({11:2.,12:100.,13:1.})
    assert aggregate_qbot2(members,h1,h2)==pytest.approx(2.5)

def test_qq_falls_back_to_all_members_without_water_boundary():
    members=pd.DataFrame({"issvatwb":[False,False],"c1":[10.,20.]},index=[1,2])
    assert aggregate_qbot2(members,pd.Series({1:1.,2:1.}),pd.Series({1:2.,2:3.}))==pytest.approx(10.)

@pytest.mark.parametrize("c1",[0.,-1.,float("nan")])
def test_qq_rejects_invalid_c1(c1):
    m=pd.DataFrame({"issvatwb":[True],"c1":[c1]},index=[1])
    with pytest.raises(ValueError):
        aggregate_qbot2(m,pd.Series({1:1.}),pd.Series({1:2.}))

def test_qq_rejects_missing_head():
    m=pd.DataFrame({"issvatwb":[True],"c1":[1.]},index=[1])
    with pytest.raises(ValueError,match="missing"):
        aggregate_qbot2(m,pd.Series(dtype=float),pd.Series({1:2.}))

def test_qq_renders_one_column_not_three():
    text=render_bbc(["2020-01-01"],[2.5])
    assert "QBOT2" in text
    assert "2.5000" in text
    assert "FLF" not in text
    assert "QLAT" not in text

def test_qq_rejects_mismatched_dates():
    with pytest.raises(ValueError,match="equally sized"):
        render_bbc(["2020-01-01"],[])
