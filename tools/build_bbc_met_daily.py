"""W08/W09 complete daily source-to-text production candidates.

Strictly separate science (qq aggregation / MET composition) from time-series
validation and serialization. These candidates are not production-admitted.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
from tools.generate_bbc import aggregate_qbot2, render_bbc
from tools.p12_met_producer import compose, render_swap_met
from tools.validate_daily_series import validate_daily_series


def build_bbc_daily(members, head_l1_by_date, head_l2_by_date, *, start, end):
    keys=list(head_l1_by_date)
    if keys!=list(head_l2_by_date):
        raise ValueError("BBC head1/head2 dates differ or have different order")
    # Date completeness is checked before expensive spatial aggregation.
    validate_daily_series(keys,[0.]*len(keys),start=start,end=end,label="BBC")
    values=[aggregate_qbot2(members,head_l1_by_date[k],head_l2_by_date[k])
            for k in keys]
    validate_daily_series(keys,values,start=start,end=end,label="BBC QBOT2")
    return render_bbc(keys,values)


def build_met_daily(records, *, start, end):
    """records: iterable of (ISO date, station, rain, etref, DistrictDay, max_wet)."""
    rows=list(records)
    keys=[str(r[0]) for r in rows]
    validate_daily_series(keys,[0.]*len(keys),start=start,end=end,label="MET")
    out=[]
    for key,station,rain,etref,district,max_wet in rows:
        d=date.fromisoformat(str(key))
        out.append(render_swap_met(compose(station,d.day,d.month,d.year,
                                           rain,etref,district,max_wet)))
    return "\n".join(out)+"\n"
