import pandas as pd
from tools.qualification_adapter import compare_flags,FLAGS

def test_flag_regression_reports_union_mismatch():
    d=pd.DataFrame({f:[0,0] for f in FLAGS})
    got=pd.DataFrame({f:[0,0] for f in FLAGS})
    got.loc[1,"runoff_sel"]=1
    q=compare_flags(d,got).set_index("flag")
    assert q.loc["runoff_sel","false_positive"]==1
    assert q.loc["ANY","derived_positive"]==1
    assert not q.loc["ANY","exact"]
