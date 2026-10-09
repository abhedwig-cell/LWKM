"""Fail-closed, reusable temporal completeness validation for LWKM BBC/MET."""
from datetime import date, timedelta
from math import isfinite


def validate_daily_series(dates, values, *, start, end, label):
    """Return canonical date/value tuples for a complete inclusive daily period."""
    first = date.fromisoformat(str(start))
    last = date.fromisoformat(str(end))
    if first > last:
        raise ValueError(f'{label}: reversed time window')
    dates = list(dates)
    values = list(values)
    if len(dates) != len(values):
        raise ValueError(f'{label}: date/value count mismatch')
    expected = (last - first).days + 1
    if len(dates) != expected:
        raise ValueError(f'{label}: expected {expected} days, received {len(dates)}')
    out = []
    for i, (raw, value) in enumerate(zip(dates, values)):
        day = date.fromisoformat(str(raw))
        if day != first + timedelta(days=i):
            raise ValueError(f'{label}: missing, duplicate or unordered date at index {i}')
        value = float(value)
        if not isfinite(value):
            raise ValueError(f'{label}: non-finite value at {day}')
        out.append((day.isoformat(), value))
    return tuple(out)
