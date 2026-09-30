import pytest
from tools.p12_dra_aggregate import *

def test_parallel_resistance():
    # two 62,500 m2 cells, C=625 each => R=100 d
    assert resistance([625,625])==pytest.approx(100)

def test_zero_resistance_caps():
    assert resistance([0,0])==100000

def test_infiltration_factor():
    # factor .5 doubles equivalent resistance
    assert infiltration_resistance([625,625],[.5,.5])==pytest.approx(200)

def test_conductance_weighted_depth():
    assert weighted_depth([1,3],[10,10],[9,7])==pytest.approx(2.5)
