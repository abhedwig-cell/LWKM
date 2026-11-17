"""Read-only adapter for the actual national_hum.py MET07 receipt schema.

The inherited W11 profile name contains MET06. Qualification here therefore
requires the explicit MET07 catalogue status and correction linkage, not a
substring replacement in that historical profile identifier.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
import math
from pathlib import Path
import re
from common import (ROOT, PROFILE, W11_COMMIT, MET07_SUCCESS, NotReady,
    IntegrityError, file_sha, object_sha, read_json, assignments, one, basename,
    parse_date, table)

REPORTS = ('STATUS_MET07_LANDELIJK.json', 'HRU_MET07_RESULTS.json',
           'ANCHOR_MET_CHECKS.json', 'BINDING.json')
ALLOWED = {'MET07_REBOUND_HASH_VERIFIED', 'MET07_REUSED_HASH_VERIFIED'}


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def load_met07(cfg):
    reports = Path(cfg['met07_reports'])
    status_path = reports/REPORTS[0]
    if not status_path.is_file():
        raise NotReady('MET07_NOG_NIET_GEREED: statusrapport ontbreekt')
    status = read_json(status_path)
    n = cfg['expected_population']
    if (status.get('status') != MET07_SUCCESS or status.get('completed') != n
        or status.get('failed') != 0 or status.get('errors') != []
        or status.get('regression_anchors_matched') != len(cfg['anchors'])):
        raise NotReady('MET07_NOG_NIET_GEREED: ' + str(status.get('status')))
    data = {name: read_json(reports/name) for name in REPORTS}
    hashes = {name: file_sha(reports/name) for name in REPORTS}
    require(status['results_sha256'] == hashes[REPORTS[1]], 'MET07_RESULTS_HASH_MISMATCH')
    require(status['expected_population'] == n and status['requested_hrus'] == n,
            'MET07_POPULATION_COUNT_MISMATCH')
    require(status.get('production_enabled') is False and status.get('swap_executed') is False,
            'UNEXPECTED_UPSTREAM_QUALIFICATION')
    source = Path(cfg['source_root']).resolve()
    require(Path(status['output_root']).resolve() == source, 'MET07_OUTPUT_ROOT_MISMATCH')
    for key in ('start','end'):
        require(status['simulation_'+key] == cfg[key], 'MET07_PERIOD_MISMATCH')
    binding = data['BINDING.json']; bs = object_sha(binding)
    require(bs == status['binding_sha256'], 'MET07_BINDING_HASH_MISMATCH')
    expected_binding = cfg.get('expected_met07_binding_sha256')
    if expected_binding:
        require(bs == expected_binding, 'UNEXPECTED_MET07_SOFTWARE_OR_CONFIG_BINDING')
    bc = binding['config']
    require(Path(bc['output_root']).resolve() == source
            and bc['expected_population'] == n
            and bc['start'] == cfg['start'] and bc['end'] == cfg['end'], 'MET07_BOUND_CONFIG_MISMATCH')
    hum = bc['hum']
    require(hum['quantity'] == 'actual_vapour_pressure' and hum['unit'] == 'kPa'
            and hum['scale'] == 1, 'MET07_HUM_CONTRACT_MISMATCH')
    require(file_sha(source/'BINDING.json') == hashes['BINDING.json'], 'MET07_ROOT_BINDING_DIFFERS')
    records = data['HRU_MET07_RESULTS.json']
    ids = [r['hru'] for r in records]
    require(len(ids) == n and len(set(ids)) == n and set(ids) == set(range(1,n+1)),
            'MET07_POPULATION_MISMATCH')
    days = (date.fromisoformat(cfg['end'])-date.fromisoformat(cfg['start'])).days+1
    for r in records:
        require(r['status'] in ALLOWED and r['non_hum_bytes_verified_equal'] is True
                and r['unchanged_other_assets'] is True and r['days'] == days,
                'MET07_RECORD_NOT_QUALIFIED: '+str(r['hru']))
        require(Path(r['run_directory']).resolve() == source/('run_%05d'%r['hru']),
                'MET07_RECORD_WRONG_RUN_PATH')
    by_id = {r['hru']:r for r in records}
    anchors = data['ANCHOR_MET_CHECKS.json']
    require(len(anchors) == len(cfg['anchors'])
            and {str(a['hru']) for a in anchors} == set(cfg['anchors']), 'MET07_ANCHOR_POPULATION')
    for a in anchors:
        expected = cfg['anchors'][str(a['hru'])]
        require(a['matched'] is True and a['expected'] == expected and a['actual'] == expected
                and by_id[a['hru']]['corrected_met_sha256'] == expected,
                'MET07_ANCHOR_MISMATCH')
    # This is a snapshot identity check, not another numerical UG calculation.
    require(file_sha(reports/'HUM_SOURCE_LEDGER.csv') == status['source_ledger_sha256'],
            'MET07_SOURCE_LEDGER_CHANGED')
    hashes['HUM_SOURCE_LEDGER.csv'] = status['source_ledger_sha256']
    return status, by_id, hashes


def verify_assets(directory, assets):
    for name, spec in assets.items():
        p = Path(directory)/basename(name)
        require(p.is_file() and not p.is_symlink() and p.stat().st_size == spec['bytes']
                and file_sha(p) == spec['sha256'], 'INPUT_HASH_OR_SIZE_CHANGED: '+str(p))


def package(cfg, record, full=True):
    hid = record['hru']; root = Path(cfg['source_root'])
    path = root/'catalogue'/('run_%05d.json'%hid); directory = root/('run_%05d'%hid)
    require(file_sha(path) == record['catalogue_sha256'], 'MET07_CATALOGUE_CHANGED: '+str(hid))
    cat = read_json(path)
    require(cat['hru'] == hid and cat['profile_id'] == PROFILE and cat['w11_source_commit'] == W11_COMMIT
            and cat['status'] == 'MET07_HUM_CORRECTED_SOURCE_CATALOGUE_NOT_ADMITTED',
            'NOT_MET07_CATALOGUE: '+str(hid))
    assets = cat['assets']
    require(assets and len(assets) == record['assets']
            and sum(a['bytes'] for a in assets.values()) == record['bytes'], 'ASSET_COUNTS_DIFFER')
    require(len({basename(n).casefold() for n in assets}) == len(assets), 'CASE_INSENSITIVE_NAME_COLLISION')
    require('swap.swp' in assets and all(Path(n).suffix.lower() in
        ('.swp','.crp','.co2','.met','.bbc','.dra') for n in assets), 'UNEXPECTED_INPUT_ASSET_TYPE')
    require(not directory.is_symlink() and directory.is_dir(), 'INVALID_RUN_DIRECTORY')
    expected_manifest = dict(schema_version=1,status='PACKAGE_CANDIDATE_NOT_ADMITTED',
        run_id=hid,profile_id=PROFILE,code_commit=W11_COMMIT,
        assets={n:{k:a[k] for k in ('sha256','qualification_id')} for n,a in assets.items()})
    require(read_json(directory/'manifest.json') == expected_manifest, 'W11_MANIFEST_DIFFERS')
    require({p.name for p in directory.iterdir()} == set(assets)|{'manifest.json'},
            'IMMUTABLE_PACKAGE_HAS_EXTRA_OR_MISSING_FILES')
    # Preparation hashes only small SWP/CRP/CO2 files. Every asset is hashed before
    # copying/executing and again after execution. There is no size-only run gate.
    selected = assets if full else {n:a for n,a in assets.items() if Path(n).suffix.lower() in ('.swp','.crp','.co2')}
    verify_assets(directory, selected)
    text = (directory/'swap.swp').read_text(encoding='utf-8-sig'); a = assignments(text)
    start, end = parse_date(one(a,'TSTART')), parse_date(one(a,'TEND'))
    require(str(start) == cfg['start'] and str(end) == cfg['end']
            and start == parse_date(cat['swp_start_literal']) and end == parse_date(cat['swp_end_literal']),
            'MODEL_PERIOD_CHANGED')
    for key in ('PATHWORK','PATHATM','PATHCROP','PATHDRAIN'):
        require(all(x.strip() in ('','.','./','.\\') for x in a.get(key,[])), 'EXTERNAL_SWP_PATH: '+key)
    for key, ext in (('METFIL','.met'),('BBCFIL','.bbc'),('DRFIL','.dra')):
        name = basename(one(a,key))
        if not Path(name).suffix: name += ext
        require(name in assets and Path(name).suffix.lower() == ext, 'UNBOUND_REFERENCE: '+key)
    met = basename(one(a,'METFIL'))
    if not Path(met).suffix: met += '.met'
    corr_receipt = cat['hum_correction']; corr = corr_receipt['correction']; inp = corr_receipt['inputs']
    require(cat['derived_input_changed'] == met and assets[met]['sha256'] == record['corrected_met_sha256']
            and corr['corrected_sha256'] == assets[met]['sha256'] and corr['hru'] == hid
            and corr['days'] == (end-start).days+1 and corr['non_hum_bytes_verified_equal'] is True
            and corr['source_sha256'] == record['original_met_sha256']
            and inp['hru'] == hid and inp['binding_sha256'] == cat['binder_code_sha256']
            and inp['original_catalogue_sha256'] == record['original_catalogue_sha256']
            and inp['start'] == str(start) and inp['end'] == str(end), 'HUM_CORRECTION_LINK_MISMATCH')
    require(cat['binder_code_sha256'] == cfg['_met07_binding'], 'CATALOGUE_WRONG_MET07_BINDING')
    for key, val in (('SWCSV',1),('NPRINTDAY',1),('PERIOD',1),('SWMONTH',0)):
        require(float(one(a,key)) == val, 'NOT_DAILY_CSV_PROFILE: '+key)
    stem = basename(one(a,'OUTFIL')); output = stem+'_output.csv'
    require(stem.lower() not in ('runtime','execution','task','summary','status','manifest'), 'OUTPUT_COLLISION')
    for suffix in ('_output.csv','.log','.err','.inf','.swp','.crp','.met','.dra','.bbc','.co2'):
        if suffix in ('.swp','.crp','.met','.dra','.bbc','.co2'): continue
        require((stem+suffix).casefold() not in {n.casefold() for n in assets}, 'OUTPUT_INPUT_COLLISION')
    return directory, cat, dict(start=str(start),end=str(end),output=output,met=met), text


def features(directory, cat, text):
    """Describe actual settings, not inferred land-use or BOFEK class labels."""
    a = assignments(text)
    rot = table(text,['CROPSTART','CROPEND','CROPNAME','CROPFIL','CROPTYPE'],5)
    crops = sorted({str(row[3]) for row in rot}) if rot else []
    crops = [n if n.lower().endswith('.crp') else n+'.crp' for n in crops]
    missing = []; schedules = []; origin = {'crop':'swap.swp:CROPSTART table',
        'soil':'swap.swp:hydraulic and discretization tables', 'bottom':'swap.swp:SWBOTB',
        'drainage':'swap.swp:SWDRA','irrigation':'referenced CRP:SCHEDULE'}
    if not crops: missing.append('crop_rotation')
    for name in crops:
        require(name in cat['assets'], 'CROP_REFERENCE_NOT_IN_CATALOGUE')
        c = assignments((directory/name).read_text(encoding='utf-8-sig'))
        schedules.append(name+':'+(one(c,'SCHEDULE') if len(c.get('SCHEDULE',[])) == 1 else 'UNKNOWN'))
    hyd = table(text,['ORES','OSAT','ALFA','NPAR'],10)
    dis = table(text,['ISUBLAY','ISOILLAY','HSUBLAY','NCOMP'],4)
    soil = 'UNKNOWN'
    if hyd and dis:
        try:
            numeric = [[float(v.replace('D','E').replace('d','e')) for v in row] for row in hyd+dis]
            if not all(math.isfinite(x) for r in numeric for x in r): raise ValueError('nonfinite')
            soil = object_sha(numeric)
        except ValueError:
            missing.append('soil_numeric_table')
    else: missing.append('soil_tables')
    result = dict(crop='|'.join(crops) or 'UNKNOWN',soil=soil,
        bottom=one(a,'SWBOTB') if len(a.get('SWBOTB',[])) == 1 else 'UNKNOWN',
        drainage=one(a,'SWDRA') if len(a.get('SWDRA',[])) == 1 else 'UNKNOWN',
        irrigation='|'.join(schedules) or 'UNKNOWN')
    for key,value in result.items():
        if 'UNKNOWN' in value and key not in missing: missing.append(key)
    result['combination'] = '|'.join(result[k] for k in ('crop','bottom','drainage','irrigation'))
    return dict(values=result, sources=origin, missing=missing,
                soil_label='exact hydraulic/discretization fingerprint; not a BOFEK class')


def select_initial(metadata, count, anchors):
    """Deterministic rare-category coverage, followed by lowest-ID filling.

    Selection is purposive coverage, not a statistical representative sample.
    Ties use the lowest HRU ID. Coverage gaps are retained in the report.
    """
    ids = sorted(metadata); count = min(count,len(ids)); selected = []
    labels = {h:{k+'='+str(v) for k,v in metadata[h]['values'].items()} for h in ids}
    freq = Counter(x for ls in labels.values() for x in ls); covered = set(); reasons = {}
    for h in sorted(anchors):
        if h in metadata and len(selected)<count:
            selected.append(h); covered |= labels[h]; reasons[str(h)] = ['previous_full_period_trial']
    while len(selected)<count:
        remaining = [h for h in ids if h not in selected]
        def score(h):
            new = sorted(labels[h]-covered)
            # First cover process settings, then soil fingerprints/combinations.
            major = sum(1/freq[x] for x in new if x.split('=')[0] in ('crop','bottom','drainage','irrigation'))
            other = sum(1/freq[x] for x in new)
            return (major,other,-h)
        h = max(remaining,key=score); new = sorted(labels[h]-covered)
        selected.append(h); reasons[str(h)] = new or ['deterministic_population_fill']
        covered |= labels[h]
    return dict(selected_hrus=selected,selection_reasons=reasons,
        method='rare_category_greedy_then_lowest_id_v1',statistical_representativeness_claimed=False,
        total_categories=len(freq),covered_categories=len(covered),
        uncovered_categories={k:freq[k] for k in sorted(set(freq)-covered)},
        missing_metadata_hrus=[h for h in ids if metadata[h]['missing']],
        category_frequencies=dict(sorted(freq.items())))
