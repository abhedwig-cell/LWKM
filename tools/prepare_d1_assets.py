"""Bind existing Work B contexts to original crop templates and C2 drainage.

Only the already qualified constant grass CF projection is reused. Other
missing crop factors remain explicit blockers. Nature SCHEDULE is always zero.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zipfile
import openpyxl
import pandas as pd
from tools.assemble_swap_package import sha256
from tools.swp_renderer import render_text
from tools.work_c_crop_factor import project
from tools.p12_landuse_flags import landuse_flags
from tools.package_preflight import scalar
from tools.run_dra_protected_population import atomic_json

def records(sheet):
    it=iter(sheet.values);header=next(it)
    return [dict(zip(header,row)) for row in it if row[0] is not None]

def prepare(workbook,templates,contexts,representatives,svats,output):
    output.mkdir(parents=True,exist_ok=True)
    w=openpyxl.load_workbook(workbook,read_only=True,data_only=True)
    irrigation={(r['irrigation_id'],r['solute_id']):r for r in records(w['Irrigatie'])}
    meteo={r['climate_id']:r for r in records(w['Meteo'])}
    reps=pd.read_csv(representatives).set_index('HRU')
    attrs=pd.read_csv(svats,usecols=['svat','landgebruik22']).set_index('svat')
    sources={str(p):sha256(p) for p in [workbook,templates,contexts,representatives,svats]}
    runs={};errors=[];nature_overrides=[];cache={}
    with zipfile.ZipFile(templates) as z,gzip.open(contexts,'rt') as f:
        for line in f:
            row=json.loads(line);hid=row['run_id'];ctx=row['context'];r=ctx['run']
            try:
                rep=int(reps.loc[hid,'hru_representative_svat']);landuse=int(attrs.loc[rep,'landgebruik22'])
                nature=landuse_flags(landuse).is_nature
                irr=irrigation[r['irrigation_id'],r['solute_id']];schedule=int(irr['SCHEDULE'])
                if nature and schedule:nature_overrides.append(hid)
                if nature:schedule=0
                atmo=meteo[r['climate_id']]['ATMOFIL'];assets={}
                for crop in sorted({x['CROPFIL'].strip("'") for x in ctx['TABLE_CROPROTATION']}):
                    need_cf=ctx['SWETR']==1 and not any(x['CROPNAME'].strip("'").lower()=='tulp' for x in ctx['TABLE_CROPROTATION'])
                    key=(crop,schedule,atmo,need_cf)
                    if key not in cache:
                        raw=z.read('Template/Gewas/'+crop+'.crp')
                        try:text=raw.decode('utf-8-sig')
                        except UnicodeDecodeError:text=raw.decode('cp1252')
                        rendered=render_text(text,dict(SCHEDULE=schedule,SWITCH_SCHEDULE_OPTION_1=schedule==1,ATMOFIL="'"+atmo+"'"))
                        projection=None
                        if need_cf and int(scalar(rendered,'SWCF'))!=1:
                            if crop!='gras_beweiding':raise ValueError('UNQUALIFIED_CROP_FACTOR: '+crop)
                            rendered,projection=project(rendered,z.read('Template/Gewas/3.0.0/'+crop+'.crp').decode('cp1252'))
                        if nature and int(scalar(rendered,'SCHEDULE',0))!=0:raise ValueError('nature irrigation active')
                        data=rendered.encode();digest=hashlib.sha256(data).hexdigest();p=output/'objects'/digest/(crop+'.crp');p.parent.mkdir(parents=True,exist_ok=True)
                        if not p.exists():p.write_bytes(data)
                        if sha256(p)!=digest:raise ValueError('cached crop asset corrupt')
                        cache[key]={'path':str(p.resolve()),'sha256':digest,'logical_id':'D1_CROP_'+digest,'qualification_status':'RESEARCH_CANDIDATE',
                                    'semantic_contract':'SOURCE_TEMPLATE_WORKBOOK_JOIN; OWNER_NATURE_NO_IRRIGATION; CONSTANT_GRASS_CF_ONLY',
                                    'evidence_refs':['docs/production/WORK_C2_20261019.md'],'projection':projection}
                    assets[crop+'.crp']=cache[key]
                    crop_text=Path(cache[key]['path']).read_text()
                    if int(scalar(crop_text,'SWCO2',0))==1 and int(scalar(crop_text,'SWATMOFIL',0))==1:
                        data=z.read('Template/Meteo/'+atmo+'.co2');digest=hashlib.sha256(data).hexdigest();p=output/'objects'/digest/(atmo+'.co2');p.parent.mkdir(parents=True,exist_ok=True)
                        if not p.exists():p.write_bytes(data)
                        if sha256(p)!=digest:raise ValueError('cached atmosphere asset corrupt')
                        assets[atmo+'.co2']={'path':str(p.resolve()),'sha256':digest}
                runs[str(hid)]=dict(assets=assets,is_nature=nature,representative_svat=rep,landuse22=landuse,schedule=schedule)
            except (ValueError,KeyError) as e:errors.append(dict(hru_id=hid,error=str(e)))
    result=dict(schema_version=1,runs=runs,input_sha256=sources,errors=errors,nature_irrigation_overrides=nature_overrides,
                production_admitted=False,code_sha256=sha256(Path(__file__)))
    atomic_json(output/'catalogue.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['workbook','templates','contexts','representatives','svats','output']:p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();r=prepare(*(getattr(a,n) for n in ['workbook','templates','contexts','representatives','svats','output']));print(json.dumps(dict(bound=len(r['runs']),errors=r['errors'],nature_overrides=len(r['nature_irrigation_overrides']))))
