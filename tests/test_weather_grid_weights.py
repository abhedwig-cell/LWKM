import zipfile
import pandas as pd
import pytest
from tools.work_a_weather_grids import run


def test_uopp_area_weighting_and_whole_hru_missing_guard(tmp_path):
    def archive(name,values):
        p=tmp_path/(name+'.zip')
        with zipfile.ZipFile(p,'w') as z:z.writestr(name+'_20180101.asc','ncols 2\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n'+values+'\n')
        return p
    rain=archive('rain','2 4');et=archive('et','1 3')
    m=tmp_path/'members.csv';pd.DataFrame(dict(svat_orig=[1,2],HRU=[7,7],x=[125,375],y=[125,125])).to_csv(m,index=False)
    a=tmp_path/'areas.csv';pd.DataFrame({'svat':[1,2],'opp(m2)':[1.,3.]}).to_csv(a,index=False)
    r=run(rain,et,m,a,tmp_path/'out','2018-01-01');f=pd.read_csv(tmp_path/'out/hru-rain-etref.csv')
    assert f.rain_source_value.iloc[0]==pytest.approx(3.5) and f.etref_source_value.iloc[0]==pytest.approx(2.5)
    assert r['production_admitted'] is False
    bad=archive('rain_missing','2 -9999');r=run(bad,et,m,a,tmp_path/'bad','2018-01-01')
    assert r['complete_rain_etref_hrus']==0
