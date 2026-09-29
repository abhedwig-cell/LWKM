"""Recover deterministic preprocessing lookup tables from realized SVAT products."""
from __future__ import annotations
import pandas as pd

FAMILIES={
 "landuse":{"source":"landgebruik22","derived":["lu7","lu4","lu2"]},
 "soil":{"source":"bodem370","derived":["bofek79","pawn21","grondsoort4","grondsoort2"]},
}

def extract_mapping(df:pd.DataFrame,source:str,derived:list[str])->pd.DataFrame:
    cols=[source]+derived
    x=df[cols].dropna().drop_duplicates()
    counts=x.groupby(source,dropna=False).size()
    ambiguous=counts[counts>1]
    if len(ambiguous):
        detail=x[x[source].isin(ambiguous.index)].sort_values(cols)
        raise ValueError(f"Non-deterministic mapping from {source}; ambiguous source classes: {ambiguous.index.tolist()}\n{detail.to_string(index=False)}")
    return x.sort_values(source).reset_index(drop=True)

def extract_family(df:pd.DataFrame,family:str)->pd.DataFrame:
    spec=FAMILIES[family]
    return extract_mapping(df,spec["source"],spec["derived"])

def validate_mapping(df:pd.DataFrame,mapping:pd.DataFrame,source:str,derived:list[str])->dict:
    x=df[[source]+derived].merge(mapping,on=source,how="left",suffixes=("_observed","_mapped"),validate="many_to_one")
    mismatches={}
    for c in derived:
        mismatches[c]=int(x[f"{c}_observed"].ne(x[f"{c}_mapped"]).sum())
    return {"rows":len(df),"source_classes":int(mapping[source].nunique()),"mismatches":mismatches,
            "exact":all(v==0 for v in mismatches.values())}
