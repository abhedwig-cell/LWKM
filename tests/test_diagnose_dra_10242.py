import struct
from pathlib import Path

import numpy as np
import pandas as pd

from tools.diagnose_dra_10242 import (
    _build_h1_level_matrix,
    _month_key,
    _read_dqsat,
    _read_membership,
)


def _write_idf(path: Path, value: float, nodata: float = -9999.0) -> None:
    header=struct.pack(
        "<3i10f",
        1271, 1, 1,
        0.0, 250.0, 0.0, 250.0,
        value, value, nodata, 0.0, 250.0, 250.0,
    )
    path.write_bytes(header + struct.pack("<f", float(value)))


def test_membership_named_columns(tmp_path: Path):
    p=tmp_path/"membership.csv"
    pd.DataFrame({
        "SVAT":[1,2],
        "HRU":[10,11],
        "NRU":[20,21],
        "NRUcode":["a","b"],
        "svat_donor":[1,2],
        "ignored":[9,9],
    }).to_csv(p,index=False)
    df=_read_membership(p)
    assert list(df.columns)==["svat","hru","nru","nrucode","svatdonor"]
    assert df["hru"].tolist()==[10,11]


def test_representative_dqsat_autodetect(tmp_path: Path):
    p=tmp_path/"dqsat.csv"
    pd.DataFrame({
        "HRU":[1,2],
        "representative_dqsat":[10.0,20.0],
    }).to_csv(p,index=False)
    assert _read_dqsat(p)=={1:10.0,2:20.0}


def test_h1_month_key():
    assert _month_key(Path("peilh_20010201.idf"))=="2001-02-01"


def test_h1_months_are_stream_aggregated_per_hru(tmp_path: Path):
    p1=tmp_path/"peilh_20000101.idf"
    p2=tmp_path/"peilh_20000201.idf"
    _write_idf(p1,8.0)
    _write_idf(p2,7.0)

    members=pd.DataFrame({
        "hru":[1],
        "row":[0],
        "col":[0],
        "glk":[10.0],
        "H1_cdr":[2.0],
    })
    dates,matrix,failures=_build_h1_level_matrix(members,[p1,p2])
    assert dates==["2000-01-01","2000-02-01"]
    np.testing.assert_allclose(matrix[1],[2.0,3.0])
    assert failures=={}


def test_h1_missing_stage_is_bound_to_affected_hru(tmp_path: Path):
    p=tmp_path/"peilh_20000101.idf"
    _write_idf(p,-9999.0)
    members=pd.DataFrame({
        "hru":[7],
        "row":[0],
        "col":[0],
        "glk":[10.0],
        "H1_cdr":[2.0],
    })
    _,_,failures=_build_h1_level_matrix(members,[p])
    assert 7 in failures
