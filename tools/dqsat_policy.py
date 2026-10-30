"""Owner decision 2026-10-09, shared by SWP and DRA (stdlib only)."""
import math
from statistics import median

METHOD = 'POSITIVE_MEMBER_MEDIAN_CANDIDATE'


def summarize(values, representative, nodata=None):
    """Equal-member median; exclude exact NoData and zero, reject other invalids.

    Preserve the raw representative sample, including a NoData sentinel. NoData
    is matched exactly: a nearby finite value is not silently discarded.
    """
    samples = [float(v) for v in values]
    positive = []
    zeros = missing = 0
    for value in samples:
        if not math.isfinite(value):
            raise ValueError('nonfinite member dqsat')
        if nodata is not None and value == nodata:
            missing += 1
        elif value < 0:
            raise ValueError('negative member dqsat')
        elif value == 0:
            zeros += 1
        else:
            positive.append(value)
    if not positive:
        raise ValueError('HRU has no positive dqsat members')
    representative = float(representative)
    if not math.isfinite(representative):
        raise ValueError('nonfinite representative dqsat')
    representative_missing = nodata is not None and representative == nodata
    if representative < 0 and not representative_missing:
        raise ValueError('negative representative dqsat')
    selected = float(median(positive))
    return dict(source_representative_dqsat=representative,
                representative_is_nodata=representative_missing,
                positive_median=selected, positive_mean=math.fsum(positive)/len(positive),
                member_count=len(samples), positive_count=len(positive),
                zero_count=zeros, nodata_count=missing,
                candidate_spacing_m=4*selected, dqsat_method=METHOD,
                discriminating=representative_missing or representative != selected)
