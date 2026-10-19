"""Bounded owner-policy effects and comparison with the preceding Work C population."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.dra_level_compression import PhysicalDrainageSystem,_level_on
from tools.dra_protected_compression import _level
from tools.work_c_drainage import atomic_json


def response(systems,h,day,branch):
    return sum(getattr(s,branch+'_conductance')*max((_level_on(s,day)-h) if branch=='drainage' else (h-_level_on(s,day)),0.) for s in systems)


def assess(current,previous,output):
    output.mkdir(parents=True,exist_ok=True);rows=[];events=[];blocked=[]
    with gzip.open(output/'drainage-checkpoints.jsonl.gz','wt') as zipped:
        for path in sorted((current/'hrus').glob('*.json'),key=lambda p:int(p.stem)):
            r=json.loads(path.read_text());zipped.write(json.dumps(r,separators=(',',':'))+'\n')
            old=json.loads((previous/'hrus'/path.name).read_text())
            d=r.get('owner_decision',{});physical=[];retained=[]
            for key,target in [('physical',physical),('retained_physical',retained)]:
                for x in r.get(key,[]):target.append(PhysicalDrainageSystem(**x))
            error=0.
            # Explicit finite test envelope, depths relative to surface (m).
            # 0..5 m is a diagnostic envelope, not a bound on all future heads.
            for day in sorted({d for s in physical+retained for d,v in (s.level_series or [])}|{'1971-01-01','1971-07-01'}):
                heads={0.,5.}|{_level_on(s,day) for s in physical+retained if 0.<=_level_on(s,day)<=5.}
                for h in heads:
                    for branch in ['drainage','infiltration']:
                        error=max(error,1000*abs(response(physical,h,day,branch)-response(retained,h,day,branch)))
            e=d.get('events',[])
            for x in e:events.append(dict(hru=r['hru'],**x))
            row=dict(hru=r['hru'],old_status=old['status'],status=r['status'],error=r.get('error',''),
                removed_records=sum(x['action']=='OMIT_DRAINAGE_SYSTEM' for x in e),
                infiltration_disabled=sum(x['action']=='DISABLE_INFILTRATION' for x in e),
                gd_before=d.get('drainage_g_before'),gd_after=d.get('drainage_g_after'),
                gi_before=d.get('infiltration_g_before'),gi_after=d.get('infiltration_g_after'),
                max_policy_response_difference_mm_d_envelope_0_5m=error,
                compression_changed=old.get('audit',{}).get('groups')!=r.get('audit',{}).get('groups'),
                originally_blocked_resolved=old['status']=='BLOCKED' and r['status']!='BLOCKED',
                newly_blocked=old['status']!='BLOCKED' and r['status']=='BLOCKED')
            rows.append(row)
            if r['status']=='BLOCKED':blocked.append({'hru':r['hru'],'error':r['error']})
    frame=pd.DataFrame(rows);frame.to_csv(output/'population-effects.csv',index=False)
    with gzip.open(output/'policy-events.json.gz','wt') as dst:json.dump(events,dst,separators=(',',':'))
    (output/'policy-events.json').unlink(missing_ok=True)
    atomic_json(output/'remaining-blockers.json',blocked)
    summary=dict(population=len(rows),candidates=int((frame.status=='DRA_INTERFACE_CANDIDATE').sum()),
        blocked=len(blocked),original_drares_overshoots=int(frame.removed_records.sum()),
        original_infres_overshoots=sum(x['infres']>100000 and x['infiltration_conductance_raw']>0 for p in (current/'hrus').glob('*.json') for x in json.loads(p.read_text()).get('physical',[]) if x['physical_active']),
        omitted_physical_records=int(frame.removed_records.sum()),
        disabled_infiltration_records=int(frame.infiltration_disabled.sum()),
        originally_blocked_resolved=int(frame.originally_blocked_resolved.sum()),
        newly_blocked=int(frame.newly_blocked.sum()),changed_compressions=int(frame.compression_changed.sum()),
        max_policy_response_difference_mm_d_envelope_0_5m=float(frame.max_policy_response_difference_mm_d_envelope_0_5m.max()),
        production_admitted=False)
    atomic_json(output/'population-summary.json',summary);print(json.dumps(summary));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['current','previous','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assess(a.current,a.previous,a.output)
