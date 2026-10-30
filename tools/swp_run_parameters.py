"""Direct replacement for the v0.38 Runs writer, without XLS or SQLite.

Grid sampling uses actual coordinates, never raster-array offsets across grids.
Identity is supplied by HRU CSV. Four-class crop policy is explicit and separate
from historical 22-class reproduction. Output remains a source candidate.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from tools.swp_hru_authority import rows, number, unique
from tools.dqsat_policy import summarize

FIELDS = 'run_id,scenario_id,bodem_id,soil2_id,lu_id,climate_id,SWBBCFILE,SWBOTB,dqsat,BBCFIL,DRFIL,METFIL,irrigation_id,solute_id,rotation_id,SWINCO,GWLI,RDS,PONDMX,RSRO,tempBot,glk,area,xc,yc,col,row,nusvat,TSTART,TEND,SWETR,soil_id,crop_id,croporg_id,dikte_id,COFANI,NUMNODNEW'.split(',')
GRID_KEYS = ('glk', 'area', 'rds', 'dqsat', 'lgn', 'soil2', 'bfe', 'irr_switch', 'meteo', 'vc', 'riv_infil', 'bbc')


def nint(v):
    return math.floor(v + .5) if v >= 0 else math.ceil(v - .5)


def mode(values):
    counts = Counter(values)
    best = max(counts.values())
    winners = [v for v, count in counts.items() if count == best]
    if len(winners) != 1:
        raise ValueError(f'ambiguous mode {winners}; historical MAJORITY tie rule not verified')
    return winners[0]


def finite(row, key):
    v = float(row[key])
    if not math.isfinite(v):
        raise ValueError(f'nonfinite {key}')
    return v


def derive(hru, members, soil_lookup, crop_lookup, config):
    hid = number(hru, 'HRU', 'hru')
    rep = number(hru, 'svat_repr', 'hru_representative_svat')
    by_svat = unique(members, lambda r: number(r, 'svat'))
    if rep not in by_svat:
        raise ValueError(f'representative SVAT {rep} is not an HRU member')
    representative = by_svat[rep]
    soil = number(hru, 'bodem370', 'bodem_repr')
    soil2 = number(soil_lookup[soil], 'grondsoort2')
    # lu4 is an identity field, never a mode of member land use.
    lu4 = number(hru, 'lu4')
    crop = crop_lookup[(soil2, lu4)]
    lgn = number(hru, 'landgebruik22') if hru.get('landgebruik22', '') != '' else number(representative, 'lgn')
    if hru.get('rz_repr', '') != '':
        rds = finite(hru, 'rz_repr')  # schema centimetres, v0.38 /100 then *100
        root_source = 'HRU_rz_repr_cm'
    elif config.get('root_policy') == 'representative_grid':
        rds = finite(representative, 'rds') * 100
        root_source = 'EXPLICIT_representative_grid_m'
    else:
        raise ValueError('rz_repr missing; representative_grid requires explicit root_policy')
    if rds <= 0:
        raise ValueError('nonpositive RDS')
    n = len(members)
    avg = lambda key: math.fsum(finite(m, key) for m in members) / n
    glk = avg('glk')
    gwli = min(0, nint((avg('head') - glk) * 100))
    area = math.fsum(finite(m, 'area') for m in members)
    if any(finite(m, 'area') <= 0 for m in members):
        raise ValueError('nonpositive member area')
    # Same geometric nearest-member rule as v0.38; reject unresolved ties.
    x, y = avg('x'), avg('y')
    distances = [(finite(m, 'x')-x)**2 + (finite(m, 'y')-y)**2 for m in members]
    nearest = [m for m, d in zip(members, distances) if d == min(distances)]
    # Stable tie handling; position is descriptive, not an HRU identity choice.
    center = min(nearest, key=lambda m: number(m, 'svat'))
    irrigation = [number(m, 'irr_switch') for m in members]
    fraction = sum(v > 0 for v in irrigation)/n
    irrigation_counts = Counter(v for v in irrigation if v > 0)
    if any(v not in (0, 1, 2) for v in irrigation):
        raise ValueError('unsupported irrigation source code; expected 0, 1 (groundwater), 2 (surface water)')
    # Owner decision 2026-10-30: choose the source by actual SVAT area,
    # with groundwater (1) winning an exact tie. National allocation follows derive.
    irrigation_areas = {code: math.fsum(finite(m, 'area') for m, v in zip(members, irrigation) if v == code)
                        for code in (1, 2)}
    irr = (1 if irrigation_areas[1] >= irrigation_areas[2] else 2) if any(irrigation_counts.values()) else 0
    bbc = mode([number(m, 'bbc') for m in members])
    policy = config.get('dqsat_policy', 'positive_member_median')
    if policy != 'positive_member_median':
        raise ValueError('unsupported dqsat policy; owner decision requires positive_member_median')
    dq = summarize([float(m['dqsat']) for m in members],
                   float(representative['dqsat']), config.get('dqsat_nodata'))
    dqsat = dq['positive_median']
    row = dict(run_id=hid, scenario_id='direct', bodem_id=soil, soil2_id=soil2,
               lu_id=lgn, climate_id=config['climate_id'], SWBBCFILE=0 if bbc==7 else 1,
               SWBOTB=bbc, dqsat=dqsat, BBCFIL=hid, DRFIL=hid, METFIL=f'{hid}.met',
               irrigation_id=irr, solute_id=0, rotation_id='max', SWINCO=2,
               GWLI=gwli, RDS=nint(rds), PONDMX=float(config['MaxPondDepth'])*100,
               RSRO=float(config['crunoff_par']), tempBot=float(config['tempCbotk']),
               glk=glk, area=area, xc=finite(center,'x'), yc=finite(center,'y'),
               col=number(center,'col'), row=number(center,'row'), nusvat=n,
               TSTART=config['start'], TEND=config['end'], SWETR=number(crop,'SWETR'),
               soil_id=number(soil_lookup[soil],'soil_id'), crop_id=number(crop,'crop_id'),
               croporg_id=number(crop,'croporg_id'), dikte_id=1700, COFANI=1., NUMNODNEW=43)
    meteo_counts = Counter(number(m,'meteo') for m in members)
    return row, dict(HRU=hid, lu4=lu4, root_source=root_source,
                    centroid_tie_candidates=len(nearest),
                    dqsat_policy=policy, dqsat=dq,
                    irrigation_fraction=fraction, irrigation_area_fraction=math.fsum(irrigation_areas.values())/area,
                    irrigation_allocation='PENDING_NATIONAL_AREA_ALLOCATION', irrigation_source_counts=dict(irrigation_counts),
                    irrigation_source_areas_m2=irrigation_areas,
                    irrigation_source_policy='ACTUAL_SVAT_AREA_GROUNDWATER_ON_EXACT_TIE_OWNER_20261030',
                    irrigation_tie_policy='GROUNDWATER',
                    irrigation_source_tied=bool(irrigation_counts) and irrigation_areas[1]==irrigation_areas[2],
                    meteo_region_counts=dict(meteo_counts))



def allocate_irrigation(runs, diagnostics):
    """Choose the closest area prefix in decreasing irrigated-area fraction.

    Exact rational ranking/sums prevent input order and accumulation roundoff
    deciding ties. Equal fractions use ascending HRU ID; equal deviations
    choose the smaller assigned area. Never select a zero-irrigation HRU.
    """
    by_id = unique(diagnostics, lambda d: int(d['HRU']))
    run_ids = [int(r['run_id']) for r in runs]
    if len(set(run_ids)) != len(runs) or set(run_ids) != set(by_id):
        raise ValueError('irrigation allocation population mismatch')
    records = []
    for run in runs:
        hid = int(run['run_id']);diag = by_id[hid]
        area = Fraction(str(run['area']))
        source = {i: Fraction(str(diag['irrigation_source_areas_m2'].get(i,
                              diag['irrigation_source_areas_m2'].get(str(i), 0)))) for i in (1, 2)}
        irrigated = sum(source.values())
        if area <= 0 or min(source.values()) < 0 or irrigated > area:
            raise ValueError(f'HRU {hid}: invalid irrigation support area')
        code = 1 if source[1] >= source[2] else 2
        records.append((hid, area, irrigated, source, code, run, diag))
    candidates = sorted((r for r in records if r[2] > 0), key=lambda r: (-r[2]/r[1], r[0]))
    target = sum((r[2] for r in records), Fraction(0))
    total = Fraction(0);best = (abs(target), Fraction(0), 0)
    for index, record in enumerate(candidates, 1):
        total += record[1]
        best = min(best, (abs(total-target), total, index))
    selected = {r[0] for r in candidates[:best[2]]}
    rank = {r[0]:i for i,r in enumerate(candidates, 1)}
    counts = Counter();assigned_source = {i:Fraction(0) for i in (1,2)}
    reference_source = {i:sum((r[3][i] for r in records),Fraction(0)) for i in (1,2)}
    for hid, area, irrigated, source, code, run, diag in records:
        enabled = hid in selected
        run['irrigation_id'] = code if enabled else 0
        counts[run['irrigation_id']] += 1
        if enabled:assigned_source[code] += area
        diag.update(irrigation_allocation='NATIONAL_CLOSEST_AREA_PREFIX_OWNER_20261030',
                    irrigation_area_fraction=float(irrigated/area),
                    irrigation_allocation_rank=rank.get(hid),irrigation_enabled=enabled,
                    irrigation_selected_source=run['irrigation_id'])
    assigned = best[1];difference = assigned-target
    return dict(policy='NATIONAL_CLOSEST_AREA_PREFIX_OWNER_20261030',status='COMPLETE_POPULATION_ALLOCATED',
        hru_count=len(runs),candidate_hrus=len(candidates),irrigated_hrus=len(selected),
        svat_irrigated_area_m2=float(target),hru_irrigated_area_m2=float(assigned),
        difference_m2=float(difference),difference_ha=float(difference/10000),
        difference_percent=float(100*difference/target) if target else 0.,
        assigned_hrus_by_code={str(i):counts[i] for i in (0,1,2)},
        source_areas_m2={str(i):dict(svat=float(reference_source[i]),hru=float(assigned_source[i]),
                                  difference=float(assigned_source[i]-reference_source[i])) for i in (1,2)},
        last_selected_hru=candidates[best[2]-1][0] if best[2] else None,
        first_excluded_hru=candidates[best[2]][0] if best[2]<len(candidates) else None,
        effective_fraction=float(candidates[best[2]-1][2]/candidates[best[2]-1][1]) if best[2] else None,
        fraction_tie_policy='ASCENDING_HRU_ID',equal_deviation_policy='SMALLER_ASSIGNED_AREA',
        qualification='National area allocation only; regional and hydrological equivalence not established')

def read_control(path, base):
    result = {}
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        line = raw.split('!',1)[0].strip()
        if '=' not in line:
            continue
        key, value = (v.strip() for v in line.split('=',1))
        key = key.lower()
        if key in result:
            raise ValueError(f'duplicate control key {key}')
        result[key] = value.strip('\"\'')
    paths = {}
    for key in GRID_KEYS:
        if key in result:
            paths[key] = str(base / result[key].replace('\\', '/'))
    return result, paths


def sample_grid(path, members):
    import numpy as np  # actual server has NumPy; only sampling needs it
    path = Path(path)
    if path.suffix.lower() == '.idf':
        from tools.idf_reader import read_idf
        g = read_idf(path)
        values, xmin, ymax, dx, dy, nodata = g.values,g.xmin,g.ymax,g.dx,g.dy,g.nodata
    else:
        with path.open() as f:
            header = dict(f.readline().lower().split() for _ in range(6))
        dx = dy = float(header['cellsize'])
        xmin = float(header['xllcorner']) if 'xllcorner' in header else float(header['xllcenter'])-dx/2
        ymin = float(header['yllcorner']) if 'yllcorner' in header else float(header['yllcenter'])-dy/2
        ymax = ymin + int(header['nrows'])*dy
        nodata = float(header['nodata_value'])
        values = np.loadtxt(path, skiprows=6, ndmin=2)
        if values.shape != (int(header['nrows']), int(header['ncols'])):
            raise ValueError(f'raster size mismatch {path}')
    samples = []
    for m in members:
        x,y = finite(m,'x'),finite(m,'y')
        col,row = math.floor((x-xmin)/dx), math.floor((ymax-y)/dy)
        if not 0 <= row < values.shape[0] or not 0 <= col < values.shape[1]:
            raise ValueError(f'SVAT {m["svat"]} outside {path}')
        if not math.isclose(x,xmin+(col+.5)*dx,abs_tol=1e-5,rel_tol=0) or not math.isclose(y,ymax-(row+.5)*dy,abs_tol=1e-5,rel_tol=0):
            raise ValueError(f'SVAT {m["svat"]} not on cell centre {path}')
        v = float(values[row,col])
        if v == nodata or not math.isfinite(v):
            raise ValueError(f'SVAT {m["svat"]} NoData {path}')
        samples.append((v,col+1,row+1))
    return samples


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('hru','members','soil','crop','config','output'):
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--control',type=Path)
    p.add_argument('--base',type=Path,default=Path('.'))
    p.add_argument('--expected-hrus',type=int,default=10242)
    args = p.parse_args()
    config = json.loads(args.config.read_text())
    if date.fromisoformat(config['end']) < date.fromisoformat(config['start']):
        raise ValueError('end before start')
    members = list(rows(args.members))
    unique(members,lambda m:number(m,'svat'))
    sources = {n:str(getattr(args,n)) for n in ('hru','members','soil','crop','config')}
    if args.control:
        control, paths = read_control(args.control,args.base)
        # Head is explicit: start-date binding must be reviewed, never nearest date.
        paths['head'] = config['head_file']
        required = ('glk','area','dqsat','lgn','bfe','irr_switch','meteo','bbc','head')
        if config.get('root_policy') == 'representative_grid':
            required += ('rds',)
        for key in required:
            path = paths[key]
            print(f'SAMPLE {key}: {path}',flush=True)
            for m,(v,col,row) in zip(members,sample_grid(path,members)):
                if key not in ('glk','area','dqsat','rds','head') and not v.is_integer():
                    raise ValueError(f'noninteger class in {key}: {v}')
                m[key] = str(v) if key in ('glk','area','dqsat','rds','head') else str(int(v))
                if key=='head':
                    m['col'],m['row']=str(col),str(row)
            sources['grid_'+key]=path
        sources['control']=str(args.control)
    hrus = unique(rows(args.hru),lambda r:number(r,'HRU','hru'))
    if len(hrus) != args.expected_hrus:
        raise ValueError(f'expected {args.expected_hrus} HRUs, found {len(hrus)}')
    groups = defaultdict(list)
    for m in members:
        groups[number(m,'HRU','hru')].append(m)
    if set(groups) != set(hrus):
        raise ValueError('membership and HRU population differ')
    soil = unique(rows(args.soil), lambda r:number(r,'bodem370'))
    crop = unique(rows(args.crop), lambda r:(number(r,'soil2_id'),number(r,'lu4')))
    args.output.mkdir(parents=True, exist_ok=True)
    result, diagnostics, errors = [],[],[]
    for hid,hru in sorted(hrus.items()):
        try:
            row,diag = derive(hru,groups[hid],soil,crop,config)
            result.append(row); diagnostics.append(diag)
        except (KeyError,ValueError,ZeroDivisionError) as exc:
            errors.append({'HRU':hid,'error':str(exc)})
    if not errors:
        allocation=allocate_irrigation(result,diagnostics)
        (args.output/'irrigation_allocation.json').write_text(json.dumps(allocation,indent=2)+'\n')
    for name,records in [('runs_candidate',result),('diagnostics',diagnostics),('errors',errors)]:
        target=args.output/(name+'.json')
        target.write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
    # Never retain an earlier success table after an incomplete rerun.
    target=args.output/'runs_candidate.csv'
    target.unlink(missing_ok=True)
    if not errors:
        with target.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(result)
    manifest={'status':'FAILED' if errors else 'RUN_PARAMETERS_SOURCE_CANDIDATE',
              'hrus':len(result),'failed_hrus':len(errors),
              'sources':{k:{'path':v,'sha256':hashlib.sha256(Path(v).read_bytes()).hexdigest()} for k,v in sources.items()}}
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':manifest['status'],'hrus':len(result),'failed_hrus':len(errors)}))
    return 1 if errors else 0


if __name__=='__main__':
    raise SystemExit(main())
