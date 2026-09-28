from tools.lwkm_pipeline import status,STAGES

def test_pipeline_has_full_a_to_j_stage_order():
    s=status()
    assert [x["stage"] for x in s["stages"]]==STAGES
    assert STAGES[0]=="A_SVAT" and STAGES[-1]=="J_ANIMO"

def test_pipeline_does_not_overclaim_partial_stages():
    d={x["stage"]:x["implementation"] for x in status()["stages"]}
    assert d["A_SVAT"]=="EXECUTABLE"
    assert d["B_QUALIFICATION"]=="EXECUTABLE"
    assert d["C_HRU"]=="PARTIAL"
    assert d["J_ANIMO"]=="NOT_IMPLEMENTED"
