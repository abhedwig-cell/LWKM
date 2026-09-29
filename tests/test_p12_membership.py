import pytest
from tools.p12_membership import *

def test_historical_selects_non_donors():
    m=[Member(1,1),Member(2,1,"Toegevoegd")]
    assert historical_selection(m)==[False,True]
    assert corrected_selection(m)==[True,False]

def test_historical_fallback_all():
    m=[Member(1,1),Member(2,2)]
    assert historical_selection(m)==[True,True]
    assert corrected_selection(m)==[True,True]

def test_restgroup_uses_same_relation():
    m=[Member(1,1,"Restgroep"),Member(2,1,"Restgroep")]
    assert [provenance(x) for x in m]==["RESTGROUP_DONOR","RESTGROUP_TARGET"]
    assert corrected_selection(m)==[True,False]

def test_corrected_fails_without_donor():
    with pytest.raises(ValueError):
        corrected_selection([Member(2,1,"Toegevoegd")])
