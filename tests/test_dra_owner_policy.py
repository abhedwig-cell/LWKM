from dataclasses import replace
import pytest
import pandas as pd
from tools.dra_level_compression import PhysicalDrainageSystem,to_render_level
from tools.dra_owner_policy import apply_owner_policy
from tools.dra_protected_compression import select_protected_candidate
from tools.generate_dra import render_dra_explicit,aggregate_physical_system


def system(name='P',dr=100.,inf=100.):
    return PhysicalDrainageSystem((name,),'infiltration_capable_open','open_channel',dr,inf,1.,.5,.5,10.,
        drainage_conductance_raw=1/dr,infiltration_conductance_raw=1/inf,physical_active=True)


def test_strict_dra_threshold_drops_only_physical_source():
    kept,a=apply_owner_policy([system('P',100001),system('S',100000)])
    assert [x.source_ids for x in kept]==[('S',)]
    assert kept[0].drnres==100000 and a['events'][0]['original']['drnres']==100001
    assert to_render_level(kept[0])['drnres']==100000


def test_inf_threshold_disables_with_swallo3_not_a_capped_flux():
    kept,a=apply_owner_policy([system(inf=100001)])
    assert kept[0].drainage_conductance==.01 and kept[0].infiltration_conductance==0
    text=render_dra_explicit([to_render_level(kept[0])],1,1971,1972,0)
    assert 'SWALLO1 = 3' in text and a['events'][0]['original']['infres']==100001
    exact,_=apply_owner_policy([system(inf=100000)])
    assert exact[0].allow_infiltration


def test_disabled_source_cannot_be_merged_with_infiltrating_source():
    kept,_=apply_owner_policy([system('P',inf=100001),system('S')])
    with pytest.raises(ValueError,match='NO_ACCEPTABLE'):select_protected_candidate(kept,max_levels=1)


def test_invalid_resistance_is_not_omitted_as_negligible():
    with pytest.raises(ValueError,match='invalid physical'):apply_owner_policy([replace(system(),drnres=float('inf'))])


def test_policy_rejects_already_compressed_input():
    with pytest.raises(ValueError,match='uncompressed'):apply_owner_policy([replace(system(),source_ids=('P','S'))])


def test_all_omitted_is_explicit_empty_drainage():
    kept,_=apply_owner_policy([system(dr=100001)])
    levels,_=select_protected_candidate(kept,require_swap_interface=True)
    assert levels==[]


def test_h1_cell_zero_policy_preserves_other_cells_and_all_drainage():
    m=pd.DataFrame({'glk':[2.,2.],'cdr':[100.,100.],'bottom':[1.,1.], 'inf':[float('nan'),.5]})
    effective=m.copy();effective.loc[effective.inf.isna(),'inf']=0.
    a=aggregate_physical_system(effective,cdr_col='cdr',bottom_col='bottom',
        infiltration_factor_col='inf',summer_level_col=None,winter_level_col=None,representative_dqsat=2.)
    assert a['cdr_sum']==200. and a['infiltration_conductance_sum']==50.
    assert pd.isna(m.inf.iloc[0])
