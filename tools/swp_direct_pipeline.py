"""One CMD entry point: inventory, original source reduction, direct SWP rendering."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from tools.swp_hru_authority import rows, unique, number
from tools.swp_run_parameters import read_control

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control',required=True,type=Path)
    p.add_argument('--base',required=True,type=Path)
    p.add_argument('--hru',required=True,type=Path)
    p.add_argument('--members',required=True,type=Path)
    p.add_argument('--representatives',type=Path)
    p.add_argument('--head',type=Path)
    p.add_argument('--start');p.add_argument('--end')
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--inventory-only',action='store_true')
    p.add_argument('--root-from-grid',action='store_true')
    p.add_argument('--expected-hrus',default=10242,type=int)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    control,paths=read_control(a.control,a.base)
    start=a.start or datetime.strptime(control['timstart'],'%Y%m%d').date().isoformat()
    end=a.end or datetime.strptime(control['timend'],'%Y%m%d').date().isoformat()
    stamp=start.replace('-','')
    head_candidates=[]
    if a.head:head_candidates=[a.head]
    elif 'dirfileshead' in control:
        base=a.base/control['dirfileshead'].replace('\\','/')
        head_candidates=[base/('head_'+stamp+tail) for tail in ('_l1.idf','000000_l1.idf')]
    available=[x for x in head_candidates if x.is_file()]
    if len(available)>1:raise ValueError('multiple exact-date heads; specify --head')
    if available:paths['head']=str(available[0])
    required=['glk','area','dqsat','lgn','bfe','irr_switch','meteo','bbc','head']
    if a.root_from_grid:required.append('rds')
    inventory={k:dict(path=paths.get(k),exists=bool(paths.get(k) and Path(paths[k]).is_file())) for k in required}
    inventory.update({k:dict(path=str(getattr(a,k)),exists=getattr(a,k).is_file()) for k in ('hru','members')})
    if a.representatives:
        inventory['representatives']=dict(path=str(a.representatives),exists=a.representatives.is_file())
    report=dict(start=start,end=end,head_candidates=[str(x) for x in head_candidates],files=inventory,
                missing=[k for k,r in inventory.items() if not r['exists']],
                status='INPUT_INVENTORY_ONLY')
    (a.output/'source_inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    if a.inventory_only:return 0
    if report['missing']:return 1
    hrus=unique(rows(a.hru),lambda r:number(r,'HRU','hru'))
    if a.representatives:
        representatives=unique(rows(a.representatives),lambda r:number(r,'HRU','hru'))
        if set(representatives)!=set(hrus):raise ValueError('representative population mismatch')
        for hid,h in hrus.items():
            r=representatives[hid]
            if number(h,'svat_repr','hru_representative_svat')!=number(r,'svat_repr'):
                raise ValueError(f'HRU {hid}: representative conflict')
            if number(h,'bodem370','bodem_repr')!=number(r,'bodem_repr','bodem370'):
                raise ValueError(f'HRU {hid}: soil conflict')
            root=number(r,'rz_repr')
            if h.get('rz_repr','')!='' and int(h['rz_repr'])!=root:raise ValueError('root conflict')
            h['rz_repr']=str(root)
    joined=a.output/'hru_source_join.csv'
    fields=sorted({k for h in hrus.values() for k in h})
    with joined.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(hrus.values())
    config=dict(start=start,end=end,climate_id='__',head_file=paths['head'],
                MaxPondDepth=float(control['maxponddepth']),crunoff_par=float(control['crunoff_par']),
                tempCbotk=float(control['tempcbotk']))
    if a.root_from_grid:config['root_policy']='representative_grid'
    cfg=a.output/'source_config.json';cfg.write_text(json.dumps(config,indent=2)+'\n')
    command=[sys.executable,'-m','tools.swp_run_parameters','--hru',str(joined.resolve()),
             '--members',str(a.members.resolve()),'--soil',str(ROOT/'config/swp/soil_classification_and_profile.csv'),
             '--crop',str(ROOT/'config/swp/four_landuse_crop_candidate.csv'),
             '--config',str(cfg.resolve()),'--control',str(a.control.resolve()),'--base',str(a.base.resolve()),
             '--output',str((a.output/'parameters').resolve()),'--expected-hrus',str(a.expected_hrus)]
    subprocess.run(command,cwd=ROOT,check=True)
    subprocess.run([sys.executable,'-m','tools.swp_direct_render',
                    '--parameters',str((a.output/'parameters/runs_candidate.csv').resolve()),
                    '--catalog',str(ROOT/'config/swp/lookup_catalog.json.gz'),
                    '--template',str(ROOT/'tests/fixtures/d1/wwl.swp'),
                    '--output',str((a.output/'swp').resolve()),'--expected-hrus',str(a.expected_hrus)],cwd=ROOT,check=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
