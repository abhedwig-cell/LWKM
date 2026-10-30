"""Generic per-HRU positive-median dqsat source preparation.

Produces a table for the existing raster diagnostic without assuming a fixed
HRU count. The representative-SVAT value is preserved as comparison evidence.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from tools.compare_dqsat_authority import read_ascii_grid,sample_centres
from tools.dqsat_policy import summarize


def prepare(schema,relation,grid):
    required={"HRU","svat_orig","x","y"}
    if not required.issubset(relation) or not {"HRU","svat_repr"}.issubset(schema):
        raise ValueError("schema/relation missing member sampling columns")
    mem=relation[["HRU","svat_orig","x","y"]].copy()
    sch=schema[["HRU","svat_repr"]].copy()
    for frame, columns in ((mem,("HRU","svat_orig")),(sch,("HRU","svat_repr"))):
        for col in columns:
            numbers=pd.to_numeric(frame[col],errors="raise")
            if (~np.isfinite(numbers)).any() or (numbers%1!=0).any():
                raise ValueError("noninteger HRU/SVAT identity")
            frame[col]=numbers.astype("int64")
    if mem.svat_orig.duplicated().any() or sch.HRU.duplicated().any() or sch.svat_repr.duplicated().any():
        raise ValueError("duplicate HRU or SVAT identity")
    if set(mem.HRU)!=set(sch.HRU):raise ValueError("schema/membership HRU domain mismatch")
    mem["dqsat"]=sample_centres(grid,mem.x,mem.y)
    representatives=dict(zip(sch.HRU,sch.svat_repr))
    records=[]
    for hid, group in mem.groupby("HRU",sort=True):
        rep=representatives[hid]
        selected=group[group.svat_orig==rep]
        if len(selected)!=1:raise ValueError("representative SVAT not in its own HRU")
        summary=summarize(group.dqsat,selected.iloc[0].dqsat,grid.nodata)
        records.append(dict(hru=hid,representative_svat=rep,
                            representative_dqsat=summary["positive_median"],**summary))
    return pd.DataFrame(records).sort_values("hru").reset_index(drop=True)



def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schema",type=Path,required=True)
    p.add_argument("--relation",type=Path,required=True)
    p.add_argument("--dqsat-grid",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=prepare(pd.read_csv(a.schema,low_memory=False),
                   pd.read_csv(a.relation,low_memory=False),
                   read_ascii_grid(a.dqsat_grid))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(a.output,index=False)
    print(f"HRUs: {len(result)}")
    return 0
if __name__=="__main__":raise SystemExit(main())
