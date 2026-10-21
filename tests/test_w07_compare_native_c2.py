from pathlib import Path
from tools.w07_compare_native_c2 import compare


def _dra(value=100):
    return ("DRAMET = 3\nNRLEVS = 1\n"
            f"DRARES1 = {value}\nINFRES1 = 100000\nSWALLO1 = 3\n"
            "L1 = 40\nZBOTDR1 = -50\nSWDTYP1 = 2\n"
            "DATOWL1 LEVEL1\n01-jan-1971 -20.0\n")


def test_native_c2_parity_explicit(tmp_path):
    native=tmp_path/'native';c2=tmp_path/'c2'
    native.mkdir();c2.mkdir()
    (native/'1.dra').write_text(_dra())
    (c2/'1.dra').write_text(_dra())
    (native/'2.dra').write_text(_dra(110))
    (c2/'2.dra').write_text(_dra(100))
    (native/'3.dra').write_text(_dra())
    r=compare(native,c2,tmp_path/'report.json',expected=3)
    assert r['counts']['BYTE_IDENTICAL']==1
    assert r['counts']['HYDRAULIC_PARAMETER_DIFFERENCE']==1
    assert r['counts']['NEW_CANDIDATE_NO_C2_BASELINE']==1


def test_native_c2_rejects_invalid(tmp_path):
    native=tmp_path/'native';c2=tmp_path/'c2'
    native.mkdir();c2.mkdir()
    (native/'1.dra').write_text('NRLEVS = 2\nDRARES1=100\n')
    r=compare(native,c2,tmp_path/'report.json',expected=1)
    assert r['counts']['INVALID_DRA']==1

def test_stage_series_changes_are_not_accepted_as_parity(tmp_path):
    native=tmp_path/'native';c2=tmp_path/'c2'
    native.mkdir();c2.mkdir()
    a=_dra()+"01-apr-1971 -40.0\n"
    b=_dra()+"01-apr-1971 -30.0\n"
    (native/'1.dra').write_text(a)
    (c2/'1.dra').write_text(b)
    r=compare(native,c2,tmp_path/'stage-report.json',expected=1)
    assert r['counts']['STAGE_SERIES_DIFFERENCE']==1
