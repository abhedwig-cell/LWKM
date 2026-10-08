from tools.dra_level_compression import PhysicalDrainageSystem
from tools.dra_protected_compression import select_protected_candidate
import pytest

def sys(name,level,g=1.,gi=0.):
    cls="pipe" if name=="PIPE" else ("drain_only_open" if name in ("MVG","OLF") else "infiltration_capable_open")
    medium="drain_tube" if name=="PIPE" else "open_channel"
    return PhysicalDrainageSystem(source_ids=(name,),hydraulic_class=cls,medium=medium,
        drnres=1/g,infres=100000 if gi==0 else 1/gi,dep=level,
        peil_sum=level,peil_win=level,dd=40.,
        drainage_conductance_raw=g,infiltration_conductance_raw=gi,physical_active=True)

def test_no_compression():
    levels,audit=select_protected_candidate([sys("H1",1),sys("PIPE",2)])
    assert audit["status"]=="NO_COMPRESSION"
    assert len(levels)==2

def test_protected_h1_pipe_and_two_compatible_merges():
    src=[sys("H1",1),sys("P",1),sys("S",2),sys("T",2),
         sys("MVG",.1),sys("PIPE",1),sys("OLF",.1)]
    levels,audit=select_protected_candidate(src)
    assert len(levels)==5
    assert any(s.source_ids==("H1",) for s in levels)
    assert any(s.source_ids==("PIPE",) for s in levels)
    assert any(set(s.source_ids)=={"S","T"} for s in levels)
    assert any(set(s.source_ids)=={"MVG","OLF"} for s in levels)

def test_rejects_incompatible_regional_merges():
    src=[sys("H1",1),sys("P",1),sys("S",4),sys("T",7),
         sys("MVG",.1),sys("PIPE",1),sys("OLF",.1)]
    with pytest.raises(ValueError,match="NO_ACCEPTABLE"):
        select_protected_candidate(src,regional_error_limit_m=.01)
