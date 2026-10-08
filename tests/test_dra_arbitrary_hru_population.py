import pandas as pd
import pytest
from tools.diagnose_dra_10242 import _read_static04_snapshot

def test_snapshot_accepts_new_hru_partition(tmp_path):
    p=tmp_path/"new_partition.csv"
    pd.DataFrame({"hru":[901,42],"representative_dqsat":[12.,23.]}).to_csv(p,index=False)
    actual=_read_static04_snapshot(p)
    assert actual.hru.tolist()==[42,901]
    assert actual.representative_dqsat.tolist()==[23.,12.]

def test_snapshot_rejects_duplicate_hru(tmp_path):
    p=tmp_path/"bad.csv"
    pd.DataFrame({"hru":[5,5],"representative_dqsat":[10.,11.]}).to_csv(p,index=False)
    with pytest.raises(ValueError,match="duplicate HRU"):
        _read_static04_snapshot(p)
