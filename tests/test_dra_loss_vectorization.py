from dataclasses import replace
from tools.dra_level_compression import PhysicalDrainageSystem
from tools.w07_autofive_full_records import loss,level,stages,flux,effective
import pytest


def test_full_axis_objective_matches_existing_scalar_breakpoint_definition():
    a=PhysicalDrainageSystem(('H1',),'infiltration_capable_open','open_channel',100.,200.,2.,1.,1.,40.,
        (('1971-01-01',.5),('1971-07-01',1.),('1972-01-01',.7)))
    b=PhysicalDrainageSystem(('P',),'infiltration_capable_open','open_channel',80.,120.,2.,.8,.6,40.)
    source=[a,b];represented=[effective(source)]
    objective=md=mi=mn=0.
    for day in stages(source):
        heads={-1.,0.,1.,2.,3.,4.,5.}|{level(s,day) for s in source}|{level(s,day) for s in represented}
        for h in sorted(heads):
            d0=sum(flux(s,h,level(s,day))[0] for s in source)
            i0=sum(flux(s,h,level(s,day))[1] for s in source)
            d1=sum(flux(s,h,level(s,day))[0] for s in represented)
            i1=sum(flux(s,h,level(s,day))[1] for s in represented)
            ed=1000*(d1-d0);ei=1000*(i1-i0)
            objective+=ed*ed+ei*ei
            md=max(md,abs(ed));mi=max(mi,abs(ei));mn=max(mn,abs(ed-ei))
    result=loss(source,represented)
    assert result['objective']==pytest.approx(objective,abs=1e-12)
    assert result['max_drain_error_mm_d']==md
    assert result['max_infil_error_mm_d']==mi
    assert result['max_net_error_mm_d']==mn
    assert result['stage_count']==3
    assert 'NOT_SIMULATED' in result['integration_scope']
