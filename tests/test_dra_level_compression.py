from tools.dra_level_compression import (
    PhysicalDrainageSystem,
    compress_to_swap_levels,
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
