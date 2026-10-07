from tools.dra_level_compression import (
    PhysicalDrainageSystem,
    compress_to_swap_levels,
    drainage_infiltration_level_gap,
    from_aggregate,
    to_render_level,
    max_source_level_separation,
)


def system(name, cls, medium, r, dep, ps, pw, inf=100000.0):
    return PhysicalDrainageSystem(
        source_ids=(name,),
        hydraulic_class=cls,
        medium=medium,
        drnres=r,
        infres=inf,
        dep=dep,
        peil_sum=ps,
        peil_win=pw,
    )


def seven():
    return [
        system("H1", "infiltration_capable_open", "open_channel", 200, 2.2, 1.4, 1.8, 400),
        system("P", "infiltration_capable_open", "open_channel", 300, 2.0, 1.3, 1.7, 600),
        system("S", "infiltration_capable_open", "open_channel", 500, 1.5, 1.0, 1.2, 1000),
        system("T", "infiltration_capable_open", "open_channel", 800, 1.4, 0.95, 1.15, 1600),
        system("MVG", "drain_only_open", "open_channel", 1500, 0.5, 0.5, 0.5),
        system("PIPE", "pipe", "drain_tube", 1000, 1.0, 1.0, 1.0),
        system("OLF", "drain_only_open", "open_channel", 1200, 0.2, 0.2, 0.2),
    ]


def test_seven_physical_systems_compress_to_five_without_loss_of_lineage():
    out = compress_to_swap_levels(seven())
    assert len(out) == 5
    sources = sorted(x for s in out for x in s.source_ids)
    assert sources == ["H1", "MVG", "OLF", "P", "PIPE", "S", "T"]


def test_pipe_remains_distinct():
    out = compress_to_swap_levels(seven())
    pipe = [s for s in out if "PIPE" in s.source_ids]
    assert len(pipe) == 1
    assert pipe[0].source_ids == ("PIPE",)
    assert pipe[0].medium == "drain_tube"


def test_parallel_conductance_is_conserved_exactly_enough():
    inp = seven()
    out = compress_to_swap_levels(inp)
    gin = sum(s.drainage_conductance for s in inp)
    gout = sum(s.drainage_conductance for s in out)
    iin = sum(s.infiltration_conductance for s in inp)
    iout = sum(s.infiltration_conductance for s in out)
    assert abs(gin - gout) < 1e-12
    assert abs(iin - iout) < 1e-12


def test_closest_hydraulic_pair_is_merged_within_class():
    out = compress_to_swap_levels(seven())
    merged = [set(s.source_ids) for s in out if len(s.source_ids) > 1]
    # S/T are deliberately closest in hydraulic levels among infiltration-capable
    # systems in this fixture.
    assert {"S", "T"} in merged


def test_drain_only_and_infiltration_capable_open_systems_do_not_cross_merge():
    out = compress_to_swap_levels(seven())
    for s in out:
        ids = set(s.source_ids)
        assert not (ids & {"H1", "P", "S", "T"} and ids & {"MVG", "OLF"})


def test_five_or_fewer_active_systems_are_not_compressed():
    inp = seven()[:5]
    out = compress_to_swap_levels(inp)
    assert len(out) == 5
    assert sorted(x for s in out for x in s.source_ids) == sorted(x for s in inp for x in s.source_ids)


def test_inactive_physical_system_does_not_consume_swap_level():
    inp = seven()
    inp[0] = system("H1", "infiltration_capable_open", "open_channel", 100000, 2.2, 1.4, 1.8)
    out = compress_to_swap_levels(inp)
    assert len(out) <= 5
    assert "H1" not in {x for s in out for x in s.source_ids}



def test_modern_spacing_is_preserved_through_merge():
    a=PhysicalDrainageSystem(("A",),"infiltration_capable_open","open_channel",100,200,2,1,1.5,80)
    b=PhysicalDrainageSystem(("B",),"infiltration_capable_open","open_channel",200,400,1.8,1.1,1.4,80)
    out=compress_to_swap_levels([a,b],max_levels=1)
    assert out[0].dd == 80


def test_different_modern_spacing_fails_instead_of_averaging():
    a=PhysicalDrainageSystem(("A",),"infiltration_capable_open","open_channel",100,200,2,1,1.5,80)
    b=PhysicalDrainageSystem(("B",),"infiltration_capable_open","open_channel",200,400,1.8,1.1,1.4,60)
    try:
        compress_to_swap_levels([a,b],max_levels=1)
    except ValueError as exc:
        assert "incompatible drainage spacing" in str(exc)
    else:
        raise AssertionError("expected differing modern L values to fail closed")


def test_aggregate_bridge_preserves_metadata_for_renderer():
    agg={"drnres":100.0,"infres":200.0,"dep":2.0,"peil_sum":1.0,"peil_win":1.5,"dd":80.0}
    p=from_aggregate(
        source_id="H1",
        hydraulic_class="infiltration_capable_open",
        medium="open_channel",
        aggregate=agg,
    )
    r=to_render_level(p)
    assert r["source_ids"] == ("H1",)
    assert r["allow_infiltration"] is True
    assert r["medium"] == "open_channel"
    assert r["dd"] == 80.0



def test_dynamic_h1_profile_is_merged_pointwise_with_seasonal_channel():
    h1=PhysicalDrainageSystem(
        ("H1",),"infiltration_capable_open","open_channel",
        100,200,2.0,1.0,1.5,80,
        (("2000-01-01",1.8),("2000-04-01",1.2),("2000-10-01",1.6)),
    )
    p=PhysicalDrainageSystem(
        ("P",),"infiltration_capable_open","open_channel",
        100,200,2.0,1.0,1.5,80,
    )
    out=compress_to_swap_levels([h1,p],max_levels=1)[0]
    assert out.level_series is not None
    vals=dict(out.level_series)
    assert abs(vals["2000-01-01"] - (1.8+1.5)/2) < 1e-12
    assert abs(vals["2000-04-01"] - (1.2+1.0)/2) < 1e-12
    assert abs(vals["2000-10-01"] - (1.6+1.5)/2) < 1e-12


def test_dynamic_profiles_with_different_dates_fail_closed():
    a=PhysicalDrainageSystem(
        ("A",),"infiltration_capable_open","open_channel",
        100,200,2,1,1,80,(("2000-01-01",1.0),),
    )
    b=PhysicalDrainageSystem(
        ("B",),"infiltration_capable_open","open_channel",
        100,200,2,1,1,80,(("2000-02-01",1.0),),
    )
    try:
        compress_to_swap_levels([a,b],max_levels=1)
    except ValueError as exc:
        assert "date mismatch" in str(exc)
    else:
        raise AssertionError("expected dynamic date mismatch to fail closed")



def test_positive_physical_conductance_survives_swap_resistance_sentinel_before_repair():
    agg={
        "drnres":100000.0,
        "infres":100000.0,
        "dep":1.0,
        "peil_sum":0.5,
        "peil_win":0.5,
        "dd":80.0,
        "cdr_sum":0.1,
        "infiltration_conductance_sum":0.0,
        "member_count":1,
        "support_area_m2":62500.0,
    }
    p=from_aggregate(
        source_id="weak",
        hydraulic_class="drain_only_open",
        medium="open_channel",
        aggregate=agg,
    )
    assert p.active is True
    assert p.drainage_conductance > 0.0


def test_drain_only_infiltration_conductance_is_zero_even_with_resistance_sentinel():
    p=PhysicalDrainageSystem(
        ("OLF",),"drain_only_open","open_channel",
        1000.0,100000.0,0.2,0.2,0.2,80.0,
    )
    assert p.infiltration_conductance == 0.0



def test_legacy_resistance_sentinel_without_raw_metadata_remains_inactive():
    p=PhysicalDrainageSystem(
        ("legacy",),
        "drain_only_open",
        "open_channel",
        100000.0,
        100000.0,
        1.0,
        0.5,
        0.5,
    )
    assert p.drainage_conductance == 0.0
    assert p.active is False


def test_merged_physical_resistance_is_uncapped_and_raw_conductance_is_preserved():
    a=PhysicalDrainageSystem(
        ("A",),
        "drain_only_open",
        "open_channel",
        100000.0,
        100000.0,
        1.0,
        0.5,
        0.5,
        80.0,
        drainage_conductance_raw=1e-7,
        infiltration_conductance_raw=0.0,
        physical_active=True,
    )
    b=PhysicalDrainageSystem(
        ("B",),
        "drain_only_open",
        "open_channel",
        100000.0,
        100000.0,
        1.0,
        0.5,
        0.5,
        80.0,
        drainage_conductance_raw=1e-7,
        infiltration_conductance_raw=0.0,
        physical_active=True,
    )
    out=compress_to_swap_levels([a,b],max_levels=1)[0]
    assert out.drnres == 5000000.0
    assert abs(out.drainage_conductance - 2e-7) < 1e-20
    assert out.active is True
    try:
        to_render_level(out)
    except ValueError as exc:
        assert "DRARES range overflow" in str(exc)
    else:
        raise AssertionError("expected uncapped merged resistance to fail SWAP interface gate")



def test_equal_cost_merge_tie_break_is_independent_of_input_order():
    systems=[
        PhysicalDrainageSystem(
            (name,),
            "drain_only_open",
            "open_channel",
            1000.0,
            100000.0,
            1.0,
            0.5,
            0.5,
            80.0,
        )
        for name in ("A","B","C","D","E","F")
    ]
    expected=None
    for ordered in (
        systems,
        list(reversed(systems)),
        [systems[i] for i in (2,5,1,4,0,3)],
    ):
        out=compress_to_swap_levels(ordered,max_levels=5)
        groups=sorted(tuple(x.source_ids) for x in out)
        if expected is None:
            expected=groups
        assert groups==expected
    assert ("A","B") in expected



def test_drainage_infiltration_level_gap_is_zero_for_equal_conductance_ratios():
    a=PhysicalDrainageSystem(
        ("A",),"infiltration_capable_open","open_channel",
        100.0,200.0,2.0,1.0,1.5,80.0,
    )
    b=PhysicalDrainageSystem(
        ("B",),"infiltration_capable_open","open_channel",
        200.0,400.0,1.8,0.8,1.3,80.0,
    )
    assert drainage_infiltration_level_gap(a,b) < 1e-15


def test_drainage_infiltration_level_gap_detects_one_level_representation_tension():
    a=PhysicalDrainageSystem(
        ("A",),"infiltration_capable_open","open_channel",
        100.0,100.0,2.0,1.0,1.5,80.0,
    )
    b=PhysicalDrainageSystem(
        ("B",),"infiltration_capable_open","open_channel",
        100.0,1000.0,1.8,0.0,0.5,80.0,
    )
    gap=drainage_infiltration_level_gap(a,b)
    assert gap > 0.0
    out=compress_to_swap_levels([a,b],max_levels=1)[0]
    assert abs(
        out.merge_history[-1]["max_drainage_infiltration_level_gap_m"] - gap
    ) < 1e-15



def test_source_level_span_detects_irreducible_activation_breakpoint_loss():
    a=PhysicalDrainageSystem(
        ("A",),"infiltration_capable_open","open_channel",
        100.0,200.0,2.0,1.0,1.5,80.0,
    )
    b=PhysicalDrainageSystem(
        ("B",),"infiltration_capable_open","open_channel",
        200.0,400.0,2.0,1.4,1.7,80.0,
    )
    assert abs(max_source_level_separation(a,b) - 0.4) < 1e-12
    merged=compress_to_swap_levels([a,b],max_levels=1)[0]
    event=merged.merge_history[-1]
    assert abs(event["max_source_level_separation_m"] - 0.4) < 1e-12
    assert event["bottom_depth_separation_m"] == 0.0


def test_equal_conductance_ratio_can_have_zero_centroid_gap_but_nonzero_level_span():
    from tools.dra_level_compression import drainage_infiltration_level_gap
    a=PhysicalDrainageSystem(
        ("A",),"infiltration_capable_open","open_channel",
        100.0,200.0,2.0,1.0,1.0,80.0,
    )
    b=PhysicalDrainageSystem(
        ("B",),"infiltration_capable_open","open_channel",
        200.0,400.0,2.0,2.0,2.0,80.0,
    )
    assert drainage_infiltration_level_gap(a,b) == 0.0
    assert max_source_level_separation(a,b) == 1.0



def test_uncapped_physical_resistance_exposes_swap_range_overflow():
    agg={
        "drnres":100000.0,
        "infres":100000.0,
        "dep":1.0,
        "peil_sum":0.5,
        "peil_win":0.5,
        "dd":80.0,
        "cdr_sum":0.01,
        "infiltration_conductance_sum":0.005,
        "member_count":1,
        "support_area_m2":62500.0,
    }
    p=from_aggregate(
        source_id="weak",
        hydraulic_class="infiltration_capable_open",
        medium="open_channel",
        aggregate=agg,
    )
    assert p.active is True
    assert p.drnres == 6250000.0
    assert p.infres == 12500000.0
    try:
        to_render_level(p)
    except ValueError as exc:
        assert "DRARES range overflow" in str(exc)
    else:
        raise AssertionError("expected physical DRARES >1e5 to fail SWAP interface gate")



def test_infiltration_capable_class_with_zero_physical_infiltration_is_rendered_drain_only():
    agg={
        "drnres":1000.0,
        "infres":100000.0,
        "dep":1.0,
        "peil_sum":0.5,
        "peil_win":0.5,
        "dd":80.0,
        "cdr_sum":62.5,
        "infiltration_conductance_sum":0.0,
        "member_count":1,
        "support_area_m2":62500.0,
    }
    p=from_aggregate(
        source_id="RIV_ZERO_INF",
        hydraulic_class="infiltration_capable_open",
        medium="open_channel",
        aggregate=agg,
    )
    assert p.active is True
    assert p.infiltration_conductance == 0.0
    assert p.allow_infiltration is False
    assert to_render_level(p)["allow_infiltration"] is False


def test_merge_enables_infiltration_only_when_merged_raw_conductance_is_positive():
    zero=PhysicalDrainageSystem(
        ("A",),"infiltration_capable_open","open_channel",
        1000.0,100000.0,1.0,0.5,0.5,80.0,
        drainage_conductance_raw=1e-3,
        infiltration_conductance_raw=0.0,
        physical_active=True,
    )
    positive=PhysicalDrainageSystem(
        ("B",),"infiltration_capable_open","open_channel",
        1000.0,2000.0,1.0,0.5,0.5,80.0,
        drainage_conductance_raw=1e-3,
        infiltration_conductance_raw=5e-4,
        physical_active=True,
    )
    assert zero.allow_infiltration is False
    merged=compress_to_swap_levels([zero,positive],max_levels=1)[0]
    assert merged.infiltration_conductance == 5e-4
    assert merged.allow_infiltration is True
