"""Bind existing daily IDFs only. Never derive WEL, GHB or LAT.

Configuration supplies explicit component directories/globs and semantic bindings.
Only selected dates are hashed. Output is directly consumable by the daily processor.
"""
import argparse,json,re
from pathlib import Path
import pandas as pd
from tools.process_daily_budget_plan import bound
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def bind(config,output):
    cfg=json.loads(config.read_text());base=cfg['processing_contract']
    if pd.Timestamp(base['end'])<pd.Timestamp(base['start']):raise ValueError('reversed binding period')
    dates=pd.date_range(base['start'],base['end']).strftime('%Y%m%d')
    if set(cfg['sources']) not in ({'flf','lat','ghb','wel'},{'flf','frf','fff','ghb','wel'}):raise ValueError('bind FLF FRF FFF GHB WEL, or explicit net LAT')
    for role,source in cfg['sources'].items():
        if '{date}' not in source['pattern'] or Path(source['pattern']).is_absolute() or '..' in Path(source['pattern']).parts:
            raise ValueError('component pattern must be relative and date selective')
        if source['positive_multiplier'] not in [-1,1] or not source.get('semantics_evidence'):
            raise ValueError('unresolved sign/semantics: '+role)
    intervals=[];missing=[];items=[]
    for day in dates:
        components={}
        for role,source in cfg['sources'].items():
            root=Path(source['directory'])
            # The root and filename patterns are supplied from existing registers,
            # not guessed. Recursive glob is limited to this component directory.
            pattern=source['pattern'].format(date=day)
            paths=sorted(p for p in root.glob(pattern) if p.is_file())
            if not paths:missing.append(dict(date=day,role=role,directory=str(root),pattern=pattern));continue
            partitions=[]
            for p in paths:
                if p.suffix.lower()!='.idf':raise ValueError('non-IDF selection')
                tokens=re.findall(r'(?<!\d)(\d{8})(?:\d{6})?(?!\d)',p.stem)
                if tokens!=[day]:raise ValueError('ambiguous/wrong filename date: '+str(p))
                b=dict(path=str(p.resolve()),sha256=sha256(p));partitions.append(b)
                items.append(dict(**b,logical_id=role+'_'+p.name,role=role,date=pd.Timestamp(day).date().isoformat(),layer=1,package=role.upper(),units=base['units'],consumer='W08-GW-L1',semantics_evidence=source['semantics_evidence'],provenance=source['provenance']))
            components[role]=[dict(layer=1,positive_multiplier=source['positive_multiplier'],spatial_operation=source.get('spatial_operation','CELL_NET'),partitions=partitions)]
        intervals.append(dict(start=pd.Timestamp(day).isoformat(),end=(pd.Timestamp(day)+pd.Timedelta(days=1)).isoformat(),components=components))
    output.mkdir(parents=True,exist_ok=True)
    atomic_json(output/'collection-plan.json',dict(schema_version=1,items=items,controls=cfg['controls']))
    result=dict(config_sha256=sha256(config),missing=missing,complete=not missing,files=len(items),production_admitted=False)
    if not missing:
        plan=dict(base,intervals=intervals)
        for role in ['wel','ghb']:
            if plan[role+'_provenance']!=cfg['sources'][role]['provenance']:raise ValueError('provenance mismatch')
        # Controls are validated before publishing an executable plan.
        for key in ['grid','membership','model_activity_mask','signs_evidence','units_evidence','time_evidence','package_coverage_evidence']:bound(plan[key])
        atomic_json(output/'processing-plan.json',plan)
    else:
        stale=output/'processing-plan.json'
        if stale.exists():stale.unlink()
    atomic_json(output/'binding-report.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=bind(a.config,a.output);print(json.dumps(r));raise SystemExit(0 if r['complete'] else 2)
