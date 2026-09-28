import pandas as pd, pytest
from tools.run_state import CaseState,runnable
from tools.hydrology_contract import validate_hydrology,normalize_records

def test_run_state_retry():
    x=CaseState(1,"abc")
    x.transition("STAGED");x.transition("RUNNING");x.transition("FAILED",exit_code=1)
    assert runnable([x])==[1]
    x.transition("STAGED");x.transition("RUNNING");x.transition("SUCCEEDED",exit_code=0)
    assert x.attempt==2

def test_invalid_transition_rejected():
    x=CaseState(1,"a")
    with pytest.raises(ValueError):x.transition("SUCCEEDED")

def test_hydrology_contract():
    r=[{"case_id":1,"time":"2020-01-01","location_type":"bottom","location_id":"bottom",
        "variable":"bottom_flux","value":1.0,"unit":"cm/d","sign_convention":"positive_upward"}]
    d=normalize_records(r)
    assert validate_hydrology(d)["valid"]

def test_duplicate_hydrology_key_fails():
    r={"case_id":1,"time":"t","location_type":"surface","location_id":"s","variable":"runoff",
       "value":1,"unit":"cm/d","sign_convention":"positive_out"}
    assert not validate_hydrology(pd.DataFrame([r,r]))["valid"]
