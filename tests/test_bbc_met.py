import pandas as pd
from tools.generate_bbc import aggregate_qbot2,render_bbc
from tools.generate_met import area_weighted_grid,wetness_adjust

def test_qbot2_uses_water_boundary_members_and_cm_conversion():
    m=pd.DataFrame({"issvatwb":[True,False],"c1":[10,1]},index=[0,1])
    h1=pd.Series([1,1]);h2=pd.Series([2,11])
    assert aggregate_qbot2(m,h1,h2)==10

def test_water_boundary_falls_back_to_all():
    m=pd.DataFrame({"issvatwb":[False,False],"c1":[10,10]},index=[0,1])
    h1=pd.Series([1,1]);h2=pd.Series([2,2])
    assert aggregate_qbot2(m,h1,h2)==10

def test_meteo_is_area_weighted_over_wb():
    m=pd.DataFrame({"issvatwb":[True,True,False],"area_m2":[1,3,100]},index=[0,1,2])
    v=pd.Series([0,4,100])
    assert area_weighted_grid(m,v)==3

def test_dry_day_zeroes_wetness():
    assert wetness_adjust(.001,2,1)==(0.0,0.0)

def test_bbc_contains_active_qbot2_only():
    s=render_bbc(["01-01-2000"],[1.25])
    assert "QBOT2" in s and "1.2500" in s
