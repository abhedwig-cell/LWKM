"""Real 2018 rain/evaporation rasters -> all-member UOPP-weighted HRU candidates."""
import argparse,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from tools.lhm_postprocess import read_ascii_grid
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def run(rain,evap,relation,svat,out,day):
    out.mkdir(parents=True,exist_ok=True);grids=[];identities=[]
    for kind,p in [('rain',rain),('evap',evap)]:
        with zipfile.ZipFile(p) as z:
            matches=[n for n in z.namelist() if n.lower().endswith('.asc') and day.replace('-','') in n]
            if len(matches)!=1:raise ValueError('ambiguous/missing meteorological day')
            raw=z.read(matches[0]);dest=out/(kind+'.asc');dest.write_bytes(raw);g=read_ascii_grid(dest)
            grids.append(g);identities.append(dict(archive=p.name,sha256=sha256(p),member=matches[0],member_sha256=sha256(dest)))
    a,b=grids
    if (a.ncols,a.nrows,a.xllcorner,a.yllcorner,a.cellsize)!=(b.ncols,b.nrows,b.xllcorner,b.yllcorner,b.cellsize):raise ValueError('meteo geometries differ')
    members=pd.read_csv(relation,low_memory=False);areas=pd.read_csv(svat,usecols=['svat','opp(m2)'])
    members=members.merge(areas,left_on='svat_orig',right_on='svat',validate='one_to_one')
    expected=len(pd.read_csv(relation,usecols=['svat_orig']))
    if len(members)!=expected:raise ValueError('missing SVAT area binding')
    area=members['opp(m2)'].to_numpy(float)
    if not np.isfinite(area).all() or (area<0).any():raise ValueError('invalid UOPP')
    cols=np.floor((members.x-a.xllcorner)/a.cellsize).astype(int)
    rows=np.floor((a.yllcorner+a.nrows*a.cellsize-members.y)/a.cellsize).astype(int)
    if ((cols<0)|(rows<0)|(cols>=a.ncols)|(rows>=a.nrows)).any():raise ValueError('meteo support outside grid')
    members['area']=area;members['pixel_id']=rows*a.ncols+cols
    weights=members.groupby(['HRU','pixel_id'],sort=True).area.sum().reset_index();weights=weights[weights.area>0].copy()
    totals=weights.groupby('HRU').area.transform('sum');weights['weight']=weights.area/totals
    rr=(weights.pixel_id//a.ncols).to_numpy(int);cc=(weights.pixel_id%a.ncols).to_numpy(int)
    result=weights.groupby('HRU').area.sum().to_frame('uopp_m2')
    for key,g in zip(['rain_source_value','etref_source_value'],grids):
        v=g.values[rr,cc];valid=np.isfinite(v)&(v!=g.nodata)&(v>=0)
        weighted=pd.Series(v*weights.weight.to_numpy(),index=weights.index).where(valid)
        # min_count cannot alone detect partial missing pixels: require every
        # positively weighted pixel for each HRU.
        result[key]=weighted.groupby(weights.HRU).sum()
        bad=set(weights.loc[~valid,'HRU']);result.loc[result.index.isin(bad),key]=np.nan
    result['date']=day;result['status']=np.where(result[['rain_source_value','etref_source_value']].notna().all(axis=1),'PARTIAL_WEATHER_CANDIDATE','SOURCE_PIXEL_MISSING')
    result.to_csv(out/'hru-rain-etref.csv',float_format='%.12g');weights.to_csv(out/'uopp-pixel-weights.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    report=dict(day=day,hrus=len(result),complete_rain_etref_hrus=int((result.status=='PARTIAL_WEATHER_CANDIDATE').sum()),
        weighting='ALL_ORIGINAL_MEMBERS_UOPP_CANDIDATE_NOT_LEGACY_DONOR_SELECTION',units='SOURCE_METADATA_CONFIRMATION_REQUIRED',
        missing_met_fields=['temperature_min','temperature_max','radiation','vapour_pressure','wind','precipitation_duration'],
        source_archives=identities,membership_sha256=sha256(relation),svat_area_source_sha256=sha256(svat),code_sha256=sha256(Path(__file__)),production_admitted=False)
    atomic_json(out/'audit.json',report);print(json.dumps(report));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['rain','evap','relation','svat','out']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--day',default='2018-01-01');a=p.parse_args();run(a.rain,a.evap,a.relation,a.svat,a.out,a.day)
