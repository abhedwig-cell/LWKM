"""Explicit original or owner-accepted reconstructed raster bindings -> daily cell/HRU flux shards, one day in memory."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.idf_reader import read_idf
from tools.modflow_daily_rasters import mosaic,into_cell_from_faces,integrate_intervals
from tools.groundwater_l1_boundary import aggregate
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def bound(meta):
    p=Path(meta['path'])
    if sha256(p)!=meta['sha256']:raise ValueError('bound input hash mismatch: '+str(p))
    return p


def process(plan,output,*,allow_estimated_wel=False):
    cfg=json.loads(plan.read_text());reference=read_idf(bound(cfg['grid']))
    membership=pd.read_csv(bound(cfg['membership']))
    if not set(['row','col','hru_id','cell_id','area_m2'])<=set(membership):raise ValueError('membership raster indices required')
    if membership.duplicated(['row','col']).any():raise ValueError('overlapping physical member cells')
    rows=membership.row.to_numpy(int);cols=membership.col.to_numpy(int)
    if ((rows<0)|(cols<0)|(rows>=reference.nrow)|(cols>=reference.ncol)).any():raise ValueError('membership outside grid')
    activity=mosaic([bound(cfg['model_activity_mask'])],reference)
    if not (activity[rows,cols]==1).all():raise ValueError('membership contains inactive/unknown model cells')
    if not (membership.area_m2==reference.dx*reference.dy).all():raise ValueError('support/geometry mismatch')
    # A source contract is mandatory, but does not itself grant admission.
    for key in ['signs_evidence','units_evidence','time_evidence','package_coverage_evidence']:
        bound(cfg[key])
    if cfg['layer']!=1 or cfg['units']!='m3/day_rate':raise ValueError('unresolved layer/units')
    accepted={'ORIGINAL_BUDGET','RECONSTRUCTED_OPERATIONAL'}
    for role in ['ghb','wel']:
        provenance=cfg[role+'_provenance']
        if provenance=='RECONSTRUCTED_OPERATIONAL':
            contract=cfg.get('reconstructed_products',{}).get(role,{})
            if not contract.get('limitations') or not contract.get('method'):
                raise ValueError('reconstructed product requires method and limitations: '+role)
            bound(contract['evidence'])
        elif provenance not in accepted and not (role=='wel' and allow_estimated_wel):
            raise ValueError('unqualified '+role+' provenance; bind reconstructed operational contract')
    output.mkdir(parents=True,exist_ok=True);reports=[]
    for day in pd.date_range(cfg['start'],cfg['end']).strftime('%Y-%m-%d'):
        lo=pd.Timestamp(day);hi=lo+pd.Timedelta(days=1)
        records=[x for x in cfg['intervals'] if pd.Timestamp(x['start'])<hi and pd.Timestamp(x['end'])>lo]
        if records and any(set(x['components'])!=set(records[0]['components']) for x in records):raise ValueError('mixed component modes within day')
        five=all(set(x['components'])=={'flf','frf','fff','ghb','wel'} for x in records) and bool(records)
        rates={k:[] for k in (['flf','frf','fff','ghb','wel'] if five else ['flf','lat','ghb','wel'])}
        for rec in records:
            roles=set(rec['components'])
            if roles not in ({'flf','lat','ghb','wel'},{'flf','frf','fff','ghb','wel'},{'flf','right','front','ghb','wel'}):raise ValueError('wrong component set; do not mix net LAT and faces or include RIV/DRN/STO/MSW')
            values={}
            for role,terms in rec['components'].items():
                if not terms:raise ValueError('missing component terms')
                needed=np.zeros(reference.values.shape,dtype=bool);needed[rows,cols]=True
                operations={x.get('spatial_operation','CELL_NET') for x in terms}
                if len(operations)!=1:raise ValueError('mixed spatial operations')
                operation=operations.pop()
                allowed={'CELL_NET','SAVED_CURRENT_MINUS_PREVIOUS_COLUMN','SAVED_CURRENT_MINUS_PREVIOUS_ROW'}
                if operation not in allowed:raise ValueError('unbound spatial operation')
                if operation!='CELL_NET' and (role,operation) not in [('frf','SAVED_CURRENT_MINUS_PREVIOUS_COLUMN'),('fff','SAVED_CURRENT_MINUS_PREVIOUS_ROW')]:raise ValueError('wrong reconstructed component operation')
                if role=='right' or operation=='SAVED_CURRENT_MINUS_PREVIOUS_COLUMN':needed[rows[cols>0],cols[cols>0]-1]=True
                if role=='front' or operation=='SAVED_CURRENT_MINUS_PREVIOUS_ROW':needed[rows[rows>0]-1,cols[rows>0]]=True
                arr=np.zeros(reference.values.shape)
                for term in terms:
                    if term['layer']!=1:raise ValueError('non-layer1 package term')
                    if term['positive_multiplier'] not in [-1,1]:raise ValueError('unresolved component sign')
                    data=mosaic([bound(x) for x in term['partitions']],reference)
                    if term.get('activity_mask'):
                        mask=mosaic([bound(term['activity_mask'])],reference)
                        if not np.isin(mask[needed],[0.,1.]).all():raise ValueError('unknown package activity')
                        if np.any(needed&(mask==1)&~np.isfinite(data)):raise ValueError('missing active package values')
                        data=np.where(mask==0,0.,data)
                    arr+=data*term['positive_multiplier']
                if operation=='SAVED_CURRENT_MINUS_PREVIOUS_COLUMN':
                    previous=np.zeros_like(arr);previous[:,1:]=arr[:,:-1];arr=arr-previous
                elif operation=='SAVED_CURRENT_MINUS_PREVIOUS_ROW':
                    previous=np.zeros_like(arr);previous[1:]=arr[:-1];arr=arr-previous
                values[role]=arr
            if 'lat' not in values and 'frf' not in values:
                values['lat']=into_cell_from_faces(values.pop('right'),values.pop('front'))
            for role in rates:rates[role].append((max(pd.Timestamp(rec['start']),lo),min(pd.Timestamp(rec['end']),hi),values[role][rows,cols]))
        cells=pd.DataFrame(dict(date=day,cell_id=membership.cell_id))
        for role,intervals in rates.items():cells[role]=integrate_intervals(intervals,start=day,end=day)[day]
        if five:cells['lat']=cells.frf+cells.fff
        hru=aggregate(cells,membership[['hru_id','cell_id','area_m2']],start=day,end=day,full_cell_area=reference.dx*reference.dy)
        if five:
            joined=cells.merge(membership[['hru_id','cell_id']],on='cell_id',validate='one_to_one')
            for component in ['frf','fff']:
                sums=joined.groupby('hru_id')[component].sum()
                hru[component+'_net_m3_d']=hru.hru_id.map(sums)
                hru[component+'_mm_d']=1000*hru[component+'_net_m3_d']/hru.area_m2
        row=dict(date=day,production_admitted=False,files={})
        for kind,frame in [('cells',cells),('hrus',hru)]:
            target=output/f'{day}-{kind}.csv';data=frame.to_csv(index=False,float_format='%.12g').encode()
            reuse=target.exists() and target.read_bytes()==data
            if not reuse:
                temp=target.with_suffix('.partial');temp.write_bytes(data);temp.replace(target)
            row['files'][kind]=dict(path=str(target.resolve()),sha256=sha256(target),reused=reuse)
        reports.append(row)
    result=dict(plan_sha256=sha256(plan),code_sha256=sha256(Path(__file__)),wel_provenance=cfg['wel_provenance'],ghb_provenance=cfg['ghb_provenance'],reconstructed_products=cfg.get('reconstructed_products',{}),production_admitted=False,days=reports)
    atomic_json(output/'manifest.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--allow-estimated-wel',action='store_true')
    a=p.parse_args();r=process(a.plan,a.output,allow_estimated_wel=a.allow_estimated_wel);print(len(r['days']))
