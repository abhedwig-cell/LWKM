"""Pure P12 aggregation kernels. Selection is supplied explicitly."""
from __future__ import annotations
from statistics import fmean

def qbot2_cm_day(head1_m,head2_m,c1_day,selected):
    q=[(h2-h1)/c for h1,h2,c,s in zip(head1_m,head2_m,c1_day,selected) if s]
    if not q: raise ValueError("empty QBOT2 selection")
    return 100.0*fmean(q)

def area_weighted(values,areas_m2,selected):
    pairs=[(v,a) for v,a,s in zip(values,areas_m2,selected) if s]
    if not pairs: raise ValueError("empty spatial selection")
    den=sum(a for _,a in pairs)
    if den<=0: raise ValueError("non-positive selected area")
    return sum(v*a for v,a in pairs)/den
