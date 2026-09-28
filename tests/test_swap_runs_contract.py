import pytest
from tools.swap_runs_contract import RUN_COLUMNS,build_runs_row,validate_runs_row

def test_strict_runs_builder_refuses_unresolved_fields():
    with pytest.raises(ValueError):
        build_runs_row({"HRU":1,"SWBOTB":2,"SWBBCFILE":1},{})

def test_full_runs_row_contract():
    base={c:1 for c in RUN_COLUMNS}
    base.update({"HRU":1,"SWBOTB":7,"SWBBCFILE":0,"PONDMX":5.0})
    providers={c:(lambda m,v=1:v) for c in RUN_COLUMNS}
    row=build_runs_row(base,providers)
    validate_runs_row(row)
    assert list(row)==RUN_COLUMNS and row["scenario_id"]=="direct"
