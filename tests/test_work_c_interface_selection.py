import pytest
from tools.dra_level_compression import PhysicalDrainageSystem,to_render_level
from tools.dra_protected_compression import select_protected_candidate


def system(name,g):
    return PhysicalDrainageSystem((name,),'infiltration_capable_open','open_channel',
        1/g,1/g,2.,1.,1.,dd=10.,drainage_conductance_raw=g,
        infiltration_conductance_raw=g,physical_active=True)


def test_interface_aware_search_can_merge_even_below_five_levels():
    x=[system('S',.001),system('T',.000004)]
    old,_=select_protected_candidate(x)
    with pytest.raises(ValueError):to_render_level(old[-1])
    levels,audit=select_protected_candidate(x,require_swap_interface=True)
    assert len(levels)==1 and set(levels[0].source_ids)=={'S','T'}
    assert levels[0].drainage_conductance==pytest.approx(.001004)
    assert audit['max_error_m']==0
    to_render_level(levels[0])


def test_protected_h1_is_never_sacrificed_to_fit_interface():
    with pytest.raises(ValueError,match='range overflow'):
        select_protected_candidate([system('S',.001),system('H1',.000004)],require_swap_interface=True)
