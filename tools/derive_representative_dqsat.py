"""HRU-agnostic representative-SVAT dqsat derivation.

Reads current HRU schema, membership coordinates and source raster. Does not
assume 10,242 HRUs, legacy-majority soil or a fixed representative lookup.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from tools.compare_dqsat_authority import read_ascii_grid, sample_centres


def derive(schema:pd.DataFrame,relation:pd.DataFrame,grid,*,allow_zero:bool=False):
    required_schema={"HRU","svat_repr"}
    required_relation={"HRU","svat_orig","x","y"}
    if not required_schema.issubset(schema.columns):
        raise ValueError("schema missing HRU/svat_repr")
    if not required_relation.issubset(relation.columns):
        raise ValueError("relation missing HRU/svat_orig/x/y")
    s=schema[["HRU","svat_repr"]].copy()
    r=relation[["HRU","svat_orig","x","y"]].copy()
    for col in ("HRU","svat_repr"):
        s[col]=pd.to_numeric(s[col],errors="raise").astype("int64")
    for col in ("HRU","svat_orig"):
        r[col]=pd.to_numeric(r[col],errors="raise").astype("int64")
    if s.HRU.duplicated().any() or r.svat_orig.duplicated().any():
        raise ValueError("duplicate HRU or SVAT identity")
    if s.svat_repr.duplicated().any():
        raise ValueError("duplicate representative SVAT")
    joined=s.merge(r,left_on=["HRU","svat_repr"],right_on=["HRU","svat_orig"],
                   how="left",validate="one_to_one",indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("representative SVAT not in its own HRU")
    values=sample_centres(grid,joined.x,joined.y)
    if (~np.isfinite(values)).any() or np.isclose(values,grid.nodata).any():
        raise ValueError("invalid representative dqsat raster sample")
    if (values<0).any() or ((values==0).any() and not allow_zero):
        raise ValueError("representative dqsat must be positive")
    return pd.DataFrame({"hru":joined.HRU.to_numpy(),
                         "representative_svat":joined.svat_repr.to_numpy(),
                         "representative_dqsat":values}).sort_values("hru").reset_index(drop=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schema",type=Path,required=True)
    p.add_argument("--relation",type=Path,required=True)
    p.add_argument("--dqsat-grid",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=derive(pd.read_csv(a.schema,low_memory=False),
                  pd.read_csv(a.relation,low_memory=False),
                  read_ascii_grid(a.dqsat_grid))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(a.output,index=False)
    print(f"HRUs: {len(result)}")
    return 0

if __name__=="__main__":raise SystemExit(main())
