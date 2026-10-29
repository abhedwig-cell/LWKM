"""Read existing NHI source locations, using run provenance already available.

No source data is moved, no model is executed and no source is auto-admitted.
Only small run controls are read; referenced grids receive metadata checks.
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile
from tools.lhm_run_chain_provenance import parse

RUNS=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
MODEL=Path(r'E:\LHM_4.3.3')
ROLES={'maaiveld_asc':'ground_surface','uopp_asc':'svat_area','lgn_asc':'source_landuse',
       'bodem_asc':'source_soil','rootzone_asc':'root_depth','metestat_asc':'meteo_region',
       'shd_l1':'initial_head_model_setup','ib_l1':'layer1_activity',
       'drn_cond_b':'pipe_drain_conductance','drn_stage_b':'pipe_drain_level'}
EXTENSIONS=('.asc','.idf','.inp','.csv','.run','.prj','.ini')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_metadata(raw):
    # Windows paths must never be accidentally interpreted relative to Linux cwd.
    if os.name!='nt' and (re.match(r'^[a-z]:',raw,re.I) or raw.startswith('\\\\')):
        return dict(path=raw,status='WINDOWS_PATH_NOT_CHECKED_ON_THIS_HOST')
    p=Path(raw)
    try:
        s=p.stat()
        return dict(path=str(p),status='FILE_EXISTS' if p.is_file() else 'DIRECTORY_EXISTS',
                    bytes=s.st_size,mtime_ns=s.st_mtime_ns)
    except FileNotFoundError:return dict(path=str(p),status='MISSING')
    except OSError as exc:return dict(path=str(p),status='ACCESS_ERROR',error=str(exc))


def read_references(control, provenance):
    result=[]
    control_digest=digest(control)
    for v in parse(control):
        if v.key.startswith('%'):continue
        raw=(v.resolved or v.raw).strip().strip('\"\'')
        if not any(raw.lower().endswith(e) for e in EXTENSIONS) and not any(t in raw for t in ('*','?')):
            continue
        record=dict(control=str(control),control_sha256=control_digest,provenance=provenance,
                    line=v.line,key=v.key,raw=v.raw,resolved=v.resolved,
                    role=ROLES.get(v.key.lower(),'OTHER_CONFIGURED_DEPENDENCY'))
        if v.resolved is None or '%(' in raw or '${' in raw:
            record.update(status='UNRESOLVED_ALIAS',locations=[])
        elif any(c in raw for c in ('*','?','[')):
            record.update(status='CONFIGURED_PATTERN_NOT_EXPANDED',locations=[])
        elif re.match(r'^[a-z]:[\\/]',raw,re.I) or raw.startswith('\\\\') or Path(raw).is_absolute():
            record.update(status='ABSOLUTE_CONFIGURED_REFERENCE',locations=[path_metadata(raw)])
        else:
            # An existing file alone cannot prove the original process cwd.
            candidate=(control.parent/Path(raw.replace('\\','/'))).resolve()
            record.update(status='RELATIVE_REFERENCE_REQUIRES_RUN_CONTEXT',locations=[path_metadata(str(candidate))])
        record['units_hint']='cm_from_filename_UNVERIFIED' if '_cm.' in raw.lower() else 'NOT_ESTABLISHED'
        result.append(record)
    return result


def discover_controls(runs, model):
    directories=[runs,model,model/'nhi_py']
    warnings=[]
    if runs.is_dir():
        for p in sorted(runs.iterdir()):
            if p.is_dir() and p.name.lower().startswith(('run_','control_run_')):
                directories.extend((p,p/'nhi_py',p/'config',p/'control'))
    controls=[];launchers=[]
    for directory in directories:
        if not directory.is_dir():continue
        try:
            for p in sorted(directory.iterdir()):
                if not p.is_file():continue
                if p.name.lower().startswith('control_run_') and p.suffix.lower()=='.ini':controls.append(p)
                elif p.suffix.lower() in ('.run','.prj','.cmd','.bat'):
                    launchers.append(dict(path=str(p),bytes=p.stat().st_size))
        except OSError as exc:warnings.append(dict(path=str(directory),error=str(exc)))
    return sorted(set(controls)),launchers,warnings


def inventory(runs,model,prior,output):
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    controls,launchers,warnings=discover_controls(runs,model)
    for root in (runs,model):
        if not root.is_dir():warnings.append(dict(path=str(root),error='known server root not found'))
    if not controls:warnings.append(dict(error='no current server control INI found in bounded scan'))
    provenance_path=prior/'provenance.json'
    prior_metadata=json.loads(provenance_path.read_text()) if provenance_path.exists() else None
    references=[];control_records=[]
    for provenance,paths in [('CURRENT_SERVER_RUN_CONFIG',controls),
                             ('PREVIOUSLY_UPLOADED_RUN_CONFIG',sorted(prior.glob('*.ini')))]:
        for control in paths:
            if control.stat().st_size>4*1024*1024:
                warnings.append(dict(path=str(control),error='control exceeds 4 MiB read limit'));continue
            refs=read_references(control,provenance)
            references.extend(refs)
            control_records.append(dict(path=str(control),sha256=digest(control),provenance=provenance,
                                        references=len(refs)))
    by_key=defaultdict(list)
    for r in references:by_key[r['key'].lower()].append(r)
    comparison={k:dict(configured_values=sorted({r['resolved'] or r['raw'] for r in values}),
                       controls=len({r['control'] for r in values})) for k,values in by_key.items()}
    known=[]
    # Earlier server topology and output inventory, not guessed local BasicData.
    for rel in ('LWKM_run_resultaten_totaal/modflow/head','LWKM_run_resultaten_totaal/metaswap'):
        known.append(path_metadata(str(runs/rel)))
    for year in (1970,1980,1990,2000,2010,2020):
        for suffix in ('_l1.idf','000000_l1.idf'):
            known.append(path_metadata(str(runs/'LWKM_run_resultaten_totaal/modflow/head'/f'head_{year}0101{suffix}')))
    roles={role:dict(configured_references=sum(r['role']==role for r in references),
                     existing_files=sorted({x['path'] for r in references if r['role']==role
                                            for x in r['locations'] if x['status']=='FILE_EXISTS'}))
           for role in sorted(set(ROLES.values()))}
    report=dict(schema_version=1,status='SOURCE_LOCATION_INVENTORY_NOT_PRODUCTION_BINDING',
                created_utc=datetime.now(timezone.utc).isoformat(),runs_root=str(runs),model_root=str(model),
                scan_scope='Known run roots and direct config subdirectories only; no recursive grid/output scan',
                controls=control_records,prior_controls_metadata=prior_metadata,references=references,key_comparison=comparison,
                role_summary=roles,known_output_locations=known,launch_configuration_candidates=launchers,
                warnings=warnings,limitations=[
                    'File existence does not prove historical byte identity or scientific equivalence.',
                    'Relative references and alternative/overlapping periods are not auto-selected.',
                    'Grid units, geometry, full time coverage and the remaining SWP source roles still require binding.',
                    'Run/prj and launcher files are listed as candidates; their content is not parsed in this inventory.'])
    (output/'source_inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    with (output/'source_references.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['provenance','control','line','key','role','raw','resolved','status','units_hint']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(references)
    summary=['LWKM SWP bronlocaties','',f'Actuele runconfiguraties gevonden: {len(controls)}',
             f'Eerder aangeleverde configuraties: {len(control_records)-len(controls)}',
             f'Bronverwijzingen: {len(references)}','',
             'Dit is een inventarisatie, geen vrijgave voor productie.','']
    for role,r in roles.items():summary.append(f'{role}: {r["configured_references"]} verwijzingen, {len(r["existing_files"])} bestaande bestanden')
    summary += ['', 'Geen grids gekopieerd of gewijzigd. Geen SWAP- of MODFLOW-run gestart.']
    (output/'LEESMIJ.txt').write_text('\n'.join(summary)+'\n')
    archive=output.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ('source_inventory.json','source_references.csv','LEESMIJ.txt'):z.write(output/name,name)
    return report,archive


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs-root',type=Path,default=RUNS)
    p.add_argument('--model-root',type=Path,default=MODEL)
    p.add_argument('--prior-controls',type=Path,default=Path(__file__).resolve().parents[2]/'source_data/prior_run_controls')
    p.add_argument('--output',type=Path,default=Path('swp_broninventarisatie'))
    a=p.parse_args()
    report,archive=inventory(a.runs_root,a.model_root,a.prior_controls,a.output)
    print(f'GEREED: {archive}\nBronverwijzingen: {len(report["references"])}; waarschuwingen: {len(report["warnings"])}')
    return 0


if __name__=='__main__':raise SystemExit(main())
