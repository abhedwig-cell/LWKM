import numpy as np, pytest
from tools.p12_meteo_weights import build_weights,aggregate_grid

def test_pixel_collapse_and_area_weights():
    rows=[
      {"HRU":"1","svat_orig":"1","svat_donor":"1","x":"100","y":"624900","uopp_m2":"1"},
      {"HRU":"1","svat_orig":"2","svat_donor":"2","x":"200","y":"624800","uopp_m2":"3"},
      {"HRU":"1","svat_orig":"3","svat_donor":"1","x":"1100","y":"624900","uopp_m2":"9"},
    ]
    w=build_weights(rows,"donor_equal")
    assert len(w)==1 and w[0]["weight"]==pytest.approx(1)
    g=np.zeros((325,300)); g[0,0]=7
    assert aggregate_grid(w,g)[1]==pytest.approx(7)

def test_source_current_selects_target():
    rows=[
      {"HRU":"1","svat_orig":"1","svat_donor":"1","x":"100","y":"624900","uopp_m2":"1"},
      {"HRU":"1","svat_orig":"2","svat_donor":"1","x":"1100","y":"624900","uopp_m2":"1"},
    ]
    w=build_weights(rows,"source_current")
    assert [(x["row"],x["col"]) for x in w]==[(0,1)]
