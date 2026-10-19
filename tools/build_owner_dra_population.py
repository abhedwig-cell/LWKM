"""Serialize all owner-rule DRA candidates; only changed bytes are rewritten."""
import argparse,json,time
from pathlib import Path
from tools.generate_dra import render_dra_explicit
from tools.swp_full_oracle import parse_named_table
from tools.swp_template_adapter import TABLE_HEADERS
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def build(drainage,swps,output):
    output.mkdir(parents=True,exist_ok=True);rows=[];begin=time.monotonic()
    for p in sorted((drainage/'hrus').glob('*.json'),key=lambda p:int(p.stem)):
        r=json.loads(p.read_text());hid=r['hru'];row=dict(hru=hid,status=r['status'],production_admitted=False)
        if r['status']=='DRA_INTERFACE_CANDIDATE':
            swp=swps/f'run_{hid:05d}'/'swap.swp'
            n=len(parse_named_table(swp.read_text(),TABLE_HEADERS['TABLE_SOILHYDRFUNC']))
            if not r['levels']:row.update(status='SWDRA_ZERO_NO_ACTIVE_SYSTEMS')
            else:
                text=render_dra_explicit(r['levels'],n,1971,1972,0.)
                target=output/f'{hid}.dra';data=text.encode();reuse=target.exists() and target.read_bytes()==data
                if not reuse:
                    tmp=target.with_suffix('.partial');tmp.write_bytes(data);tmp.replace(target)
                row.update(status='DRA_SERIALIZED_CANDIDATE',sha256=sha256(target),reused=reuse,
                    checkpoint_sha256=sha256(p),path=str(target.resolve()))
        else:row['error']=r['error']
        rows.append(row)
    summary=dict(population=len(rows),serialized=sum(r['status']=='DRA_SERIALIZED_CANDIDATE' for r in rows),
        reused=sum(r.get('reused',False) for r in rows),elapsed_seconds=time.monotonic()-begin,
        production_admitted=False,runs=rows)
    atomic_json(output/'build-status.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='runs'}));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['drainage','swps','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.drainage,a.swps,a.output)
