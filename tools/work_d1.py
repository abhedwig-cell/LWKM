"""One restartable reception -> MET/BBC -> immutable SWAP package workflow.

Local orchestration consumes compact server products, not national rasters.
All outputs remain explicit research candidates until independent admission.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import shutil
import pandas as pd
from tools.production_transfer import receive, KINDS
from tools.process_daily_budget_plan import bound
from tools.daily_forcing import effective_bbc,modern_met
from tools.run_dra_protected_population import atomic_json,canonical
from tools.assemble_swap_package import assemble,sha256
from tools.modern_swp import render
from tools.package_preflight import validate,scalar

def index_daily(accepted,database):
    """Read changed daily shards only. SQLite bounds memory by one day/HRU."""
    with sqlite3.connect(database) as c:
        c.execute('create table if not exists shard (kind text, day text, digest text, primary key(kind,day))')
        c.execute('create table if not exists daily (kind text, hru integer, day text, record text, primary key(kind,hru,day))')
        loaded=0
        for meta in accepted:
            kind=meta['product_kind']
            days={r['date'] for r in meta['files']}
            for (day,) in c.execute('select day from shard where kind=?',(kind,)).fetchall():
                if day not in days:
                    c.execute('delete from daily where kind=? and day=?',(kind,day));c.execute('delete from shard where kind=? and day=?',(kind,day))
            for f in meta['files']:
                p=bound(f);old=c.execute('select digest from shard where kind=? and day=?',(kind,f['date'])).fetchone()
                if old and old[0]==f['sha256']:continue
                data=pd.read_csv(p)
                c.execute('delete from daily where kind=? and day=?',(kind,f['date']))
                c.executemany('insert into daily values (?,?,?,?)',[(kind,int(r['hru_id']),f['date'],json.dumps(r,allow_nan=False)) for r in data.to_dict('records')])
                c.execute('insert or replace into shard values (?,?,?)',(kind,f['date'],f['sha256']));loaded+=1
        c.commit()
    return loaded

def forcing(accepted,database,output):
    met,gw=accepted
    if met['product_kind']!='MET' or gw['product_kind']!='BBC':raise ValueError('MET and BBC input roles required')
    for key in ['start','end','hru_ids']:
        if met[key]!=gw[key]:raise ValueError('MET/BBC identity or coverage differs: '+key)
    output.mkdir(parents=True,exist_ok=True)
    loaded=index_daily(accepted,database);rows=[]
    with sqlite3.connect(database) as c:
        for hid in met['hru_ids']:
            frames={kind:pd.DataFrame([json.loads(x[0]) for x in c.execute('select record from daily where kind=? and hru=? order by day',(kind,hid))]) for kind in ['MET','BBC']}
            texts={'met':modern_met(frames['MET'],start=met['start'],end=met['end'],station=hid),
                   'bbc':effective_bbc(frames['BBC'],start=gw['start'],end=gw['end'])}
            assets={};reused=True
            for ext,text in texts.items():
                p=output/f'{hid}.{ext}';same=p.exists() and p.read_text()==text
                if not same:
                    tmp=p.with_suffix('.partial');tmp.write_text(text);tmp.replace(p)
                assets[p.name]={'path':str(p.resolve()),'sha256':sha256(p),'qualification_id':'D1_SOURCE_BOUND_RESEARCH_CANDIDATE'}
                reused &= same
            rows.append(dict(hru_id=hid,assets=assets,reused=reused))
    report=dict(start=met['start'],end=met['end'],runs=rows,changed_shards_indexed=loaded,production_admitted=False,
                source_manifests=[met['source_manifest_sha256'],gw['source_manifest_sha256']],
                wind_measurement_height_m=10,bbc_policy='OWNER_DAILY_MEAN_NODES_20261020')
    atomic_json(output/'manifest.json',report);return report

def build_packages(contexts,template,dra_bundle,asset_catalogue,pairs,output,*,expected_population=10242):
    """Reuse Work B contexts and exact C2 DRA bytes; no legacy forcing fallback."""
    with gzip.open(contexts,'rt') as f:records=[json.loads(line) for line in f]
    ids=[r['run_id'] for r in records]
    if ids!=list(range(1,expected_population+1)):raise ValueError('Work B population identity mismatch')
    with gzip.open(dra_bundle,'rt') as f:dras={int(r['hru']):r for r in map(json.loads,f)}
    if set(dras)-set(ids):raise ValueError('DRA outside HRU population')
    assets_by_hru=json.loads(asset_catalogue.read_text())['runs']
    inputs={r['hru_id']:r for r in pairs['runs']};rows=[]
    if set(inputs)-set(ids):raise ValueError('forcing outside Work B population')
    for record in records:
        hid=record['run_id'];ctx=record['context'];row=dict(run_id=hid,production_admitted=False)
        try:
            if hid not in dras:raise ValueError('C2_PROTECTED_DRAINAGE_EXCEPTION')
            if hid not in inputs:raise ValueError('INCOMING_FORCING_UNBOUND')
            if str(hid) not in assets_by_hru:raise ValueError('NONFORCING_ASSETS_UNBOUND')
            d=dras[hid]
            if hashlib.sha256(d['text'].encode()).hexdigest()!=d['sha256']:raise ValueError('DRA bundle SHA mismatch')
            with tempfile.TemporaryDirectory(prefix='lwkm-d1-') as td:
                stage=Path(td)
                # No historical MET/BBC/DRA survives this boundary.
                selected={n:m for n,m in assets_by_hru[str(hid)]['assets'].items() if Path(n).suffix.lower() not in ['.swp','.met','.bbc','.dra']}
                for name,meta in selected.items():
                    if Path(name).name!=name or '\\' in name or ':' in name:raise ValueError('unsafe asset name')
                    shutil.copyfile(bound(meta),stage/name)
                for name,meta in inputs[hid]['assets'].items():shutil.copyfile(bound(meta),stage/name)
                (stage/f'{hid}.dra').write_text(d['text'])
                swp=render(template.read_bytes(),ctx,policy={'TSTART':pairs['start'],'TEND':pairs['end'],'ALTW':10.},et_policy='owner_tulip_pm')
                (stage/'swap.swp').write_text(swp)
                # Fixed irrigation is disabled in the source template. Nature
                # auto-irrigation must also be disabled in every active CRP.
                nature=assets_by_hru[str(hid)].get('is_nature')
                if type(nature)!=bool:raise ValueError('explicit representative nature classification required')
                if nature:
                    if int(scalar(swp,'SWIRFIX'))!=0:raise ValueError('nature fixed irrigation forbidden')
                    for crop in stage.glob('*.crp'):
                        if int(scalar(crop.read_text(),'SCHEDULE',0))!=0:
                            raise ValueError('nature automatic irrigation forbidden: '+crop.name)
                if float(scalar(swp,'ALTW'))!=10:raise ValueError('10m wind height mismatch')
                preflight=validate(stage)
                assets={name:dict(path=str(stage/name),sha256=sha256(stage/name),qualification_id='D1_BOUND_RESEARCH_CANDIDATE') for name in preflight['files']}
                identity=dict(hru_id=hid,context=record,inputs={n:m['sha256'] for n,m in assets.items()},
                              is_nature=nature,source_manifests=pairs['source_manifests'],
                              code={n:sha256(Path(__file__).with_name(n)) for n in ['work_d1.py','modern_swp.py','package_preflight.py','assemble_swap_package.py']})
                fingerprint=hashlib.sha256(canonical(identity).encode()).hexdigest()
                target=output/'objects'/fingerprint/f'run_{hid:05d}';reuse=target.exists()
                if reuse:
                    manifest=json.loads((target/'manifest.json').read_text())
                    if {n:m['sha256'] for n,m in manifest['assets'].items()}!=identity['inputs']:raise ValueError('cached package manifest mismatch')
                    if any(sha256(target/n)!=m['sha256'] for n,m in assets.items()):raise ValueError('cached package corrupt')
                    validate(target)
                else:
                    assemble(hid,assets,target.parent,profile_id='LWKM_D1_SOURCE_BOUND_CANDIDATE',code_commit='sha256:'+identity['code']['work_d1.py'],required_assets=preflight['files'],file_keys=('METFIL',))
                    atomic_json(target/'input-bindings.json',identity);atomic_json(target/'preflight.json',preflight)
                row.update(status='COMPLETE_CANDIDATE_PACKAGE',package=str(target.resolve()),fingerprint=fingerprint,reused=reuse)
        except (ValueError,KeyError,OSError) as exc:row.update(status='BLOCKED',error=str(exc))
        rows.append(row)
    report=dict(population=len(records),complete_packages=sum(r['status']=='COMPLETE_CANDIDATE_PACKAGE' for r in rows),
                reused_packages=sum(r.get('reused',False) for r in rows),production_admitted=False,runs=rows)
    atomic_json(output/'build-status.json',report);return report

def run(plan,output):
    cfg=json.loads(plan.read_text())
    if cfg.get('mode')!='RESEARCH_ONLY':raise ValueError('D1 does not grant production admission')
    output.mkdir(parents=True,exist_ok=True);received=[]
    for role in ['met','bbc']:
        meta=cfg[role];manifest=bound(meta['manifest'])
        report=receive(manifest,Path(meta['source']),output/('import-'+role))
        if report['errors']:raise ValueError('incoming '+role+' blocked; see import-report.json')
        received.append(json.loads((output/('import-'+role)/'accepted-manifest.json').read_text()))
    pairs=forcing(received,output/'daily.sqlite',output/'forcing')
    result=build_packages(*(bound(cfg[k]) for k in ['contexts','template','dra_bundle','asset_catalogue']),pairs,output/'packages',expected_population=cfg.get('expected_population',10242))
    if cfg.get('execute'):
        from tools.execute_catalogue_packages import run as execute
        execute(output/'packages/build-status.json',output/'executions',bound(cfg['engine']),Path(cfg['runtime_library']))
    atomic_json(output/'workflow.json',dict(plan_sha256=sha256(plan),production_admitted=False,complete_packages=result['complete_packages'],population=result['population']))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();r=run(a.plan,a.output);print(json.dumps({k:v for k,v in r.items() if k!='runs'}))
