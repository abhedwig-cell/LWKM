"""Export qualified Work C2 drainage checkpoints for the offline NHI DRA serializer.

Upstream source authority and automatic five-level selection remain Python.
Never fabricate lost monthly H1 levels or overwrite existing C2 evidence.
"""
import argparse,json
from pathlib import Path
from tools.w07_build_29_dra import from_record
from tools.w07_autofive_full_records import solve
from tools.dra_level_compression import to_render_level
from tools.swp_full_oracle import parse_named_table
from tools.swp_template_adapter import TABLE_HEADERS
from tools.run_dra_protected_population import atomic_json

def export(checkpoints,swps,output,start_year=1971,end_year=1972):
    hrus=[];errors=[]
    for p in sorted((Path(checkpoints)/'hrus').glob('*.json'),key=lambda p:int(p.stem)):
        row=json.loads(p.read_text());hid=int(row['hru'])
        try:
            if row['status']=='DRA_INTERFACE_CANDIDATE':
                levels=row['levels']
            elif row['status']=='BLOCKED' and row.get('retained_physical'):
                levels=[to_render_level(s) for s in solve([from_record(x) for x in row['retained_physical']])[0]]
            else:raise ValueError('unresolved checkpoint source: '+row['status'])
            swp=Path(swps)/f'run_{hid:05d}'/'swap.swp'
            n=len(parse_named_table(swp.read_text(),TABLE_HEADERS['TABLE_SOILHYDRFUNC']))
            if not 1<=len(levels)<=5:raise ValueError('no active DRA levels')
            hrus.append(dict(hru=hid,n_horizons=n,levels=levels))
        except (ValueError,KeyError,TypeError,FileNotFoundError) as e:
            errors.append(dict(hru=hid,error=str(e)))
    payload=dict(schema_version=1,start_year=start_year,end_year=end_year,
                 status='RENDERER_INPUT_NOT_PRODUCTION_ADMITTED',hrus=hrus,errors=errors)
    atomic_json(Path(output),payload)
    return payload

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for n in ('checkpoints','swps','output'):ap.add_argument('--'+n,required=True,type=Path)
    a=ap.parse_args()
    p=export(a.checkpoints,a.swps,a.output)
    print(json.dumps(dict(renderer_ready=len(p['hrus']),errors=len(p['errors']))))
    raise SystemExit(1 if p['errors'] else 0)
