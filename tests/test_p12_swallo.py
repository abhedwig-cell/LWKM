from tools.p12_swallo import swallo
def test_swallo_policy():
    assert swallo(1,100,11)==1
    assert swallo(1,100,9.9)==3
    assert swallo(1,20001,11)==3
    assert swallo(4,100,11)==3
