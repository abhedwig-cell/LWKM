#!/usr/bin/env python3
"""Vier afgeleide Frank-tabellen met donorprofielen voor oorspronkelijke verdachte SVATs.

Leest uitsluitend voltooide v07-tabellen en de meegeleverde kwalificatie.
Geen nieuwe donorselectie, modelberekening, dagflux- of headverwerking.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import uuid

from schema import HEADERS, ID, COUNT, AREA, FLAG, REGION, NUMERIC_COLUMNS
from donor_bindings import load_bindings
from donor_profile import (HYDRO_COLUMNS, PRESERVED_COLUMNS, FLUX_COLUMNS,
                           apply_profile, validate_row)
from hru_aggregate import HruAggregator
from frank_io import (sha, digest, atomic_json, read_csv, check_row, integer,
                      number, assert_close, source_identity, run_lock)

VERSION = '08.0'
HERE = Path(__file__).resolve().parent
ROOT = Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal')
SOURCE_MANIFEST = 'MANIFEST_FRANK_LWKM_HRU_V07.json'
MANIFEST_NAME = 'MANIFEST_FRANK_VERDACHT_V08.json'
STATIC_CATEGORIES = tuple(HEADERS[3:12])
VARIANTS = (
    {'key': 'ONGECORRIGEERD', 'source_svat': 'FRANK_SVAT_LWKM_1991_2020.csv',
     'source_hru': 'FRANK_HRU_LWKM_1991_2020.csv',
     'svat': 'FRANK_SVAT_LWKM_VERDACHT_VERVANGEN_1991_2020.csv',
     'hru': 'FRANK_HRU_LWKM_VERDACHT_VERVANGEN_1991_2020.csv'},
    {'key': 'FLEVOLAND', 'source_svat': 'FRANK_SVAT_LWKM_FLEVOLAND_1991_2020.csv',
     'source_hru': 'FRANK_HRU_LWKM_FLEVOLAND_1991_2020.csv',
     'svat': 'FRANK_SVAT_LWKM_FLEVOLAND_VERDACHT_VERVANGEN_1991_2020.csv',
     'hru': 'FRANK_HRU_LWKM_FLEVOLAND_VERDACHT_VERVANGEN_1991_2020.csv'},
)


def fmt(value):
    return '' if value is None else format(value, '.15g')


def optional_number(value):
    return None if not value.strip() else number(value, 'numerieke vergelijking')


def different(left, right):
    if left.strip() == right.strip():
        return False
    if not left.strip() or not right.strip():
        return True
    try:
        return float(left) != float(right)
    except ValueError:
        return True


def load_reference(directory):
    directory = Path(directory)
    sources = json.loads((directory / 'SOURCES.json').read_text(encoding='utf-8'))
    for name in ('SVAT_HRU.csv.gz', 'HRU_SCHEMA.csv.gz'):
        if sha(directory / name) != sources['outputs'][name]['sha256']:
            raise ValueError('Meegeleverde referentie gewijzigd: ' + name)
    membership, positions = {}, {}
    with read_csv(directory / 'SVAT_HRU.csv.gz',
                  required=['svat', 'HRU', 'x', 'y', 'svat_area_m2']) as rows:
        for row in rows:
            check_row(row, 'LWKM-membership')
            sid, hru = integer(row['svat'], 'svat'), integer(row['HRU'], 'HRU')
            if sid in membership:
                raise ValueError('Dubbele SVAT in membership: ' + str(sid))
            membership[sid] = hru
            positions[sid] = (number(row['x'], 'x'), number(row['y'], 'y'))
            if number(row['svat_area_m2'], 'historisch oppervlak') <= 0:
                raise ValueError('Historisch oppervlak is niet positief')
    counts = Counter(membership.values())
    if len(set(positions.values())) != len(positions):
        raise ValueError('Meerdere geselecteerde SVATs op hetzelfde celcentrum')
    if len(membership) != sources['checks']['membership_rows'] or len(counts) != sources['checks']['unique_hrus']:
        raise ValueError('Referentieaantallen wijken af van het bronregister')
    schema_ids = set()
    with read_csv(directory / 'HRU_SCHEMA.csv.gz', required=['HRU', 'N', 'svat_repr']) as rows:
        for row in rows:
            hru = integer(row['HRU'], 'HRU-schema')
            if hru in schema_ids or hru not in counts:
                raise ValueError('Dubbele of onbekende HRU in referentieschema')
            schema_ids.add(hru)
            if integer(row['N'], 'HRU-schema N') != counts[hru]:
                raise ValueError('Schema-N wijkt af van membership: ' + str(hru))
            if membership.get(integer(row['svat_repr'], 'representant')) != hru:
                raise ValueError('Representant hoort niet bij de eigen HRU')
    if schema_ids != set(counts):
        raise ValueError('HRUs ontbreken in het referentieschema')
    return {'membership': membership, 'positions': positions, 'counts': counts,
            'sources': sources}


def bind_source(source, ref):
    source = Path(source)
    manifest_path = source / SOURCE_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError('Voltooide v07-uitvoer ontbreekt: ' + str(manifest_path) +
                                '. Laat START_FRANK_LWKM_HRU eerst afronden.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('status') != 'COMPLETE_BOOKKEEPING_COMPARISON_NOT_NEW_MODEL_RUN':
        raise ValueError('De v07-bron is niet als volledig vastgelegd')
    if manifest.get('version') not in ('07.0', '07.1'):
        raise ValueError('Niet ondersteunde bronversie: ' + str(manifest.get('version')))
    if manifest.get('headers') != HEADERS or manifest.get('delimiter') != ',':
        raise ValueError('Bron gebruikt niet de 49 overeengekomen kommagescheiden kolommen')
    if manifest.get('period') != '1991-2020' or manifest.get('years') != 30:
        raise ValueError('Bronperiode is niet 1991-2020 met 30 jaren')
    selection = manifest.get('selection', {})
    if selection.get('selected_svats') != len(ref['membership']) or selection.get('hrus') != len(ref['counts']):
        raise ValueError('v07-selectie en meegeleverde LWKM-koppeling verschillen')
    previous_data = manifest.get('identity', {}).get('sources', {}).get('data', {})
    for name in ('SVAT_HRU.csv.gz', 'HRU_SCHEMA.csv.gz'):
        if previous_data.get(name, {}).get('sha256') != ref['sources']['outputs'][name]['sha256']:
            raise ValueError('v07 gebruikte een andere SVAT-HRU-referentie: ' + name)
    identities = {SOURCE_MANIFEST: source_identity(manifest_path)}
    for variant in VARIANTS:
        for role, count in (('source_svat', len(ref['membership'])), ('source_hru', len(ref['counts']))):
            name = variant[role]
            record = manifest.get('tables', {}).get('outputs', {}).get(name)
            if not record or record.get('rows') != count:
                raise ValueError('Voltooide bronregistratie ontbreekt voor ' + name)
            identity = source_identity(source / name)
            if identity['sha256'] != record.get('sha256'):
                raise ValueError('v07-brontabel is gewijzigd of onvolledig: ' + name)
            identities[name] = identity
    return manifest, identities


def load_hru_rows(path, ref):
    result = {}
    with read_csv(path, exact=HEADERS) as rows:
        for row in rows:
            check_row(row, str(path))
            hru = integer(row[ID], 'HRU')
            if hru in result or hru not in ref['counts']:
                raise ValueError('Dubbele of onbekende bron-HRU: ' + str(hru))
            if integer(row[COUNT], 'HRU N') != ref['counts'][hru]:
                raise ValueError('Bron-HRU heeft een afwijkend ledenaantal: ' + str(hru))
            if number(row[AREA], 'HRU oppervlak') <= 0 or row[FLAG] not in ('0', '1'):
                raise ValueError('Ongeldig bron-HRU-oppervlak of indicator: ' + str(hru))
            for field in NUMERIC_COLUMNS:
                if row[field].strip():
                    number(row[field], field)
            result[hru] = row
    if set(result) != set(ref['counts']):
        raise ValueError('Bron-HRUs zijn niet volledig')
    return result


def scan_variant(path, ref, bindings, variant, progress):
    needed = {b['donor'] for b in bindings.values() if b['is_suspect']}
    donors, seen, support, large = {}, set(), {}, []
    static_hash = hashlib.sha256()
    for_index = ref['membership']
    for_key = variant['key']
    with read_csv(path, exact=HEADERS) as rows:
        for row in rows:
            validate_row(row)
            sid = integer(row[ID], 'SVAT')
            if sid not in for_index or sid in seen:
                raise ValueError('Onbekende of dubbele SVAT in bron: ' + str(sid))
            seen.add(sid)
            if for_key == 'ONGECORRIGEERD' and row[FLAG] != '0':
                raise ValueError('Ongecorrigeerde v07-bron heeft indicator 1: ' + str(sid))
            hru, area = for_index[sid], number(row[AREA], AREA)
            b = bindings[sid]
            item = support.setdefault(hru, {'n': 0, 'area': 0.0, 'suspects': 0,
                'suspect_area': 0.0, 'flevo': 0, 'flevo_area': 0.0,
                'p12_sources': 0, 'p12_source_area': 0.0,
                'retained_nonself': 0, 'changed': 0, 'changed_area': 0.0})
            item['n'] += 1
            item['area'] += area
            if b['is_suspect']:
                item['suspects'] += 1
                item['suspect_area'] += area
            elif b['donor'] != sid:
                item['retained_nonself'] += 1
            if row[FLAG] == '1':
                item['flevo'] += 1
                item['flevo_area'] += area
            if b['donor'] == sid:
                item['p12_sources'] += 1
                item['p12_source_area'] += area
            if sid in needed:
                donors[sid] = dict(row)
            if area > 62500:
                large.append({'SVAT': sid, 'HRU': hru, 'Opp_svat_m2': area,
                              'Verschil_met_62500_m2': area - 62500})
            payload = [row[k] for k in PRESERVED_COLUMNS]
            static_hash.update((json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
            if len(seen) % 50000 == 0:
                progress('{}: bron gecontroleerd {} / {}'.format(for_key, len(seen), len(for_index)))
    if seen != set(for_index) or set(donors) != needed:
        raise ValueError('SVATs of benodigde donorprofielen ontbreken in ' + str(path))
    return {'donors': donors, 'support': support, 'large_areas': large,
            'static_digest': static_hash.hexdigest(), 'rows': len(seen)}


def check_hru_support(before, scanned):
    for hru, support in scanned['support'].items():
        assert_close(number(before[hru][AREA], 'HRU oppervlak'), support['area'],
                     'Actueel HRU-oppervlak ' + str(hru), rel=2e-10, absolute=0.0001)


def write_column_rules(control):
    path = control / 'KOLOMREGELS.csv'
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Kolomnummer', 'Kolom', 'SVAT_regel', 'HRU_regel', 'Eenheid_of_betekenis'])
        for index, name in enumerate(HEADERS, 1):
            if name in HYDRO_COLUMNS:
                svat = 'Verdacht: donor uit dezelfde bronvariant; anders eigen waarde'
            elif name == FLAG:
                svat = '1 bij donorvervanging of bestaande Flevolandcorrectie; anders 0'
            else:
                svat = 'Eigen ontvangende SVAT behouden'
            if name == ID:
                hru = 'Bestaand HRU-nummer'
            elif name == COUNT:
                hru = 'Aantal ontvangende SVATs'
            elif name == AREA:
                hru = 'Som werkelijke ontvangende SVAT-oppervlakken'
            elif name in STATIC_CATEGORIES:
                hru = 'Bestaande vaste HRU-categorie uit v07'
            elif name in ('Gtnr', 'Kwelklasse4', REGION):
                hru = 'Unieke actuele ledenwaarden gescheiden door |'
            elif name == FLAG:
                hru = '1 als ten minste een lid indicator 1 heeft'
            else:
                hru = 'Gewogen met werkelijk ontvangend SVAT-oppervlak; leeg bij onvolledige dekking'
            unit = 'mm/jaar' if name in FLUX_COLUMNS else ('m-mv' if name in HEADERS[13:19] else '')
            if name == AREA:
                unit = 'm2'
            if name in ('Waterbalansfout MetaSWAP', 'Waterbalansfout overall'):
                unit += '; bestaande diagnostiek, geen nieuwe sluiting'
            writer.writerow([index, name, svat, hru, unit])


def write_variant(directory, source, ref, bindings, variant, scanned, before, progress):
    control = directory / 'controle'
    categories = {hru: {name: row[name] for name in STATIC_CATEGORIES} for hru, row in before.items()}
    # Gtnr en Kwelklasse komen uit de actuele leden, niet uit het oude schema.
    agg = HruAggregator(categories, membership=ref['membership'], use_schema_kwelklasse=False)
    changes, missing_donor = Counter(), Counter()
    replaced = numerically_changed = inherited_donor_flevo = original_target_flevo = 0
    audit_names = ['SVAT', 'HRU', 'Donor_SVAT', 'Kwalificatieredenen', 'Toewijzingslabel',
                   'Opp_target_m2', 'Opp_donor_m2', 'Oppervlakfactor_target_donor',
                   'X_target_RD', 'Y_target_RD', 'X_donor_RD', 'Y_donor_RD',
                   'Gebied_target', 'Gebied_donor', 'Vervanging_toegepast',
                   'Flevoland_target_voor_vervanging', 'Flevoland_gebruikt_donorprofiel',
                   'Indicator_resultaat', 'Aantal_gewijzigde_profielvelden',
                   'Gewijzigde_profielvelden', 'Lege_donorvelden', 'Afwijkende_locatiekenmerken']
    with (directory / variant['svat']).open('w', encoding='utf-8', newline='') as fout, \
         (control / ('SVAT_VERVANGING_' + variant['key'] + '.csv')).open('w', encoding='utf-8', newline='') as fa:
        writer = csv.DictWriter(fout, HEADERS)
        audit = csv.writer(fa)
        writer.writeheader()
        audit.writerow(audit_names)
        count = 0
        with read_csv(source / variant['source_svat'], exact=HEADERS) as rows:
            for row in rows:
                sid = integer(row[ID], 'SVAT')
                binding = bindings[sid]
                hru = ref['membership'][sid]
                donor = scanned['donors'].get(binding['donor']) if binding['is_suspect'] else None
                output = apply_profile(row, donor, binding['is_suspect'])
                writer.writerow(output)
                agg.add(hru, output)
                if output[FLAG] == '1':
                    scanned['support'][hru]['changed'] += 1
                    scanned['support'][hru]['changed_area'] += number(row[AREA], AREA)
                if binding['is_suspect']:
                    replaced += 1
                    changed = [name for name in HYDRO_COLUMNS if different(row[name], output[name])]
                    empty = [name for name in HYDRO_COLUMNS if not donor[name].strip()]
                    numerical = any(name in NUMERIC_COLUMNS for name in changed)
                    numerically_changed += bool(numerical)
                    changes.update(changed)
                    missing_donor.update(empty)
                    original_target_flevo += row[FLAG] == '1'
                    inherited_donor_flevo += donor[FLAG] == '1'
                    target_xy, donor_xy = ref['positions'][sid], ref['positions'][binding['donor']]
                    mismatches = [name for name in STATIC_CATEGORIES if different(row[name], donor[name])]
                    audit.writerow([sid, hru, binding['donor'], binding['reasons'], binding['label'],
                        row[AREA], donor[AREA], fmt(number(row[AREA], AREA) / number(donor[AREA], AREA)),
                        target_xy[0], target_xy[1], donor_xy[0], donor_xy[1], row[REGION], donor[REGION],
                        '1', row[FLAG], donor[FLAG], output[FLAG], len(changed), '|'.join(changed),
                        '|'.join(empty), '|'.join(mismatches)])
                count += 1
                if count % 50000 == 0:
                    progress('{}: SVAT-uitvoer {} / {}'.format(variant['key'], count, len(bindings)))
        if count != len(bindings):
            raise ValueError('Bronrijenaantal veranderde tijdens verwerking')
    support_names = ['HRU', 'N_SVAT', 'Opp_HRU_m2', 'N_vervangen', 'Opp_vervangen_m2',
                     'Aandeel_opp_vervangen', 'N_Flevoland_bron', 'N_indicator_1_resultaat',
                     'Opp_indicator_1_m2', 'N_nietverdacht_met_andere_donor_behouden',
                     'N_P12_donorgelijke_bronleden', 'Opp_P12_donorgelijke_bronleden_m2',
                     'P12_selectie_gebruikt_voor_deze_tabel']
    volume_names = ['HRU', 'Waterterm', 'Opp_HRU_m2', 'Voor_mm_jaar', 'Na_mm_jaar',
                    'Verschil_mm_jaar', 'Voor_m3eq_jaar', 'Na_m3eq_jaar', 'Verschil_m3eq_jaar']
    hru_count = 0
    with (directory / variant['hru']).open('w', encoding='utf-8', newline='') as fh, \
         (control / ('HRU_VERVANGING_' + variant['key'] + '.csv')).open('w', encoding='utf-8', newline='') as fs, \
         (control / ('HRU_WATERTERMEN_' + variant['key'] + '.csv')).open('w', encoding='utf-8', newline='') as fv:
        writer = csv.DictWriter(fh, HEADERS)
        sw, vw = csv.writer(fs), csv.writer(fv)
        writer.writeheader()
        sw.writerow(support_names)
        vw.writerow(volume_names)
        for row in agg.rows():
            hru = integer(row[ID], 'HRU')
            sup = scanned['support'][hru]
            assert_close(number(row[AREA], AREA), number(before[hru][AREA], AREA),
                         'Behoud HRU-oppervlak', rel=2e-10, absolute=0.0001)
            if integer(row[COUNT], COUNT) != ref['counts'][hru]:
                raise ValueError('HRU-leden veranderen bij donorvervanging')
            writer.writerow(row)
            sw.writerow([hru, sup['n'], fmt(sup['area']), sup['suspects'], fmt(sup['suspect_area']),
                fmt(sup['suspect_area'] / sup['area']), sup['flevo'], sup['changed'], fmt(sup['changed_area']),
                sup['retained_nonself'], sup['p12_sources'], fmt(sup['p12_source_area']), '0'])
            for name in FLUX_COLUMNS:
                old, new = optional_number(before[hru][name]), optional_number(row[name])
                delta = None if old is None or new is None else new - old
                scale = number(row[AREA], AREA) / 1000.0
                values = [old, new, delta, None if old is None else old * scale,
                          None if new is None else new * scale, None if delta is None else delta * scale]
                if any(value is not None and not math.isfinite(value) for value in values):
                    raise ValueError('Niet-eindig HRU-volume-equivalent')
                vw.writerow([hru, name, row[AREA]] + [fmt(v) for v in values])
            hru_count += 1
    if hru_count != len(ref['counts']):
        raise ValueError('Aantal HRUs veranderde bij donorvervanging')
    diagnostics = agg.diagnostics()
    diagnostics['method'] = 'area_weighted_target_population_after_suspect_profile_imputation'
    diagnostics['p12_donor_equal_selection_used'] = False
    diagnostics['fixed_categories'] = list(STATIC_CATEGORIES)
    diagnostics['gt_and_kwelclass'] = 'Distinct current member values separated by |; no recomputed classification.'
    atomic_json(control / ('HRU_AGGREGATIE_' + variant['key'] + '.json'), diagnostics)
    return {'source_variant': variant['key'], 'svats': count, 'hrus': hru_count,
        'replaced_svats': replaced, 'replaced_with_numeric_change': numerically_changed,
        'replaced_targets_originally_flevoland': original_target_flevo,
        'replaced_using_flevoland_donor_profile': inherited_donor_flevo,
        'changed_profile_fields': dict(changes), 'empty_donor_fields': dict(missing_donor),
        'retained_nonself_nonsuspect': sum(x['retained_nonself'] for x in scanned['support'].values()),
        'flagged_svats': diagnostics['corrected_svats'], 'flagged_hrus': diagnostics['corrected_hrus'],
        'actual_area_m2': diagnostics['total_area_m2'],
        'replacement_area_m2': math.fsum(x['suspect_area'] for x in scanned['support'].values())}


def verify_input_bytes(source, identities):
    for name, record in identities.items():
        if sha(source / name) != record['sha256']:
            raise ValueError('Bron gewijzigd tijdens verwerking: ' + name)


def verify_data_bytes(data, hashes):
    for name, expected in hashes.items():
        if sha(data / name) != expected:
            raise ValueError('Meegeleverde referentie gewijzigd tijdens verwerking: ' + name)


def verify_existing(output, manifest, fingerprint):
    if manifest.get('fingerprint') != fingerprint or manifest.get('status') != 'COMPLETE_DERIVED_DONOR_COMPARISON':
        raise FileExistsError('Bestaande uitvoer hoort bij andere bronnen of code. Gebruik --out met een nieuwe map.')
    expected = {v[k] for v in VARIANTS for k in ('svat', 'hru')}
    records = manifest.get('files', {})
    if not expected.issubset(records):
        raise ValueError('Bestaand uitvoermanifest mist tabellen')
    for name, record in records.items():
        path = output / name
        if not path.is_file() or sha(path) != record['sha256']:
            raise ValueError('Bestaande uitvoer ontbreekt of is gewijzigd: ' + name)


def run(args, progress=print):
    progress('Frank verdachte SVATs v' + VERSION)
    root = Path(args.root)
    source = Path(args.source) if args.source else root / 'frank_export_eindtabel/svat_lwkm_hru_v07'
    output = Path(args.out) if args.out else root / 'frank_export_eindtabel/svat_lwkm_hru_verdacht_v08'
    data = Path(args.data) if getattr(args, 'data', None) else HERE / 'data'
    if source.resolve() == output.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError('Kies een afzonderlijke uitvoermap buiten de v07-bronmap')
    progress('Stap 1: gekwalificeerde verdachte lijst en operationele donoren controleren.')
    data_names = ('SVAT_HRU.csv.gz', 'HRU_SCHEMA.csv.gz', 'SOURCES.json',
                  'SVAT_DONOR_QUALIFICATION.csv.gz', 'DONOR_SOURCES.json')
    data_hashes = {name: sha(data / name) for name in data_names}
    ref = load_reference(data)
    bindings, donor_sources = load_bindings(data, ref['membership'])
    verify_data_bytes(data, data_hashes)
    progress('Koppeling OK: {} SVATs, {} HRUs, {} verdachte SVATs.'.format(
        len(bindings), len(ref['counts']), sum(b['is_suspect'] for b in bindings.values())))
    progress('Stap 2: voltooide v07-tabellen en vastgelegde bestandshashes controleren.')
    source_manifest, identities = bind_source(source, ref)
    code_names = ('frank_verdacht.py', 'frank_io.py', 'donor_profile.py', 'donor_bindings.py', 'schema.py', 'hru_aggregate.py')
    code = {name: sha(HERE / name) for name in code_names}
    fingerprint = digest({'version': VERSION, 'source_hashes': {k: v['sha256'] for k, v in identities.items()},
                          'code': code, 'data': data_hashes})
    if args.check_only:
        previous_digest = None
        for variant in VARIANTS:
            scanned = scan_variant(source / variant['source_svat'], ref, bindings, variant, progress)
            before = load_hru_rows(source / variant['source_hru'], ref)
            check_hru_support(before, scanned)
            if previous_digest is not None and previous_digest != scanned['static_digest']:
                raise ValueError('Targetidentiteiten/oppervlakken/categorieen verschillen tussen v07-varianten')
            previous_digest = scanned['static_digest']
        verify_input_bytes(source, identities)
        verify_data_bytes(data, data_hashes)
        progress('CONTROLE OK. Alle donorprofielen aanwezig; geen nieuwe tabellen gemaakt.')
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with run_lock(output.parent / 'FRANK_VERDACHT_V08.lock.json'):
        if output.exists():
            if not (output / MANIFEST_NAME).is_file():
                raise FileExistsError('Uitvoermap bestaat zonder voltooid manifest: ' + str(output))
            verify_existing(output, json.loads((output / MANIFEST_NAME).read_text(encoding='utf-8')), fingerprint)
            verify_input_bytes(source, identities)
            verify_data_bytes(data, data_hashes)
            progress('KLAAR: bestaande vier donorvarianten opnieuw gecontroleerd: ' + str(output))
            return 0
        stage = output.with_name(output.name + '.gereed_' + uuid.uuid4().hex[:12])
        stage.mkdir()
        try:
            control = stage / 'controle'
            control.mkdir()
            write_column_rules(control)
            results, previous_digest = {}, None
            for variant in VARIANTS:
                progress('Stap 3: {} donorprofielen lezen en twee afgeleide tabellen schrijven.'.format(variant['key']))
                scanned = scan_variant(source / variant['source_svat'], ref, bindings, variant, progress)
                before = load_hru_rows(source / variant['source_hru'], ref)
                check_hru_support(before, scanned)
                if previous_digest is not None and previous_digest != scanned['static_digest']:
                    raise ValueError('Targetidentiteiten/oppervlakken/categorieen verschillen tussen v07-varianten')
                if previous_digest is None:
                    with (control / 'SVAT_OPPERVLAK_BOVEN_62500.csv').open('w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, ['SVAT', 'HRU', 'Opp_svat_m2', 'Verschil_met_62500_m2'])
                        writer.writeheader()
                        writer.writerows(scanned['large_areas'])
                    progress('INFO: {} SVATs boven 62500 m2 worden met hun opgegeven oppervlak verwerkt.'.format(len(scanned['large_areas'])))
                previous_digest = scanned['static_digest']
                results[variant['key']] = write_variant(stage, source, ref, bindings, variant, scanned, before, progress)
                del scanned, before
            progress('Stap 4: bronbehoud controleren en voltooide uitvoer publiceren.')
            verify_input_bytes(source, identities)
            verify_data_bytes(data, data_hashes)
            summary = ('Frank verdachte SVATs v08.0\n\n'
                       'Periode 1991-2020. CSV met komma; decimaal punt.\n'
                       'SVATs: {svats}; HRUs: {hrus}; vervangen per variant: {replaced}.\n'
                       'Overige SVATs met afwijkende donor blijven behouden: {retained}.\n'
                       '35 hydrologische velden uit dezelfde bronvariant van de operationele donor.\n'
                       'Eigen ontvangend oppervlak, locatie, landgebruik, bodem en HRU blijven behouden.\n'
                       'HRU: alle ontvangende oppervlakken meegewogen, geen P12 donor-equal-selectie.\n'
                       'Gt en kwelklasse: unieke actuele ledenklassen, gescheiden door |.\n'
                       'GxG en percentielen in HRUs zijn gewogen SVAT-kengetallen.\n'
                       'm3eq/jaar = mm/jaar * ontvangend oppervlak / 1000; geen oorspronkelijk lokaal MODFLOW-budget.\n'
                       'Balansvelden zijn overgenomen diagnostiek, geen nieuw berekende sluiting.\n'
                       'Details per vervanging, HRU en waterterm staan in controle.\n').format(
                           svats=len(bindings), hrus=len(ref['counts']),
                           replaced=results['ONGECORRIGEERD']['replaced_svats'],
                           retained=results['ONGECORRIGEERD']['retained_nonself_nonsuspect'])
            (stage / 'LEES_RESULTAAT.txt').write_text(summary, encoding='utf-8')
            files = {p.relative_to(stage).as_posix(): {'sha256': sha(p), 'size_bytes': p.stat().st_size}
                     for p in sorted(stage.rglob('*')) if p.is_file()}
            manifest = {'status': 'COMPLETE_DERIVED_DONOR_COMPARISON', 'version': VERSION,
                'created_utc': datetime.now(timezone.utc).isoformat(), 'fingerprint': fingerprint,
                'period': source_manifest['period'], 'years': source_manifest['years'],
                'source_directory': str(source.resolve()), 'sources': identities,
                'code': code, 'data': data_hashes, 'donor_reference': donor_sources,
                'headers': HEADERS, 'delimiter': ',', 'decimal': '.',
                'choices': {'profile_columns': list(HYDRO_COLUMNS), 'preserved_columns': list(PRESERVED_COLUMNS),
                    'selection': 'Only original positive qualification flags, not donor != self.',
                    'donor': 'Operational hru_cluster_donor_svat from the fixed qualified reference; same input variant.',
                    'missing': 'Keep missing donor values; no target fallback.',
                    'flag': '1 when replacement applied, even if values equal, or existing target Flevoland flag 1.',
                    'hru': 'All original target members weighted by actual target area; not P12 donor-equal.',
                    'hru_static_categories': list(STATIC_CATEGORIES),
                    'gt_kwelclass': 'Current member classes joined by |, no new classification.',
                    'volumes': 'Equivalent annual volumes on target area; not original local cell budgets.',
                    'balances': 'Source profile diagnostic values retained; no new model run or complete balance reconstruction.'},
                'results': results, 'files': files}
            atomic_json(stage / MANIFEST_NAME, manifest)
            if output.exists():
                raise FileExistsError('Uitvoermap ontstond tijdens verwerking: ' + str(output))
            stage.rename(output)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    progress('KLAAR: ' + str(output))
    for variant in VARIANTS:
        progress('  ' + variant['svat'])
        progress('  ' + variant['hru'])
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(ROOT), help='LWKM_run_resultaten_totaal')
    parser.add_argument('--source', help='Map met voltooide vier v07-tabellen en manifest')
    parser.add_argument('--out', help='Afzonderlijke uitvoermap voor de vier nieuwe tabellen')
    parser.add_argument('--data', help='Gekwalificeerde koppelingen; standaard de meegeleverde map data')
    parser.add_argument('--check-only', action='store_true', help='Controleer zonder tabellen te maken')
    args = parser.parse_args()
    try:
        return run(args, progress=lambda s: print(s, flush=True))
    except KeyboardInterrupt:
        print('\nAFGEBROKEN. De v07-bronnen blijven beschikbaar; start opnieuw.', file=sys.stderr)
        return 130
    except Exception as exc:
        print('STOP: ' + str(exc), file=sys.stderr, flush=True)
        print('De bestaande v07-tabellen zijn niet gewijzigd.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
