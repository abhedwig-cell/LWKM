"""Conservative dependency invalidation for staged HRU construction.

Cluster membership can change throughout an LDGBclus and the later rest/donor
procedure spans every cluster district sharing an LDGB. We compute the entire
connected dependency component, rather than pretending changes are row-local.
"""
from __future__ import annotations
import hashlib
import json
import pandas as pd


def row_fingerprints(frame, key="svat"):
    if frame[key].duplicated().any() or frame[key].isna().any():
        raise ValueError("non-unique or missing identity")
    cols=sorted(c for c in frame if c!=key)
    def digest(row):
        data={c:None if pd.isna(row[c]) else row[c] for c in cols}
        return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),default=str,allow_nan=False).encode()).hexdigest()
    return dict(zip(frame[key].astype(int), (digest(r) for r in frame[cols].to_dict('records'))))


def impacted(before, after, membership, *, algorithm_changed=False, global_lookup_changed=False):
    for frame in [before,after]:
        if frame[['LDGB','LDGBclus']].isna().any().any():
            raise ValueError("unresolved district dependency")
    a,b=row_fingerprints(before),row_fingerprints(after)
    changed={i for i in a.keys()|b.keys() if a.get(i)!=b.get(i)}
    universe=set(a)|set(b)
    if algorithm_changed or global_lookup_changed:
        selected=universe
    else:
        links=pd.concat([before[['svat','LDGB','LDGBclus']],after[['svat','LDGB','LDGBclus']]]).drop_duplicates()
        selected=set(changed)
        while True:
            rows=links[links.svat.isin(selected)]
            expanded=set(links.loc[links.LDGB.isin(rows.LDGB)|links.LDGBclus.isin(rows.LDGBclus),'svat'].astype(int))
            if expanded<=selected:break
            selected|=expanded
    hrus=sorted(set(membership.loc[membership.svat.isin(selected),'HRU'].astype(int)))
    return dict(changed_svats=sorted(changed),recompute_svats=sorted(selected),
                affected_existing_hrus=hrus,reusable_existing_hrus=sorted(set(membership.HRU.astype(int))-set(hrus)),
                requires_global_hru_id_reconciliation=bool(selected),
                reason="GLOBAL_CODE_OR_LOOKUP" if algorithm_changed or global_lookup_changed else "DISTRICT_DEPENDENCY_CLOSURE",
                production_admitted=False)


def reconcile_component(reference,candidate):
    """Stable release IDs for a dependency-closed candidate component.

    Identical member sets retain their IDs. New sets get monotonically new
    IDs in sorted-member order; deleted IDs are never silently recycled.
    Releasing a changed population remains a separate admission decision.
    """
    for frame in [reference,candidate]:
        if frame.svat.duplicated().any() or frame.svat.isna().any():raise ValueError('Invalid membership identity')
    ids=set(candidate.svat)
    if not ids<=set(reference.svat):raise ValueError('New SVATs need an explicit population release')
    selected=reference[reference.svat.isin(ids)]
    affected=set(selected.HRU)
    if set(reference.loc[reference.HRU.isin(affected),'svat'])!=ids:
        raise ValueError('Component cuts through an existing HRU')
    old={tuple(sorted(g.svat.astype(int))):int(h) for h,g in selected.groupby('HRU')}
    new={int(h):tuple(sorted(g.svat.astype(int))) for h,g in candidate.groupby('HRU')}
    mapping={};next_id=int(reference.HRU.max())+1
    for h,members in sorted(new.items(),key=lambda item:item[1]):
        if members in old:mapping[h]=old[members]
        else:mapping[h]=next_id;next_id+=1
    fixed=candidate.copy();fixed['HRU']=fixed.HRU.map(mapping)
    if 'LDGB_orig' in fixed and 'NRU' in reference:
        nrus=reference[['HRU','LDGB_orig','NRU']].drop_duplicates()
        if nrus.duplicated(['HRU','LDGB_orig']).any():raise ValueError('Ambiguous original NRU')
        lookup={(int(r.HRU),int(r.LDGB_orig)):int(r.NRU) for r in nrus.itertuples()}
        next_nru=int(nrus.NRU.max())+1
        for pair in sorted(set(zip(fixed.HRU.astype(int),fixed.LDGB_orig.astype(int)))):
            if pair not in lookup:lookup[pair]=next_nru;next_nru+=1
        fixed['NRU']=[lookup[(int(h),int(l))] for h,l in zip(fixed.HRU,fixed.LDGB_orig)]
        fixed['NRUcode']=[f'{int(h)}_{int(l)}' for h,l in zip(fixed.HRU,fixed.LDGB_orig)]
    combined=pd.concat([reference[~reference.svat.isin(ids)],fixed],ignore_index=True).sort_values('svat')
    if combined.svat.duplicated().any() or set(combined.svat)!=set(reference.svat):raise ValueError('Reconciliation changed the universe')
    return combined,dict(local_to_release_hru=mapping,new_hru_ids=sorted(set(mapping.values())-set(affected)),
        retired_hru_ids=sorted(affected-set(mapping.values())),untouched_hrus=len(set(reference.HRU)-affected),production_admitted=False)
