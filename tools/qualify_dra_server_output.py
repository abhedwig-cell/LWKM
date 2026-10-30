"""Independent population checks on serialized DRA and archived C2 physics."""
import argparse
from collections import Counter
from datetime import date,datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
from tools.dra_semantic_oracle import parse_dra
from tools.server.check_swp_source_values import sha


def qualify(output,c2_archive,report):
    manifest=json.loads((output/'production_manifest.json').read_text())
    original={}
    with gzip.open(c2_archive,'rt') as stream:
        for line in stream:
            rec=json.loads(line);original[int(rec['hru'])]=rec
    first,last=date.fromisoformat(manifest['start']),date.fromisoformat(manifest['end'])
    ids={row['hru'] for row in manifest['outcomes']}
    files={int(path.stem):path for path in (output/'dra').glob('*.dra')}
    if ids!=set(files) or ids!=set(original):raise ValueError('DRA/manifest/C2 population mismatch')
    maxima=Counter();changed=Counter();methods=Counter();fingerprints=[]
    decision_counts=Counter();approximate=[]
    for row in manifest['outcomes']:
        hid=row['hru'];path=files[hid]
        if sha(path)!=row['sha256']:raise ValueError(f'output hash mismatch {hid}')
        with gzip.open(output/'hrus'/f'{hid}.json.gz','rt') as stream:rec=json.load(stream)
        methods[rec['status']]+=1
        parsed=parse_dra(path.read_text());glob=parsed['global'];n=int(glob['NRLEVS'])
        if not 1<=n<=5:raise ValueError(f'invalid NRLEVS {hid}')
        if len(str(glob['COFANI']).split())!=row['soil_horizons']:
            raise ValueError(f'COFANI/horizon count mismatch {hid}')
        for i in range(1,n+1):
            level=parsed['systems'][str(i)]
            if not 1<=level['DRARES']<=100000 or not 0<=level['INFRES']<=100000:
                raise ValueError(f'resistance outside parser range {hid}')
            dates=[datetime.strptime(day,'%d-%b-%Y').date() for day in level['LEVEL']]
            if dates!=sorted(set(dates)) or dates[0]>first or dates[-1]<last:
                raise ValueError(f'level time coverage failure {hid}')
            if level['L']!=rec['dqsat']['candidate_spacing_m']:
                raise ValueError(f'dqsat/spacing mismatch {hid}')
        old={tuple(s['source_ids']):s for s in original[hid]['physical']}
        for current in rec['physical']:
            previous=old[tuple(current['source_ids'])]
            for field in ('drnres','infres','dep','peil_sum','peil_win','dd',
                          'drainage_conductance_raw','infiltration_conductance_raw'):
                delta=abs(current[field]-previous[field]);maxima[field]=max(maxima[field],delta)
                if delta>1e-9*max(1.,abs(previous[field])):changed[field]+=1
        for event in rec['owner_decision']['events']:decision_counts[event['action']]+=1
        if rec['status']=='AUTO_APPROXIMATED_FIVE_LEVEL':
            approximate.append(dict(hru=hid,**rec['audit']))
        fingerprints.append(f'{hid},{row["status"]},{row["sha256"]}\n')
    report.mkdir(parents=True,exist_ok=True)
    data=('hru,status,sha256\n'+''.join(fingerprints)).encode()
    with (report/'files.csv.gz').open('wb') as stream:
        with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0,filename='') as zipped:zipped.write(data)
    summary=dict(status='REAL_SOURCE_DRA_POPULATION_SERIALIZATION_PASS',hrus=len(ids),
        start=manifest['start'],end=manifest['end'],h1_source_months=manifest['h1_months'],
        methods=dict(methods),c2_static_physical_max_absolute_difference=dict(maxima),
        c2_static_physical_changed_above_tolerance=dict(changed),
        owner_events=dict(decision_counts),approximate=approximate,
        source_manifest_sha256=sha(output/'source_manifest.json'),
        production_manifest_sha256=sha(output/'production_manifest.json'),
        c2_archive_sha256=sha(c2_archive),files_csv_sha256=hashlib.sha256(data).hexdigest(),
        dra_bytes=sum(p.stat().st_size for p in files.values()),
        production_admitted=False,swap_executed=False,
        limits=['C2 comparison excludes monthly series: actual 637-month coverage replaces the 13-month C2 interval.',
                'C2 physical comparisons use tolerance 1e-9 * max(1,abs(reference)); maxima are unrounded.',
                'Serialization and source comparisons are not hydrological validation.'])
    if changed:raise ValueError('unexpected physical change against C2: '+str(changed))
    (report/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('output','c2-archive','report'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();r=qualify(args.output,args.c2_archive,args.report)
    print(json.dumps({k:v for k,v in r.items() if k not in ('approximate','limits')}))
