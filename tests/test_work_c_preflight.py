from pathlib import Path
import pytest
from tools.package_preflight import validate
from tools.work_c_packages import project_bbc


def fixture(root):
    root.mkdir(exist_ok=True)
    (root/'swap.swp').write_text("""TSTART=1971-01-01
TEND=1971-01-03
METFIL='weather.met'
SWDRA=0
SWBBCFILE=0
SWETR=0
CROPSTART CROPEND CROPNAME CROPFIL CROPTYPE
1971-01-02 1971-01-03 'test' 'crop' 1
* End of table
""")
    (root/'crop.crp').write_text('SWCF=2\nSWCO2=0\n')
    (root/'weather.met').write_text('Station,DD,MM,YYYY,Rad,Tmin,Tmax,Hum,Wind,Rain,ETref,Wet\n'+
        ''.join(f"'1' {d} 1 1971 1000.0 1.0 3.0 0.8 2.0 1.0 0.1 0.5\n" for d in range(1,4)))
    return root


def test_fallow_is_explicit_bare_soil_not_missing_forcing(tmp_path):
    r=validate(fixture(tmp_path/'p'))
    assert r['fallow_days']==1 and r['status']=='PACKAGE_PREFLIGHT_PASS'
    assert r['files']==['crop.crp','swap.swp','weather.met']


def test_missing_weather_day_rejected(tmp_path):
    p=fixture(tmp_path/'p');f=p/'weather.met';lines=f.read_text().splitlines();f.write_text('\n'.join(lines[:2]+lines[3:])+'\n')
    with pytest.raises(ValueError,match='coverage'):validate(p)


def test_active_crop_reference_rejected_if_missing(tmp_path):
    p=fixture(tmp_path/'p');(p/'crop.crp').unlink()
    with pytest.raises(ValueError,match='missing asset'):validate(p)


def test_unsafe_crop_reference_rejected(tmp_path):
    p=fixture(tmp_path/'p');f=p/'swap.swp';f.write_text(f.read_text().replace("'crop'","'../crop'"))
    with pytest.raises(ValueError,match='unsafe'):validate(p)


def test_schema_etref_requires_sourced_crop_factors(tmp_path):
    p=fixture(tmp_path/'p');f=p/'swap.swp';f.write_text(f.read_text().replace('SWETR=0','SWETR=1'))
    with pytest.raises(ValueError,match='requires crop factors'):validate(p)


def test_co2_reference_is_transitive_and_year_bound(tmp_path):
    p=fixture(tmp_path/'p');(p/'crop.crp').write_text("SWCF=2\nSWCO2=1\nSWATMOFIL=1\nATMOFIL='air'\n")
    with pytest.raises(ValueError,match='missing asset'):validate(p)
    (p/'air.co2').write_text('1972 360.0\n')
    with pytest.raises(ValueError,match='year coverage'):validate(p)


def test_diagnostic_projection_preserves_source_period_without_extension():
    out,days,count=project_bbc('SWBOTB=2\nSW2=2\nDATE2 QBOT2\n31-dec-1970 0.1 0.2 0.3\n20-dec-1971 0.4 0.5 0.6\n* End of table\n')
    assert days[-1].isoformat()=='1971-12-20' and count==4
    assert '20-dec-1971 0.4\n' in out and '31-dec-1971' not in out


def test_external_restart_profile_is_not_silently_accepted(tmp_path):
    p=fixture(tmp_path/'p');f=p/'swap.swp';f.write_text(f.read_text()+"SWINCO=3\nINIFIL='missing'\n")
    with pytest.raises(ValueError,match='unsupported package profile'):validate(p)
