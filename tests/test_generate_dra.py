import pandas as pd
from tools.generate_dra import (
    aggregate_system,
    aggregate_physical_system,
    repair_system,
    render_dra,
    repair_system_explicit,
    repair_system_explicit_legacy_v038,
    render_dra_explicit,
)
from tools.p12_swallo import REALIZED_PRODUCTION_COMPAT

def members():
    return pd.DataFrame({"glk":[10,10],"cdr1":[1,1],"inf1":[1,1],"leng1":[1,0],
                         "bodh1":[8,8],"peil_sum1":[9,9],"peil_win1":[8.5,8.5]})

def test_active_drainage_uses_all_members():
    s=aggregate_system(members(),1,25)
    assert s["dd"]==100
    assert s["drnres"]==62500
    assert s["infres"]==62500

def test_high_resistance_disables_system():
    s={"drnres":20001,"infres":1,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    x=repair_system(s,1,False)
    assert x["drnres"]==100000 and x["dep"]==0

def test_nature_disables_system_four():
    s={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    assert repair_system(s,4,True)["drnres"]==100000

def test_serializer_has_five_level_header_and_tube_system_four():
    s={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    text=render_dra([s]*5,3,2000,2000,20)
    assert "NRLEVS = 5" in text and "SWDTYP4 = 1" in text and "SWALLO4 = 3" in text


def test_serializer_can_target_realized_system_three_swallo():
    s={"drnres":10,"infres":725,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    text=render_dra([s]*5,3,2000,2000,11.820416666666667,swallo_mode=REALIZED_PRODUCTION_COMPAT)
    assert "SWALLO3 = 3" in text



def test_legacy_explicit_repair_disables_pipe_for_nature_independent_of_level_number():
    s={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    assert repair_system_explicit_legacy_v038(
        s, medium="drain_tube", isnatuur=True
    )["drnres"] == 100000
    assert repair_system_explicit_legacy_v038(
        s, medium="open_channel", isnatuur=True
    )["drnres"] == 10


def test_modern_explicit_repair_preserves_high_resistance_physical_level():
    s={"drnres":25000,"infres":50000,"dep":2,"peil_sum":1,"peil_win":1,"dd":10}
    assert repair_system_explicit(s,medium="open_channel",isnatuur=False) == s


def test_modern_explicit_repair_does_not_delete_pipe_only_for_nature_label():
    s={"drnres":1000,"infres":100000,"dep":1,"peil_sum":1,"peil_win":1,"dd":80}
    x=repair_system_explicit(s,medium="drain_tube",isnatuur=True)
    assert x["drnres"] == 1000
    assert x["dep"] == 1


def test_explicit_renderer_uses_medium_not_level_number_for_swdtyp():
    base={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10,
          "allow_infiltration":False,"source_ids":("x",)}
    levels=[
        {**base,"medium":"drain_tube"},
        {**base,"medium":"open_channel"},
    ]
    text=render_dra_explicit(levels,3,2000,2000,20)
    assert "NRLEVS = 2" in text
    assert "SWDTYP1 = 1" in text
    assert "SWDTYP2 = 2" in text


def test_explicit_renderer_uses_hydraulic_capability_not_level_number_for_swallo():
    base={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10,
          "medium":"open_channel","source_ids":("x",)}
    levels=[
        {**base,"allow_infiltration":True},
        {**base,"allow_infiltration":False},
        {**base,"allow_infiltration":True},
        {**base,"allow_infiltration":True},
    ]
    text=render_dra_explicit(levels,3,2000,2000,20)
    assert "SWALLO1 = 1" in text
    assert "SWALLO2 = 3" in text
    assert "SWALLO3 = 1" in text
    assert "SWALLO4 = 1" in text


def test_explicit_renderer_rejects_more_than_five_levels():
    base={"drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1,"dd":10,
          "medium":"open_channel","allow_infiltration":True,"source_ids":("x",)}
    try:
        render_dra_explicit([base]*6,3,2000,2000,20)
    except ValueError as exc:
        assert "1..5" in str(exc)
    else:
        raise AssertionError("expected six-level render to fail")



def test_named_physical_system_uses_all_members_and_representative_dqsat():
    df=pd.DataFrame({
        "glk":[10.0,10.0],
        "cdr_h1":[1.0,3.0],
        "inf_h1":[0.5,1.0],
        "bottom_h1":[8.0,9.0],
        "summer_h1":[9.0,9.5],
        "winter_h1":[8.5,9.0],
    })
    s=aggregate_physical_system(
        df,
        cdr_col="cdr_h1",
        bottom_col="bottom_h1",
        summer_level_col="summer_h1",
        winter_level_col="winter_h1",
        infiltration_factor_col="inf_h1",
        representative_dqsat=25.0,
    )
    assert s["drnres"] == 31250.0
    assert s["dd"] == 100.0
    assert s["member_count"] == 2


def test_named_drain_only_system_has_inactive_infiltration_resistance():
    df=pd.DataFrame({
        "glk":[10.0],
        "cdr_mvg":[100.0],
        "bottom_mvg":[9.0],
        "summer_mvg":[9.0],
        "winter_mvg":[9.0],
    })
    s=aggregate_physical_system(
        df,
        cdr_col="cdr_mvg",
        bottom_col="bottom_mvg",
        summer_level_col="summer_mvg",
        winter_level_col="winter_mvg",
        representative_dqsat=20.0,
    )
    assert s["infres"] == 100000.0
    assert s["dd"] == 80.0


def test_named_physical_system_fails_closed_on_missing_active_hydraulics():
    df=pd.DataFrame({
        "glk":[10.0],
        "cdr_h1":[100.0],
        "inf_h1":[float("nan")],
        "bottom_h1":[9.0],
        "summer_h1":[9.0],
        "winter_h1":[9.0],
    })
    try:
        aggregate_physical_system(
            df,
            cdr_col="cdr_h1",
            bottom_col="bottom_h1",
            summer_level_col="summer_h1",
            winter_level_col="winter_h1",
            infiltration_factor_col="inf_h1",
            representative_dqsat=20.0,
        )
    except ValueError as exc:
        assert "missing infiltration factor" in str(exc)
    else:
        raise AssertionError("expected missing active H1 infiltration factor to fail closed")



def test_explicit_renderer_writes_dynamic_monthly_level_series():
    level={
        "drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1.5,"dd":80,
        "medium":"open_channel","allow_infiltration":True,"source_ids":("H1",),
        "level_series":(
            ("2000-01-01",1.8),
            ("2000-02-01",1.7),
            ("2000-03-01",1.6),
        ),
    }
    text=render_dra_explicit([level],3,2000,2000,20)
    assert "01-jan-2000  -180.00" in text
    assert "01-feb-2000  -170.00" in text
    assert "01-mar-2000  -160.00" in text
    assert "01-apr-2000" not in text



def test_dynamic_renderer_uses_fixed_english_month_tokens():
    level={
        "drnres":10,"infres":10,"dep":2,"peil_sum":1,"peil_win":1.5,"dd":80,
        "medium":"open_channel","allow_infiltration":True,"source_ids":("H1",),
        "level_series":(
            ("2000-05-01",1.2),
            ("2000-10-01",1.4),
        ),
    }
    text=render_dra_explicit([level],3,2000,2000,20)
    assert "01-may-2000" in text
    assert "01-oct-2000" in text



def test_named_dynamic_physical_system_can_aggregate_without_seasonal_columns():
    df=pd.DataFrame({
        "glk":[10.0,10.0],
        "cdr_h1":[1.0,3.0],
        "inf_h1":[0.5,1.0],
        "bottom_h1":[8.0,9.0],
    })
    s=aggregate_physical_system(
        df,
        cdr_col="cdr_h1",
        bottom_col="bottom_h1",
        summer_level_col=None,
        winter_level_col=None,
        infiltration_factor_col="inf_h1",
        representative_dqsat=25.0,
    )
    assert s["cdr_sum"] == 4.0
    assert s["peil_sum"] == 0.0
    assert s["peil_win"] == 0.0
    assert s["support_area_m2"] == 125000.0



def test_explicit_renderer_rejects_drares_above_swap_parser_range():
    level={
        "drnres":100001.0,"infres":100000.0,"dep":1.0,
        "peil_sum":0.5,"peil_win":0.5,"dd":80.0,
        "medium":"open_channel","allow_infiltration":False,
        "source_ids":("weak",),
    }
    try:
        render_dra_explicit([level],3,2000,2000,20)
    except ValueError as exc:
        assert "DRARES outside SWAP method-3 range" in str(exc)
    else:
        raise AssertionError("expected DRARES range overflow to fail")


def test_explicit_renderer_rejects_infres_above_swap_parser_range():
    level={
        "drnres":1000.0,"infres":100001.0,"dep":1.0,
        "peil_sum":0.5,"peil_win":0.5,"dd":80.0,
        "medium":"open_channel","allow_infiltration":True,
        "source_ids":("weak",),
    }
    try:
        render_dra_explicit([level],3,2000,2000,20)
    except ValueError as exc:
        assert "INFRES outside SWAP method-3 range" in str(exc)
    else:
        raise AssertionError("expected INFRES range overflow to fail")
