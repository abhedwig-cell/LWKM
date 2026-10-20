"""Serialize the already selected C2 hydraulic levels for a requested period.

No regrouping, resistance changes, or new compression. C2 generated monthly
representative cycles may repeat only after validating a complete closed cycle.
"""
from copy import deepcopy
from datetime import date
from tools.generate_dra import render_dra_explicit

def render_period(checkpoint,n_horizons,start,end):
    if checkpoint['status']!='DRA_INTERFACE_CANDIDATE':raise ValueError('C2_PROTECTED_DRAINAGE_EXCEPTION')
    levels=deepcopy(checkpoint['levels'])
    first,last=date.fromisoformat(start),date.fromisoformat(end)
    for level in levels:
        series=level.get('level_series')
        if not series:continue
        nodes=[(date.fromisoformat(d),float(v)) for d,v in series]
        # The selected C2 monthly representation is a closed annual parameter
        # cycle, not an observed historical management time series.
        expected=[date(nodes[0][0].year,m,1) for m in range(1,13)]+[date(nodes[0][0].year+1,1,1)]
        if [d for d,v in nodes]!=expected or abs(nodes[-1][1]-nodes[0][1])>1e-12:
            raise ValueError('UNQUALIFIED_NONREPEATING_DRA_SERIES')
        monthly={d.month:v for d,v in nodes[:-1]}
        level['level_series']=[[date(y,m,1).isoformat(),monthly[m]] for y in range(first.year,last.year+2) for m in range(1,13)]
    return render_dra_explicit(levels,n_horizons,first.year,last.year+1,0.)
