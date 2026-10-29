from pathlib import Path
import pytest
from tools.svat_areas import read_area_svat,bind_area_files,locate_area_files


def write(path,svat=10,area=50,x=125,y=125):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(f'{svat} {area} 1 2 3 4 5 6 7 {x} {y} 8 9 10\n')
    return path


def members():return [dict(svat='10',HRU='1',x='125',y='125',svat_area_m2='40')]


def test_original_id_xy_and_actual_area_no_fallback(tmp_path):
    p=write(tmp_path/'area_svat.inp')
    assert read_area_svat(p,members())=={10:50}
    p=write(p,svat=11)
    with pytest.raises(ValueError,match='missing 1 original SVAT'):read_area_svat(p,members())
    p=write(p,x=375)
    with pytest.raises(ValueError,match='coordinate mismatch'):read_area_svat(p,members())


def test_duplicate_and_invalid_area_are_rejected(tmp_path):
    p=write(tmp_path/'area_svat.inp');p.write_text(p.read_text()*2)
    with pytest.raises(ValueError,match='duplicate'):read_area_svat(p,members())
    write(p,area=0)
    with pytest.raises(ValueError,match='invalid area'):read_area_svat(p,members())


def test_period_discovery_excludes_appendage_and_daily_overlap(tmp_path):
    p=write(tmp_path/'run_1970_1979/metaswap/area_svat.inp')
    write(tmp_path/'run_2010_2021_MS_daily/metaswap/area_svat.inp',area=600)
    write(tmp_path/'svat_border/area_svat.inp',area=999)
    paths,r=locate_area_files(tmp_path,'1970-01-01','1979-12-31')
    assert paths==[p] and not r['missing_periods']


def test_period_differences_are_recorded_and_equal_selected_areas_allowed(tmp_path):
    a=write(tmp_path/'a.inp');b=write(tmp_path/'b.inp',area=55)
    values,report=bind_area_files([a,b],members(),dict(scope='PERIOD_RUN_FILES'))
    assert values=={10:50}
    assert report['status']=='SELECTED_SVAT_AREAS_DIFFER_BETWEEN_FILES'
    assert report['period_area_differences'][0]['changed_selected_svats']==1
    write(b);b.write_text(b.read_text()+'20 90 1 2 3 4 5 6 7 375 125 8 9 10\n')
    _,report=bind_area_files([a,b],members(),dict(scope='PERIOD_RUN_FILES'))
    assert not report['period_area_differences']


def test_no_area_file_never_uses_membership(tmp_path):
    paths,r=locate_area_files(tmp_path,'1970-01-01','2022-12-31')
    with pytest.raises(FileNotFoundError,match='no area fallback'):bind_area_files(paths,members(),r)
