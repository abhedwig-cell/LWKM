import pandas as pd
import pytest
from tools.review_dra_protected_population import review

def test_all_candidates_present(tmp_path):
    p=tmp_path/"c.csv"
    pd.DataFrame([
      {"hru":11,"status":"NO_COMPRESSION","groups":"P","max_error_m":0,"compression_required":False},
      {"hru":99,"status":"CANDIDATE_NOT_ADMITTED","groups":"P+S","max_error_m":.01,"compression_required":True},
    ]).to_csv(p,index=False)
    x=review(p,expected_hrus=2)
    assert x["failed_hru_count"]==0
    assert x["production_admission"] is False

def test_fail_closed_on_unresolved(tmp_path):
    p=tmp_path/"c.csv"
    pd.DataFrame([
      {"hru":11,"status":"FAIL_CLOSED","groups":None,"max_error_m":None,"compression_required":True}
    ]).to_csv(p,index=False)
    x=review(p)
    assert x["failed_hru_ids"]==["11"]
    assert x["status"]=="PROTECTED_CANDIDATE_SCREEN_FAIL"

def test_duplicate_hru_rejected(tmp_path):
    p=tmp_path/"c.csv"
    pd.DataFrame([
      {"hru":11,"status":"NO_COMPRESSION","groups":"P","max_error_m":0,"compression_required":False},
      {"hru":11,"status":"NO_COMPRESSION","groups":"P","max_error_m":0,"compression_required":False},
    ]).to_csv(p,index=False)
    with pytest.raises(ValueError,match="duplicate HRU"):review(p)
