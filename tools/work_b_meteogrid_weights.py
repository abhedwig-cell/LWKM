"""Join Work B SVAT_QUALIFIED and HRU_MEMBERSHIP to fixed meteogrid weights.

Column names are explicitly bound; no inferred source schema.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from tools.hru_grid_weights import cells, header, sha


def build(svat, membership, template, fields, expected_hrus=10242, expected_members=427656):
    sc, mc = fields['svat_id_svat'], fields['svat_id_membership']
    req_s = [sc, fields['x'], fields['y'], fields['area']]
    req_m = [mc, fields['hru']]
    if not set(req_s).issubset(svat.columns) or not set(req_m).issubset(membership.columns):
        raise ValueError('Missing explicitly bound source columns')
    s = svat[req_s].rename(columns={sc:'svat_id',fields['x']:'x_rd',fields['y']:'y_rd',fields['area']:'area_m2'})
    m = membership[req_m].rename(columns={mc:'svat_id',fields['hru']:'hru_id'})
    if s.svat_id.duplicated().any() or m.svat_id.duplicated().any():
        raise ValueError('duplicate SVAT in source')
    joined = m.merge(s,on='svat_id',how='left',validate='one_to_one',indicator=True)
    if not joined._merge.eq('both').all():
        raise ValueError('unmatched membership SVAT')
    if len(joined)!=expected_members or joined.hru_id.nunique()!=expected_hrus:
        raise ValueError(f'population mismatch: {len(joined)} members, {joined.hru_id.nunique()} HRUs')
    return cells(joined.drop(columns='_merge'),header(template)), joined.drop(columns='_merge')


def main():
    p=argparse.ArgumentParser()
    for name in ('svat','membership','template','fields','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-hrus',type=int,default=10242)
    p.add_argument('--expected-members',type=int,default=427656)
    a=p.parse_args()
    fields=json.loads(a.fields.read_text())
    result,joined=build(pd.read_csv(a.svat),pd.read_csv(a.membership),a.template,fields,a.expected_hrus,a.expected_members)
    a.output.mkdir(parents=True,exist_ok=True)
    out=a.output/'hru_meteogrid_weights.csv'
    result.to_csv(out,index=False,float_format='%.15g')
    manifest={'status':'RECONSTRUCTION_CANDIDATE','svat_sha256':sha(a.svat),
              'membership_sha256':sha(a.membership),'template_sha256':sha(a.template),
              'fields_sha256':sha(a.fields),'weights_sha256':sha(out),
              'hrus':int(result.hru_id.nunique()),'members':len(joined),
              'grid_links':len(result),'area_m2':float(joined.area_m2.sum())}
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
