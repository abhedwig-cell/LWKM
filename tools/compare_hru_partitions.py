"""Label-invariant comparison of historical and candidate HRU partitions."""
from __future__ import annotations
import json
import pandas as pd

def canonical_partition(mapping:pd.DataFrame,svat="svat",hru="HRU")->dict[int,frozenset[int]]:
    g=mapping.groupby(hru,dropna=False)[svat].apply(lambda s:frozenset(map(int,s)))
    return {int(k):v for k,v in g.items()}

def partition_signatures(mapping:pd.DataFrame,svat="svat",hru="HRU")->set[frozenset[int]]:
    return set(canonical_partition(mapping,svat,hru).values())

def compare_partitions(reference:pd.DataFrame,candidate:pd.DataFrame,svat="svat",hru="HRU")->dict:
    r=partition_signatures(reference,svat,hru); c=partition_signatures(candidate,svat,hru)
    rs=set(map(int,reference[svat])); cs=set(map(int,candidate[svat]))
    return {
      "reference_hrus":len(r),"candidate_hrus":len(c),
      "reference_svats":len(rs),"candidate_svats":len(cs),
      "same_svat_universe":rs==cs,
      "exact_partition_equal":r==c,
      "shared_hru_member_sets":len(r&c),
      "reference_only_member_sets":len(r-c),
      "candidate_only_member_sets":len(c-r),
    }

def compare_routes(reference:pd.DataFrame,candidate:pd.DataFrame,svat="svat",route="aggr_no")->dict:
    a=reference[[svat,route]].rename(columns={route:"reference"}).merge(
      candidate[[svat,route]].rename(columns={route:"candidate"}),on=svat,how="outer",indicator=True)
    both=a["_merge"].eq("both")
    eq=both & a["reference"].eq(a["candidate"])
    return {"rows":len(a),"both":int(both.sum()),"same_route":int(eq.sum()),
            "route_mismatches":int((both&~a["reference"].eq(a["candidate"])).sum())}

def write_report(reference,candidate,path,svat="svat",hru="HRU",route="aggr_no"):
    report={"partition":compare_partitions(reference,candidate,svat,hru)}
    if route in reference.columns and route in candidate.columns:
        report["routes"]=compare_routes(reference,candidate,svat,route)
    path.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report
