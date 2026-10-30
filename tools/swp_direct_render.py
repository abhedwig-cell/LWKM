"""Render SWP from direct HRU-derived parameters and standalone lookup catalog."""
import argparse
from collections import defaultdict
from datetime import date
import gzip
import hashlib
import json
from pathlib import Path
from tools.modern_swp import render
from tools.swp_hru_authority import rows
from tools.swp_local_assets import local_assets, source_assets

HYDRAULIC=('ORES','OSAT','ALFA','NPAR','KSATFIT','LEXP','H_ENPR','KSATEXM','BDENS','ELAS')
TEXTURE=('PSAND','PSILT','PCLAY','ORGMAT')


def quote(value):
    return "'"+str(value).strip("'").replace("'","''")+"'"


class Catalog:
    def __init__(self, path):
        with gzip.open(path,'rt') as f:self.data=json.load(f)
        if set(self.data['tables']) != {'discretisatie','DZNEW','eigenschappen','Gewasrotatie','Gewasweerstand'}:
            raise ValueError('unexpected catalog tables')
        self.index={}
        keys={'discretisatie':('bodem_id','dikte_id'),'DZNEW':('dikte_id',),
              'eigenschappen':('bodem_id',),'Gewasrotatie':('climate_id','crop_id','rotation_id'),
              'Gewasweerstand':('crop_id',)}
        for table,fields in keys.items():
            index=defaultdict(list)
            for row in self.data['tables'][table]:
                index[tuple(str(row[k]) for k in fields)].append(row)
            self.index[table]=index

    def get(self, table, *key):
        result=self.index[table].get(tuple(str(k) for k in key))
        if not result:raise ValueError(f'missing {table} lookup {key}')
        return result

    def context(self, run):
        integer=lambda k:int(run[k])
        bottom=integer('SWBOTB')
        if bottom not in (2,5):raise ValueError(f'unsupported template bottom option {bottom}')
        if integer('SWINCO')!=2:raise ValueError('direct renderer requires SWINCO=2')
        start,end=date.fromisoformat(run['TSTART']),date.fromisoformat(run['TEND'])
        if end<start:raise ValueError('end before start')
        profile=sorted(self.get('discretisatie',integer('bodem_id'),integer('dikte_id')),key=lambda r:r['ISUBLAY'])
        props=sorted(self.get('eigenschappen',integer('bodem_id')),key=lambda r:r['ISOILLAY'])
        dz=sorted(self.get('DZNEW',integer('dikte_id')),key=lambda r:r['ICOMP'])
        if len(dz)!=integer('NUMNODNEW') or abs(sum(float(r['HSUBLAY']) for r in profile)-sum(float(r['DZNEW']) for r in dz))>1e-6:
            raise ValueError('inconsistent soil discretization node counts')
        if {r['ISOILLAY'] for r in props}!={r['ISOILLAY'] for r in profile}:
            raise ValueError('inconsistent hydraulic/profile layers')
        rotations=[]
        selected=self.get('Gewasrotatie',run['climate_id'],integer('crop_id'),run['rotation_id'])
        for r in sorted(selected,key=lambda r:r['CROPSTART']):
            a,b=date.fromisoformat(r['CROPSTART']),date.fromisoformat(r['CROPEND'])
            if b<a:raise ValueError('reversed crop dates')
            if b<start or a>end:continue
            rotations.append(dict(CROPSTART=a.isoformat(),CROPEND=b.isoformat(),
                                  CROPNAME=quote(r['CROPNAME']),CROPFIL=quote(r['CROPFIL']),CROPTYPE=int(r['CROPTYPE'])))
        # Crop-free seasons are allowed, missing whole years are not.
        for year in range(start.year,end.year+1):
            if not any(int(r['CROPSTART'][:4])<=year<=int(r['CROPEND'][:4]) for r in rotations):
                raise ValueError(f'missing rotation year {year}')
        for previous,current in zip(rotations,rotations[1:]):
            if current['CROPSTART']<=previous['CROPEND']:raise ValueError('overlapping crop intervals')
        resistance=self.get('Gewasweerstand',integer('crop_id'))
        if len(resistance)!=1:raise ValueError('ambiguous crop resistance')
        context={k:run[k] for k in ('TSTART','TEND','NUMNODNEW','SWETR','GWLI','PONDMX','RSRO','RDS','SWINCO','SWBBCFILE','SWBOTB')}
        for k in ('NUMNODNEW','SWETR','SWINCO','SWBBCFILE','SWBOTB'):context[k]=int(context[k])
        context.update(run_id=integer('run_id'),run=run,DZNEW=' '.join(str(r['DZNEW']) for r in dz),
                       METFIL=quote(run['METFIL']),DRFIL=quote(run['DRFIL']),BBCFIL=quote(run['BBCFIL']),
                       RSOIL=resistance[0]['RSOIL'],TABLE_CROPROTATION=rotations,
                       TABLE_SOILPROFILE=[{k:r[k] for k in ('ISUBLAY','ISOILLAY','HSUBLAY','NCOMP')} for r in profile],
                       TABLE_SOILHYDRFUNC=[{k:r[k] for k in HYDRAULIC} for r in props],
                       TABLE_SOILTEXTURES=[{k:r[k] for k in TEXTURE} for r in props],
                       SWDRA=1,SWITCH_SWDRA_OPTION_1=True,SWITCH_SWINCO_OPTION_2=True,
                       SWITCH_SWINCO_OPTION_3=False,SWITCH_SWBOTB_OPTION_2=bottom==2,
                       SWITCH_SWBOTB_OPTION_5=bottom==5,issues=[],diagnostics=[],renderable=True)
        return context


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('parameters','catalog','template','output'):p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--expected-hrus',type=int,default=10242)
    a=p.parse_args(argv);catalog=Catalog(a.catalog);template=a.template.read_bytes()
    parameters=list(rows(a.parameters));ids=[int(r['run_id']) for r in parameters]
    if len(set(ids))!=len(ids) or len(ids)!=a.expected_hrus:raise ValueError('parameter population mismatch')
    a.output.mkdir(parents=True,exist_ok=True)
    asset_sources=source_assets()
    outcomes=[]
    for run in parameters:
        target=a.output/str(int(run['run_id']))/(str(int(run['run_id']))+'.swp')
        try:
            context=catalog.context(run)
            assets=local_assets(run,context)
            content=render(template,context).encode()
            assets[target.name]=content
            target.parent.mkdir(parents=True,exist_ok=True)
            digest=hashlib.sha256(content).hexdigest()
            reused=all((target.parent/name).is_file() and (target.parent/name).read_bytes()==data for name,data in assets.items())
            if not reused:
                for name,data in assets.items():
                    dest=target.parent/name
                    temp=dest.with_suffix(dest.suffix+'.tmp');temp.write_bytes(data);temp.replace(dest)
            outcomes.append(dict(HRU=int(run['run_id']),status='REUSED' if reused else 'WRITTEN',sha256=digest,
                                 irrigation_id=int(run['irrigation_id']),irrigation_management_connected=True,
                                 directory=str(int(run['run_id'])),
                                 assets={name:hashlib.sha256(data).hexdigest() for name,data in assets.items()}))
        except (ValueError,KeyError,TypeError,OSError) as exc:
            target.unlink(missing_ok=True)
            outcomes.append(dict(HRU=int(run['run_id']),status='FAILED',error=str(exc)))
        if len(outcomes)%1000==0:print(f'SWP {len(outcomes)}/{len(parameters)}',flush=True)
    failed=sum(r['status']=='FAILED' for r in outcomes)
    manifest=dict(status='FAILED' if failed else 'SWP_RENDERED_NOT_SWAP_VALIDATED',failed_hrus=failed,
                  asset_sources=asset_sources,
                  sources={k:hashlib.sha256(getattr(a,k).read_bytes()).hexdigest() for k in ('parameters','catalog','template')},hrus=outcomes)
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(status=manifest['status'],hrus=len(outcomes),failed_hrus=failed)))
    return bool(failed)


if __name__=='__main__':raise SystemExit(main())
