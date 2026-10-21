from tools.run_dra_protected_population import physical
from tools.w07_autofive_full_records import solve

def _make(name, cls, medium, level):
    return physical(dict(source_id=name,hydraulic_class=cls,medium=medium,
        drainage_conductance=.001,infiltration_conductance=.0001 if cls=="infiltration_capable_open" else 0.,
        dep=level+.1,peil_sum=level,peil_win=level+.02,dd=40.))

def test_seven_to_five_preserves_source_and_conductance():
    s=[_make("H1","infiltration_capable_open","open_channel",0.),
       _make("P","infiltration_capable_open","open_channel",1.),
       _make("S","infiltration_capable_open","open_channel",1.1),
       _make("T","infiltration_capable_open","open_channel",1.2),
       _make("MVG","drain_only_open","open_channel",.1),
       _make("OLF","drain_only_open","open_channel",.2),
       _make("PIPE","pipe","drain_tube",1.)]
    out,audit=solve(s)
    assert len(out)==5
    assert sorted(v for x in out for v in x.source_ids)==sorted(x.source_ids[0] for x in s)
    assert abs(sum(x.drainage_conductance for x in out)-sum(x.drainage_conductance for x in s))<1e-12
    assert len([x for x in out if x.medium=="drain_tube"])==1
    assert audit["method"] in ("PROTECTED","AUTO_APPROXIMATED_FIVE_LEVEL")
