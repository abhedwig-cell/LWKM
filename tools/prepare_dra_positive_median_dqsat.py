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
from tools.derive_representative_dqsat import derive


def prepare(schema,relation,grid):
    rep=derive(schema,relation,grid,allow_zero=True)
    required={"HRU","svat_orig","x","y"}
    if not required.issubset(relation):
        raise ValueError("relation missing member sampling columns")
    mem=relation[["HRU","svat_orig","x","y"]].copy()
    if mem.svat_orig.duplicated().any():raise ValueError("duplicate SVAT member")
    mem["hru"]=pd.to_numeric(mem.HRU,errors="raise").astype(int)
    vals=sample_centres(grid,mem.x,mem.y)
    if (~np.isfinite(vals)).any() or np.isclose(vals,grid.nodata).any():
        raise ValueError("member dqsat samples invalid or NODATA cell")
    if (vals<0).any():raise ValueError("negative member dqsat")
    mem["dqsat"]=vals
    positive=mem[mem.dqsat>0].groupby("hru").dqsat.agg(
        positive_median="median",positive_mean="mean",
        positive_count="count")
    out=rep.merge(positive,on="hru",how="left",validate="one_to_one")
    if out.positive_median.isna().any():
        raise ValueError("HRU has no positive dqsat members")
    out["source_representative_dqsat"]=out.representative_dqsat
    out["representative_dqsat"]=out.positive_median
    out["dqsat_method"]="POSITIVE_MEMBER_MEDIAN_CANDIDATE"
    out["discriminating"]=out.source_representative_dqsat.ne(out.representative_dqsat)
    return out.sort_values("hru").reset_index(drop=True)


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
