"""Bind existing offline raster families to the MET consumer, without copying."""
import argparse
import json
from pathlib import Path
import math
import pandas as pd
from tools.met_grid_consumer import UNITS,geometry
from tools.hru_grid_weights import header
from tools.process_daily_budget_plan import bound
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json

def bind(spec,output):
    cfg=json.loads(spec.read_text());output.parent.mkdir(parents=True,exist_ok=True)
    output.unlink(missing_ok=True)
    if set(cfg['sources'])!=set(UNITS):raise ValueError('incomplete meteorological source families')
    bound(cfg['members']);g=header(bound(cfg['template']));geometry(g)
    transforms={}
    for k,source in cfg['sources'].items():
        if source.get('confirmed') is not True or not source.get('input_unit') or not source.get('evidence'):
            raise ValueError('unconfirmed meteorological source units/semantics: '+k)
        if source.get('output_unit')!=UNITS[k]:raise ValueError('consumer units mismatch: '+k)
        scale,offset=float(source['scale']),float(source['offset'])
        if not math.isfinite(scale) or not math.isfinite(offset) or scale<=0:raise ValueError('invalid explicit conversion')
        pattern=source['pattern']
        if '{date}' not in pattern or Path(pattern).is_absolute() or '..' in Path(pattern).parts:raise ValueError('relative date pattern required')
        transforms[k]=dict(scale=scale,offset=offset,input_unit=source['input_unit'],evidence=source['evidence'])
    plan={k:cfg[k] for k in ['dataset_id','members','start','end','expected_members','expected_hrus']}
    plan.update(geometry=g,units=UNITS,transforms=transforms,spec_sha256=sha256(spec),days={})
    stamps=pd.date_range(cfg['start'],cfg['end'])
    if not len(stamps):raise ValueError('empty daily period')
    for stamp in stamps:
        day=stamp.strftime('%Y-%m-%d');plan['days'][day]={}
        for k,source in cfg['sources'].items():
            files=sorted(p for p in Path(source['directory']).glob(source['pattern'].format(date=stamp.strftime('%Y%m%d'))) if p.is_file())
            if len(files)!=1:raise ValueError(f'{day} {k}: expected one raster, found {len(files)}')
            p=files[0];plan['days'][day][k]=dict(path=str(p.resolve()),sha256=sha256(p))
    atomic_json(output,plan);return plan

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--spec',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();bind(a.spec,a.output)
