"""Convert sampled daily LHM and KNMI meteorology per SVAT into weighted HRU daily MET."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE = ['rad_kj_m2_d','tmin_c','tmax_c','vapour_pressure_kpa','rain_mm_d','etref_mm_d']
MET = ['rad_kj_m2_d','tmin_c','tmax_c','vapour_pressure_kpa','wind_m_s','rain_mm_d','etref_mm_d','wet_fraction']

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def aggregate(membership, lhm, knmi):
    for name,f,cols in [('membership',membership,['hru_id','svat_id']),('lhm',lhm,['svat_id','date']),('knmi',knmi,['svat_id','date'])]:
        if f.duplicated(cols).any():raise ValueError('duplicate '+name)
    if not {'hru_id','svat_id','area_m2'}.issubset(membership):raise ValueError('bad membership')
    if not {'svat_id','date',*BASE}.issubset(lhm):raise ValueError('bad LHM columns')
    if not {'svat_id','date','wind_m_s','wet_raw_fraction'}.issubset(knmi):raise ValueError('bad KNMI columns')
    if (membership.area_m2<=0).any() or not np.isfinite(membership.area_m2).all():raise ValueError('invalid areas')
    if lhm[BASE].isna().any().any() or not np.isfinite(lhm[BASE].to_numpy(dtype=float)).all():raise ValueError('invalid LHM values')
    if lhm[['rain_mm_d','rad_kj_m2_d','etref_mm_d']].lt(0).any().any() or (lhm.tmin_c>lhm.tmax_c).any():raise ValueError('invalid LHM met')
    j=lhm.merge(knmi,on=['svat_id','date'],how='left',validate='one_to_one',indicator=True)
    if (j._merge!='both').any():raise ValueError('missing KNMI sampling')
    if j.wind_m_s.isna().any() or not np.isfinite(j.wind_m_s).all() or (j.wind_m_s<0).any():raise ValueError('invalid WIND')
    raw=pd.to_numeric(j.wet_raw_fraction,errors='coerce')
    if (raw.notna()&((raw<=0)|(raw>1))).any():raise ValueError('raw duration must be positive or NODATA')
    j['wet_fraction']=np.where(j.rain_mm_d==0,0.,raw.fillna(0.1))
    j['wet_fallback']=((j.rain_mm_d>0)&raw.isna()).astype(int)
    j=j.merge(membership,on='svat_id',how='inner',validate='many_to_many')
    if j.empty:raise ValueError('no membership')
    sizes=membership.groupby('hru_id').svat_id.nunique()
    counts=j.groupby(['hru_id','date']).svat_id.nunique()
    if not counts.eq(counts.index.get_level_values('hru_id').map(sizes)).all():raise ValueError('partial HRU/day membership')
    dates=set(lhm.date.unique())
    if any(set(f.date)!=dates for _,f in j.groupby('hru_id')):raise ValueError('missing HRU days')
    j['weight']=j.area_m2/j.groupby(['hru_id','date']).area_m2.transform('sum')
    for key in MET:j[key]=j[key]*j.weight
    out=j.groupby(['hru_id','date'],sort=True)[MET].sum().reset_index()
    if ((out.rain_mm_d==0)&(out.wet_fraction!=0)).any() or ((out.rain_mm_d>0)&(out.wet_fraction<=0)).any():raise ValueError('inconsistent WET')
    audit=j.groupby(['hru_id','date']).agg(fallback_svat_count=('wet_fallback','sum'),member_count=('svat_id','nunique')).reset_index()
    return out,audit

def main():
    p=argparse.ArgumentParser()
    for name in ['membership','lhm-svat-met','knmi-svat-grids','output']:p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    inputs=[a.membership,a.lhm_svat_met,a.knmi_svat_grids]
    out,audit=aggregate(*(pd.read_csv(x) for x in inputs))
    out.to_csv(a.output/'hru_daily_met.csv',index=False,float_format='%.12g')
    audit.to_csv(a.output/'wet_audit.csv',index=False)
    files=[a.output/'hru_daily_met.csv',a.output/'wet_audit.csv']
    manifest={'schema_version':1,'input_sha256':{str(x):sha256(x) for x in inputs},'output_sha256':{str(x):sha256(x) for x in files},'hru_count':int(out.hru_id.nunique()),'days':int(out.date.nunique()),'status':'CANDIDATE_NOT_ADMITTED'}
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
