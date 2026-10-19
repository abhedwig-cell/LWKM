"""Join hash-bound daily HRU/weather shards and emit strict MET/BBC bindings."""
import argparse,json
from pathlib import Path
import pandas as pd
from tools.daily_forcing import modern_met,effective_bbc
from tools.process_daily_budget_plan import bound
from tools.run_dra_protected_population import atomic_json
from tools.assemble_swap_package import sha256


def consume(plan,output):
    cfg=json.loads(plan.read_text());output.mkdir(parents=True,exist_ok=True)
    flux=pd.concat([pd.read_csv(bound(x)) for x in cfg['hru_flux_shards']],ignore_index=True)
    weather=pd.concat([pd.read_csv(bound(x)) for x in cfg['weather_shards']],ignore_index=True)
    if flux.duplicated(['hru_id','date']).any() or weather.duplicated(['hru_id','date']).any():raise ValueError('duplicate HRU/day input')
    rows=[]
    for hid in cfg['eligible_hrus']:
        row=dict(hru_id=hid,production_admitted=False)
        try:
            gw=flux[flux.hru_id==hid].sort_values('date');met=weather[weather.hru_id==hid].sort_values('date')
            if gw.empty:raise ValueError('MISSING_HRU_DAILY_GW_COMPONENTS')
            if met.empty:raise ValueError('MISSING_HRU_DAILY_MET')
            bbc=effective_bbc(gw,start=cfg['start'],end=cfg['end'])
            met_text=modern_met(met,start=cfg['start'],end=cfg['end'],station=hid)
            assets={}
            for ext,text in [('bbc',bbc),('met',met_text)]:
                p=output/f'{hid}.{ext}';data=text.encode();reuse=p.exists() and p.read_bytes()==data
                if not reuse:p.write_bytes(data)
                assets[p.name]=dict(path=str(p.resolve()),sha256=sha256(p),logical_id=f'W_A_{hid}_{ext}',qualification_status='CANDIDATE_NOT_ADMITTED',
                    semantic_contract='GW_L1_DAILY_MEAN_CONSTANT_INTERVAL' if ext=='bbc' else 'STRICT_DAILY_MET_CANONICAL_UNITS',evidence_refs=[str(plan.resolve())],reused=reuse)
            row.update(status='FORCING_PAIR_CANDIDATE',assets=assets)
        except (ValueError,IndexError) as e:row.update(status='BLOCKED',error=str(e))
        rows.append(row)
    result=dict(plan_sha256=sha256(plan),start=cfg['start'],end=cfg['end'],population=len(rows),complete_pairs=sum(r['status']=='FORCING_PAIR_CANDIDATE' for r in rows),production_admitted=False,runs=rows)
    atomic_json(output/'manifest.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=consume(a.plan,a.output);print(r['complete_pairs'])
