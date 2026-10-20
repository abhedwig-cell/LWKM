"""Fixed 1 km HRU weights -> daily MET, with audited spatial exceptions.

Daily normal sampling uses the compressed HRU/grid table. Only SVATs in
missing/invalid grid cells require original-coordinate nearest-valid lookup.
Rain and WET_RAW are combined before HRU aggregation, including exceptions.
"""
import argparse
import hashlib
import json
import sys
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from tools.hru_grid_weights import cells, header, sha
from tools.daily_forcing import MET_COLUMNS
from tools.run_dra_protected_population import atomic_json

FIELDS=[x for x in MET_COLUMNS if x!='wet_fraction']+['wet_raw_fraction']
UNITS=dict(zip(FIELDS,['kJ/m2/day','degC','degC','kPa','m/s_at_10m','mm/day','mm/day','day_fraction']))

def geometry(g):
    if any(not np.isfinite(g[k]) for k in g) or g['cellsize']<=0:
        raise ValueError('invalid grid geometry')
    for k in ['ncols','nrows']:
        if g[k]<=0 or g[k]!=int(g[k]):raise ValueError('invalid grid dimensions')
    return {k:g[k] for k in ['ncols','nrows','xllcorner','yllcorner','cellsize']}

def support(members,g):
    w=cells(members,g)
    m=members.copy()
    nc,nr=int(g['ncols']),int(g['nrows'])
    c=np.floor((m.x_rd-g['xllcorner'])/g['cellsize']).astype(int)
    r=nr-1-np.floor((m.y_rd-g['yllcorner'])/g['cellsize']).astype(int)
    m['grid_id']=r*nc+c
    m['member_weight']=m.area_m2/m.groupby('hru_id').area_m2.transform('sum')
    return w,m

def valid_values(a,key,g):
    ok=np.isfinite(a)&(a!=g['nodata_value'])
    if key in ['rad_kj_m2_d','vapour_pressure_kpa','wind_m_s','rain_mm_d','etref_mm_d']:
        ok &= a>=0
    if key=='vapour_pressure_kpa':ok &= a<=10
    if key=='wet_raw_fraction':ok &= (a>=0)&(a<=1)
    return ok

def nearest(points,valid_ids,g):
    """Projected metric distance; ties resolve by ascending row-major grid ID."""
    nc=int(g['ncols']);step=g['cellsize']
    xy=np.column_stack([g['xllcorner']+(valid_ids%nc+.5)*step,
                        g['yllcorner']+(int(g['nrows'])-valid_ids//nc-.5)*step])
    tree=cKDTree(xy);distance,index=tree.query(points)
    # cKDTree does not promise deterministic ties. Resolve only tied queries.
    if len(valid_ids)>1:
        two=tree.query(points,k=2)[0]
        for i in np.flatnonzero(np.isclose(two[:,0],two[:,1],rtol=0,atol=1e-8)):
            choices=tree.query_ball_point(points[i],distance[i]+1e-8)
            d=np.linalg.norm(xy[choices]-points[i],axis=1)
            candidates=np.asarray(choices)[np.isclose(d,d.min(),rtol=0,atol=1e-8)]
            index[i]=candidates[np.argmin(valid_ids[candidates])]
    return valid_ids[index],distance

def day(weights,members,arrays,g,day_id,source_hashes=None):
    nc,nr=int(g['ncols']),int(g['nrows'])
    ids=np.sort(weights.hru_id.unique());hid_to_ix={v:i for i,v in enumerate(ids)}
    wi=weights.hru_id.map(hid_to_ix).to_numpy();wg=weights.grid_id.to_numpy(int)
    wh=weights.weight.to_numpy();member_g=members.grid_id.to_numpy(int)
    mi=members.hru_id.map(hid_to_ix).to_numpy();mw=members.member_weight.to_numpy()
    filled={};exceptions={};audit=[]
    for key in FIELDS:
        a=np.asarray(arrays[key],dtype=float)
        if a.shape!=(nr,nc):raise ValueError('grid shape mismatch: '+key)
        flat=a.ravel();ok=valid_values(flat,key,g);valid=np.flatnonzero(ok)
        if not len(valid):
            if key!='wet_raw_fraction':raise ValueError('no valid meteorological cell: '+key)
            filled[key]=np.full_like(flat,np.nan);exceptions[key]={};continue
        base=flat.copy();bad=np.flatnonzero(~ok)
        if len(bad):
            xy=np.column_stack([g['xllcorner']+(bad%nc+.5)*g['cellsize'],g['yllcorner']+(nr-bad//nc-.5)*g['cellsize']])
            replacement,_=nearest(xy,valid,g);base[bad]=flat[replacement]
        filled[key]=base
        ix=np.flatnonzero(~ok[member_g]);exceptions[key]={}
        if len(ix):
            chosen,dist=nearest(members.iloc[ix][['x_rd','y_rd']].to_numpy(),valid,g)
            for i,c,d in zip(ix,chosen,dist):
                exceptions[key][int(i)]=float(flat[c])
                audit.append(dict(date=day_id,variable=key,svat_id=int(members.svat_id.iloc[i]),
                    hru_id=int(members.hru_id.iloc[i]),source_grid=int(member_g[i]),replacement_grid=int(c),
                    distance_m=float(d),source_sha256=(source_hashes or {}).get(key)))
    def wet(p,r):return np.where(p==0,0.,np.where(np.isfinite(r)&(r>0),r,.1))
    filled['wet_fraction']=wet(filled['rain_mm_d'],filled['wet_raw_fraction'])
    out=pd.DataFrame({'hru_id':ids,'date':day_id})
    for key in MET_COLUMNS:
        values=filled[key]
        result=np.bincount(wi,weights=wh*values[wg],minlength=len(ids))
        ex=exceptions.get(key,{})
        if key=='wet_fraction':
            affected=set(exceptions['rain_mm_d'])|set(exceptions['wet_raw_fraction'])
            ex={i:float(wet(exceptions['rain_mm_d'].get(i,filled['rain_mm_d'][member_g[i]]),
                            exceptions['wet_raw_fraction'].get(i,filled['wet_raw_fraction'][member_g[i]]))) for i in affected}
        for i,v in ex.items():result[mi[i]]+=mw[i]*(v-values[member_g[i]])
        out[key]=result
    if (out.tmin_c>out.tmax_c).any():raise ValueError('mixed spatial sources produce Tmin>Tmax')
    # Count/weight fallback on the exact support, without redoing area fractions.
    p=filled['rain_mm_d'][member_g].copy();raw=filled['wet_raw_fraction'][member_g].copy()
    for i,v in exceptions['rain_mm_d'].items():p[i]=v
    for i,v in exceptions['wet_raw_fraction'].items():raw[i]=v
    fallback=(p>0)&(~np.isfinite(raw)|(raw<=0))
    summary=dict(date=day_id,nearest_valid_svat_values=len(audit),fallback_svat_count=int(fallback.sum()),
                 fallback_area_m2=float(members.area_m2.to_numpy()[fallback].sum()),
                 rain_zero_duration_corrected_svat_count=int(((p==0)&np.isfinite(raw)&(raw>0)).sum()),
                 wind_measurement_height_m=10,production_admitted=False)
    return out,pd.DataFrame(audit),summary

def run(plan,output):
    cfg=json.loads(plan.read_text());output.mkdir(parents=True,exist_ok=True)
    from tools.process_daily_budget_plan import bound
    members=pd.read_csv(bound(cfg['members']))
    g=cfg['geometry'];geometry(g)
    weights,ms=support(members,g)
    if len(members)!=cfg['expected_members'] or len(weights.hru_id.unique())!=cfg['expected_hrus']:
        raise ValueError('meteorology support population mismatch')
    if cfg['units']!=UNITS:raise ValueError('explicit canonical raster units required')
    days=pd.date_range(cfg['start'],cfg['end']).strftime('%Y-%m-%d').tolist()
    if sorted(cfg['days'])!=days:raise ValueError('missing/extra daily meteorological raster bindings')
    weight_path=output/'weights.csv';data=weights.to_csv(index=False,float_format='%.15g')
    if not weight_path.exists() or weight_path.read_text()!=data:weight_path.write_text(data)
    results=[]
    code_hash=sha(Path(sys.executable) if getattr(sys,'frozen',False) else Path(__file__))
    weight_hash=sha(weight_path)
    for stamp in days:
        bindings=cfg['days'][stamp]
        if set(bindings)!=set(FIELDS):raise ValueError('incomplete daily variable set')
        paths={k:bound(v) for k,v in bindings.items()}
        hashes={k:bindings[k]['sha256'] for k in paths}
        identity={'inputs':hashes,'members':cfg['members']['sha256'],'weights':weight_hash,
                  'geometry':g,'transforms':cfg.get('transforms',{}),'code':code_hash,'date':stamp,'units':cfg['units']}
        target=output/(stamp+'.csv');marker=output/(stamp+'.json');qa=output/(stamp+'-qa.csv')
        cached=json.loads(marker.read_text()) if marker.exists() else {}
        reuse=cached.get('identity')==identity and target.exists() and qa.exists() and cached.get('sha256')==sha(target) and cached.get('qa_sha256')==sha(qa)
        if not reuse:
            arrays={}
            for k,p in paths.items():
                gh=header(p)
                if geometry(gh)!=geometry(g):raise ValueError('different geometry requires separate support: '+k)
                a=np.loadtxt(p,skiprows=6).reshape(int(g['nrows']),int(g['ncols']))
                a[a==gh['nodata_value']]=np.nan
                if k in cfg.get('transforms',{}):
                    t=cfg['transforms'][k];valid=np.isfinite(a)&(a!=g['nodata_value'])
                    if not np.isfinite([t['scale'],t['offset']]).all() or t['scale']<=0 or not t.get('input_unit') or not t.get('evidence'):raise ValueError('unbound raster conversion')
                    a[valid]=a[valid]*t['scale']+t['offset']
                arrays[k]=a
            frame,audit,summary=day(weights,ms,arrays,g,stamp,hashes)
            frame.to_csv(target.with_suffix('.partial'),index=False,float_format='%.12g');target.with_suffix('.partial').replace(target)
            audit.to_csv(qa,index=False)
            atomic_json(marker,dict(identity=identity,sha256=sha(target),qa_sha256=sha(qa),summary=summary))
        results.append(dict(date=stamp,path=str(target.resolve()),sha256=sha(target),reused=reuse))
    transfer=dict(schema_version=1,product_kind='MET',dataset_id=cfg['dataset_id'],population_sha256=cfg['members']['sha256'],
                  source_manifest_sha256=sha(plan),source_manifest_path='source-plan.json',producer_sha256=code_hash,units='canonical_MET_units_v1',
                  start=cfg['start'],end=cfg['end'],hru_ids=sorted(map(int,weights.hru_id.unique())),status='RESEARCH_CANDIDATE',
                  files=[{**r,'path':Path(r['path']).name} for r in results])
    shutil.copyfile(plan,output/'source-plan.json')
    atomic_json(output/'transfer.json',transfer)
    atomic_json(output/'manifest.json',dict(files=results,production_admitted=False,weights_sha256=sha(weight_path)))
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(len(run(a.plan,a.output)))
