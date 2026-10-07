import struct
from pathlib import Path
import pandas as pd
import pytest

from tools.diagnose_dra_activity_10242 import _read_relation


def test_activity_relation_fails_closed_on_incomplete_population(tmp_path: Path):
    p=tmp_path/"relation.csv"
    pd.DataFrame({
        "svat_orig":[1,2],
        "HRU":[1,2],
        "x":[125.0,375.0],
        "y":[625.0,625.0],
    }).to_csv(p,index=False)
    with pytest.raises(ValueError,match="427656"):
        _read_relation(p)


def test_activity_system_contract_has_all_seven_named_sources():
    from tools.diagnose_dra_activity_10242 import MODERN_SEVEN
    assert MODERN_SEVEN == ("H1","P","S","T","MVG","PIPE","OLF")
