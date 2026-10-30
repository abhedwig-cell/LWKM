import copy
import itertools
import pytest
from tools.swp_run_parameters import allocate_irrigation


def population(values):
    runs=[dict(run_id=i,area=a,irrigation_id=99) for i,a,b,c in values]
    diagnostics=[dict(HRU=i,irrigation_source_areas_m2={1:b,2:c}) for i,a,b,c in values]
    return runs,diagnostics


def test_closest_prefix_uses_area_fraction_and_preserves_source_policy():
    # Counts do not enter the allocation. Rank is 3,1,2; target 180.
    r,d=population([(1,100,30,20),(2,200,20,30),(3,100,40,40),(4,900,0,0)])
    report=allocate_irrigation(r,d)
    assert [x['irrigation_id'] for x in r]==[1,0,1,0]
    assert report['svat_irrigated_area_m2']==180
    assert report['hru_irrigated_area_m2']==200
    assert report['difference_m2']==20
    assert report['last_selected_hru']==1 and report['first_excluded_hru']==2
    assert [x['irrigation_allocation_rank'] for x in d]==[2,3,1,None]


def test_nearest_prefix_excludes_crossing_hru_when_it_increases_error():
    r,d=population([(1,100,90,0),(2,100,20,0)])
    report=allocate_irrigation(r,d)
    assert report['irrigated_hrus']==1
    assert report['difference_m2']==-10


def test_exact_deviation_tie_uses_lower_area_and_fraction_ties_use_hru_id():
    r,d=population([(9,100,25,0),(2,100,25,0),(3,100,25,0)])
    report=allocate_irrigation(r,d)
    assert report['last_selected_hru']==2
    r,d=population([(1,100,50,0)])
    assert allocate_irrigation(r,d)['irrigated_hrus']==0


def test_permutation_invariance_and_independent_prefix_minimum():
    vals=[(8,70,10,10),(2,50,0,45),(5,120,40,20)]
    for perm in itertools.permutations(vals):
        r,d=population(perm);report=allocate_irrigation(r,d)
        # Independently ordered fractions: 2(.9),5(.5),8(2/7).
        assert report['difference_m2']==min([0,50,170,240],key=lambda a:abs(a-125))-125
        assert {x['run_id'] for x in r if x['irrigation_id']}=={2,5}
        assert sum(x['area'] for x in r if x['irrigation_id'])==report['hru_irrigated_area_m2']


def test_zero_and_all_irrigation_and_serialized_diagnostic_keys():
    for b in (0,100):
        r,d=population([(1,100,b,0)])
        d[0]['irrigation_source_areas_m2']={'1':b,'2':0}
        a=allocate_irrigation(r,d)
        assert a['difference_m2']==0 and a['irrigated_hrus']==bool(b)
    assert allocate_irrigation([],[])['difference_percent']==0


def test_exact_decimal_area_accounting():
    r,d=population([(1,.3,.1,.2)])
    a=allocate_irrigation(r,d)
    assert a['difference_m2']==0 and r[0]['irrigation_id']==2


@pytest.mark.parametrize('values', [[(1,10,11,0)],[(1,0,0,0)],[(1,10,-1,0)]])
def test_invalid_support_rejected(values):
    with pytest.raises(ValueError):allocate_irrigation(*population(values))


def test_population_mismatch_rejected():
    r,d=population([(1,10,2,0)])
    with pytest.raises(ValueError):allocate_irrigation(r,[])
