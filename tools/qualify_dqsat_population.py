"""Compare owner-preferred dqsat variants on actual schema/membership/raster."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.prepare_dra_positive_median_dqsat import prepare
from tools.compare_dqsat_authority import read_ascii_grid
from tools.server.check_swp_source_values import grid, sample, sha
from tools.server.dqsat_source import DQSAT_SHA256
from tools.dqsat_policy import summarize


def qualify(schema_path, membership_path, raster, output):
    if sha(raster) != DQSAT_SHA256:
        raise ValueError('not the identified dqsat raster')
    schema=pd.read_csv(schema_path)
    members=pd.read_csv(membership_path).rename(columns={'svat':'svat_orig'})
    dra=prepare(schema,members,read_ascii_grid(raster)).set_index('hru')
    # Independent server raster reader/sampler, retaining exact NoData sentinels.
    values,g=grid(raster)
    xy=members[['x','y']].to_numpy(float)
    _,coverage=sample(values,g,xy)
    if coverage['outside'] or coverage['off_center']:
        raise ValueError('server sampling geometry mismatch')
    col=np.floor((xy[:,0]-g['xmin'])/g['dx']).astype(int)
    row=np.floor((g['ymin']+g['nrows']*g['dy']-xy[:,1])/g['dy']).astype(int)
    members['dqsat']=values[row,col]
    reps=dict(zip(schema.HRU,schema.svat_repr))
    for hid,group in members.groupby('HRU'):
        raw=group.dqsat.to_numpy()
        rep=float(group.loc[group.svat_orig==reps[hid],'dqsat'].iloc[0])
        server=summarize(raw,rep,g['nodata'])
        for key,value in server.items():
            if dra.loc[hid,key] != value:
                raise ValueError(f'SWP/DRA mismatch {hid} {key}')
        valid=raw[(raw!=g['nodata']) & (raw>0)]
        if server['positive_median'] != float(np.median(valid)):
            raise ValueError(f'independent median mismatch {hid}')
    output.mkdir(parents=True,exist_ok=True)
    table=output/'dqsat_hru.csv'
    dra.reset_index().to_csv(table,index=False)
    distributions={}
    for field in ('source_representative_dqsat','positive_median','positive_mean','candidate_spacing_m'):
        v=dra[field]
        if field=='source_representative_dqsat':v=v[~dra.representative_is_nodata]
        distributions[field]={str(k):float(v.quantile(k)) for k in (0,.05,.5,.95,1)}
    positive_rep=dra.source_representative_dqsat>0
    positive_rep &= ~dra.representative_is_nodata
    relative=(dra.loc[positive_rep,'positive_median']/dra.loc[positive_rep,'source_representative_dqsat']-1)
    extremes=(relative.abs().sort_values(ascending=False).head(20).index)
    summary=dict(status='REAL_SOURCE_POPULATION_METHOD_CONSISTENCY_PASS',
        production_admitted=False, swap_response_validated=False,
        hrus=len(dra),svats=len(members),server_dra_mismatches=0,
        representative_zero_hrus=int((dra.source_representative_dqsat==0).sum()),
        representative_nodata_hrus=int(dra.representative_is_nodata.sum()),
        changed_from_representative_hrus=int(dra.discriminating.sum()),
        changed_from_positive_mean_hrus=int((dra.positive_median!=dra.positive_mean).sum()),
        zero_member_samples=int(dra.zero_count.sum()),nodata_member_samples=int(dra.nodata_count.sum()),
        distributions=distributions,
        median_relative_difference_from_positive_representative=float(relative.median()),
        max_absolute_relative_difference_from_positive_representative=float(relative.abs().max()),
        extreme_hrus=dra.loc[extremes].reset_index().to_dict('records'),
        sources={key:dict(name=path.name,sha256=sha(path)) for key,path in
                 dict(schema=schema_path,membership=membership_path,raster=raster).items()},
        table_sha256=sha(table))
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('schema','membership','raster','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    result=qualify(args.schema,args.membership,args.raster,args.output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('extreme_hrus','distributions','sources')}))
