import pandas as pd
from tools.compare_hru_partitions import compare_partitions, compare_routes

def test_partition_comparison_ignores_hru_labels():
    a=pd.DataFrame({"svat":[1,2,3,4],"HRU":[10,10,20,20]})
    b=pd.DataFrame({"svat":[1,2,3,4],"HRU":[99,99,7,7]})
    assert compare_partitions(a,b)["exact_partition_equal"]

def test_partition_detects_different_membership():
    a=pd.DataFrame({"svat":[1,2,3,4],"HRU":[1,1,2,2]})
    b=pd.DataFrame({"svat":[1,2,3,4],"HRU":[1,2,2,2]})
    assert not compare_partitions(a,b)["exact_partition_equal"]

def test_route_comparison_by_svat():
    a=pd.DataFrame({"svat":[1,2],"aggr_no":[1,2]})
    b=pd.DataFrame({"svat":[2,1],"aggr_no":[2,1]})
    assert compare_routes(a,b)["route_mismatches"]==0
