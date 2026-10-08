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

def test_triple_regional_merge_without_surface_merge():
    src=[sys("H1",1),sys("P",2),sys("S",2),sys("T",2),
         sys("MVG",.1),sys("PIPE",1),sys("OLF",.4)]
    levels,audit=select_protected_candidate(src)
    assert len(levels)==5
    assert any(set(s.source_ids)=={"P","S","T"} for s in levels)
    assert any(s.source_ids==("MVG",) for s in levels)
    assert any(s.source_ids==("OLF",) for s in levels)

def test_conductance_and_lineage_preserved():
    src=[sys("H1",1,g=2,gi=1),sys("P",2,g=3,gi=2),
         sys("S",2,g=4,gi=1),sys("T",2,g=5,gi=1),
         sys("MVG",.1,g=6),sys("PIPE",1,g=7),sys("OLF",.1,g=8)]
    levels,_=select_protected_candidate(src)
    assert abs(sum(x.drainage_conductance for x in src)-
               sum(x.drainage_conductance for x in levels))<1e-12
    assert abs(sum(x.infiltration_conductance for x in src)-
               sum(x.infiltration_conductance for x in levels))<1e-12
    assert sorted(x for s in src for x in s.source_ids)==sorted(
        x for s in levels for x in s.source_ids)

def test_invalid_level_limit_fails():
    with pytest.raises(ValueError,match="max_levels"):
        select_protected_candidate([sys("P",1)],max_levels=0)
