"""Explicit owner decision 3143f4d, applied to physical HRU systems before merging."""
from dataclasses import asdict,replace
from math import isfinite

POLICY_ID='LWKM_C2_OWNER_3143f4d_V1'
LIMIT=100000.


def apply_owner_policy(systems):
    retained=[];events=[]
    for s in systems:
        if len(s.source_ids)!=1:raise ValueError('owner policy requires uncompressed physical systems')
        if not s.active:continue
        if not isfinite(s.drnres) or s.drnres<=0 or not isfinite(s.infres) or s.infres<=0:
            raise ValueError('invalid physical resistance')
        if not isfinite(s.drainage_conductance) or s.drainage_conductance<=0:
            raise ValueError('invalid drainage conductance')
        original=asdict(s)
        if s.drnres>LIMIT:
            events.append(dict(action='OMIT_DRAINAGE_SYSTEM',original=original,
                removed_drainage_g=s.drainage_conductance,removed_infiltration_g=s.infiltration_conductance))
            continue
        if s.allow_infiltration and s.infres>LIMIT:
            # Positive unused placeholder prevents a divide-by-zero in SWAP before
            # it enforces SWALLO=3. This is not a finite infiltration approximation.
            events.append(dict(action='DISABLE_INFILTRATION',original=original,
                removed_drainage_g=0.,removed_infiltration_g=s.infiltration_conductance))
            s=replace(s,hydraulic_class='drain_only_open',infres=LIMIT,
                      infiltration_conductance_raw=0.)
        retained.append(s)
    return retained,dict(policy_id=POLICY_ID,events=events,
        drainage_g_before=sum(s.drainage_conductance for s in systems if s.active),
        drainage_g_after=sum(s.drainage_conductance for s in retained),
        infiltration_g_before=sum(s.infiltration_conductance for s in systems if s.active),
        infiltration_g_after=sum(s.infiltration_conductance for s in retained))
