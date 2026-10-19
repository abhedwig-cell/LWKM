import pandas as pd
import pytest
from tools.groundwater_l1_boundary import aggregate, lateral_from_faces


def example():
    membership = pd.DataFrame({"hru_id": [4, 4], "cell_id": [1, 7], "area_m2": [62500., 62500.]})
    cells = pd.DataFrame({"date": ["2020-07-01"] * 2, "cell_id": [1, 7],
                          "flf": [100., -30.], "lat": [-12., 17.],
                          "ghb": [0., 5.], "wel": [-10., 0.]})
    return cells, membership


def test_group_volume_support_and_components():
    c, m = example()
    r = aggregate(c, m, start="2020-07-01", end="2020-07-01").iloc[0]
    assert r.q_ext_m3_d == 70
    assert r.q_ext_mm_d == pytest.approx(.56)
    assert r.flf_in_m3_d == 100 and r.flf_out_m3_d == 30
    assert r.wel_mm_d == pytest.approx(-.08)


def test_internal_faces_cancel_even_for_noncontiguous_ids():
    f = pd.DataFrame({"face_id": ["a", "b"], "from_cell": [1, 7], "to_cell": [7, 9], "volume_m3": [120., 13.]})
    r = lateral_from_faces(f, [1, 7])
    assert r.sum() == -13
    with pytest.raises(ValueError, match="duplicate face"):
        lateral_from_faces(pd.concat([f, f]), [1, 7])


@pytest.mark.parametrize("kind", ["duplicate", "missing", "nan", "fractional", "overlap"])
def test_fail_closed(kind):
    c, m = example()
    if kind == "duplicate": c = pd.concat([c, c.iloc[:1]])
    if kind == "missing": c = c.iloc[:1]
    if kind == "nan": c.loc[0, "wel"] = float("nan")
    if kind == "fractional": m.loc[0, "area_m2"] = 1000.
    if kind == "overlap": m = pd.concat([m, m.iloc[:1]])
    with pytest.raises(ValueError):
        aggregate(c, m, start="2020-07-01", end="2020-07-01")
