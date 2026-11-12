#!/usr/bin/env python3
"""Add true GxG and explicit annual volume/depth columns to existing Frank CSVs.
Read-only inputs; separate output directory; no LHM run or percentile replacement.
Python >=3.8, standard library only. Source contract: LWKM b06e8d576f1c,
tools/lwkm_frank/legacy/maak_svat_basis.py. Period 1991-2020, 30 years.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

YEARS = 30
CELL_M2 = 62500.0
ROOT = Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal')
OLD = ROOT / 'frank_export_eindtabel' / 'svat_basis_ongecorrigeerd_v01'
DEFAULTS = {
    'base': OLD / 'FRANK_SVAT_BASIS_ONGECORRIGEERD_1991_2020.csv',
    'audit': OLD / 'FRANK_SVAT_BASIS_CONTROLE_1991_2020.csv',
    'gxg': ROOT / 'frank_export_heads' / 'percentielen_v01' / 'FRANK_LHM_SVAT_GXG_GG_GW5_GW95_1991_2020.csv',
    'manifest': OLD / 'MANIFEST_FRANK_SVAT_BASIS.json',
    'out': ROOT / 'frank_export_eindtabel' / 'svat_leesbaar_v02',
}
MF = ([f'RIV_SYS{i}_ONTWATERING_m3' for i in range(1, 5)]
      + [f'RIV_SYS{i}_INFILTRATIE_m3' for i in range(1, 5)]
      + [f'DRN_SYS{i}_ONTWATERING_m3' for i in range(1, 4)]
      + ['FLF_KWEL_m3', 'FLF_WEGZIJGING_m3', 'LAT_NETTO_m3', 'WEL_NETTO_m3', 'GHB_NETTO_m3'])
MSW = ['bdgdecstot', 'bdgpm', 'bdgpssw', 'bdgpsgw', 'bdgetact', 'bdgqrun']
MSW_FIELDS = ['Neerslag', 'Beregening', 'Evapotranspiratie', 'Verdamping gewas',
              'Verdamping interceptie', 'Verdamping bodem', 'Oppervlakkige afstroming',
              'QModF', 'Bergingsverandering (MetaSWAP)', 'Waterbalansafwijking MetaSWAP']
MF_FIELDS = ['Ontwatering', 'Fldrou1', 'Fldrou2', 'Fldrou3', 'Fldrou4', 'Fldrou5',
             'Infiltratie', 'Fldrin1', 'Fldrin2', 'Fldrin345', 'Netto kwel/wegzijging',
             'Laterale stroming (netto)', 'Onttrekkingen (laag 1)', 'General head boundary',
             'Wegzijging', 'Kwel']
OVERALL = 'Waterbalansafwijking overall (excl. MODFLOW storage)'
GW = ['GLG', 'GHG', 'GG', 'Dynamiek', 'GW5', 'GW95']
NUM_META = ['Opp_svat/hru', *GW]
TECH_NAME = 'FRANK_SVAT_COMPLEET_TECHNISCH_1991_2020.csv'
READ_NAME = 'FRANK_SVAT_LEESBAAR_1991_2020.csv'
AUDIT_NAME = 'FRANK_SVAT_CONTROLE_UITGEBREID_1991_2020.csv'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def num(value, label):
    if value is None or str(value).strip().lower() in ('', 'nan', 'none', 'null'):
        raise ValueError('Ontbrekend getal: ' + label)
    text = str(value).strip()
    if ',' in text and '.' in text:
        raise ValueError('Ambigue getalnotatie: ' + label)
    try:
        result = float(text.replace(',', '.'))
    except ValueError as exc:
        raise ValueError('Ongeldig getal: ' + label + '=' + repr(value)) from exc
    if not math.isfinite(result):
        raise ValueError('NoData/niet-eindig: ' + label)
    return result


def close(a, b, label):
    if not math.isclose(a, b, rel_tol=2e-9, abs_tol=2e-6):
        raise ValueError('{}: {} != {}'.format(label, a, b))


def sid(value):
    if not re.fullmatch(r'[1-9][0-9]*', str(value).strip()):
        raise ValueError('Ongeldig SVAT-ID: ' + repr(value))
    return int(value)


def native_depth(volume_period, area):
    if area <= 0 or not math.isfinite(area):
        raise ValueError('Oppervlak moet positief en eindig zijn')
    return volume_period * 1000.0 / (YEARS * area)


def gxg_values(g, b, sv):
    # Source fields are cm below ground level. Percentiles never fill GxG.
    for key in ('GHG_cm_mv', 'GLG_cm_mv', 'GW5', 'GW95'):
        raw = num(g.get(key), key + ' SVAT ' + str(sv))
        if raw == -9999 or abs(raw) >= 1e20:
            raise ValueError('NoData GxG: ' + key + ' SVAT ' + str(sv))
    ghg = num(g.get('GHG_cm_mv'), 'GHG_cm_mv SVAT ' + str(sv)) / 100.0
    glg = num(g.get('GLG_cm_mv'), 'GLG_cm_mv SVAT ' + str(sv)) / 100.0
    if ghg > glg + 1e-9:
        raise ValueError('GHG dieper dan GLG voor SVAT ' + str(sv))
    values = {'GHG': ghg, 'GLG': glg, 'GG': (ghg + glg) / 2, 'Dynamiek': glg - ghg,
              'GW5': num(g.get('GW5'), 'GW5') / 100, 'GW95': num(g.get('GW95'), 'GW95') / 100}
    if values['GW5'] > values['GW95'] + 1e-9:
        raise ValueError('GW5 > GW95 voor SVAT ' + str(sv))
    for key, value in values.items():
        # Missing existing GxG can be filled, but conflicting valid GxG is not overwritten.
        if str(b.get(key, '')).strip():
            close(num(b[key], key), value, '{} SVAT {}'.format(key, sv))
    return values


def flux_groups(a):
    q = {k: num(a[k], k) for k in MF}
    dr = [q['RIV_SYS1_ONTWATERING_m3'] + q['RIV_SYS4_ONTWATERING_m3'],
          q['RIV_SYS2_ONTWATERING_m3'], q['RIV_SYS3_ONTWATERING_m3'],
          q['DRN_SYS1_ONTWATERING_m3'], q['DRN_SYS2_ONTWATERING_m3'] + q['DRN_SYS3_ONTWATERING_m3']]
    inf = [q['RIV_SYS1_INFILTRATIE_m3'] + q['RIV_SYS4_INFILTRATIE_m3'],
           q['RIV_SYS2_INFILTRATIE_m3'], q['RIV_SYS3_INFILTRATIE_m3']]
    out = {'Ontwatering': sum(dr), 'Infiltratie': sum(inf),
           'Netto kwel/wegzijging': q['FLF_KWEL_m3'] - q['FLF_WEGZIJGING_m3'],
           'Laterale stroming (netto)': q['LAT_NETTO_m3'],
           'Onttrekkingen (laag 1)': q['WEL_NETTO_m3'], 'General head boundary': q['GHB_NETTO_m3'],
           'Wegzijging': q['FLF_WEGZIJGING_m3'], 'Kwel': q['FLF_KWEL_m3']}
    out.update({'Fldrou' + str(i + 1): v for i, v in enumerate(dr)})
    out.update(dict(zip(['Fldrin1', 'Fldrin2', 'Fldrin345'], inf)))
    return out


def audit_columns(headers):
    columns = []
    for h in headers:
        columns.append(h)
        if h == 'Opp_svat_m2':
            columns += ['Opp_MODFLOW_cel_m2', 'GLG_m_mv', 'GHG_m_mv', 'GG_m_mv', 'Dynamiek_m']
        if h in MF:
            stem = h[:-3]
            columns += [stem + '_m3_per_jaar_MFcel', stem + '_mm_per_jaar_MFcel',
                        stem + '_mm_per_jaar_MSW_equivalent']
        if h.endswith('_signed_mm_per_year') and h[:-19] in MSW:
            columns.append(h[:-19] + '_signed_m3_per_jaar_MSW')
        if h in ('MetaSWAP_QModF_signed_mm_j', 'MSW_7term_afwijking_mm_j'):
            columns.append(h.replace('_mm_j', '_m3_per_jaar_MSW'))
        if h == 'Overall_onverklaard_volume_m3_per_j_cel':
            columns += ['Overall_onverklaard_mm_per_jaar_MFcel', 'Overall_onverklaard_mm_per_jaar_MSW_equivalent']
    if len(columns) != len(set(columns)):
        raise ValueError('Uitvoerkolommen audit niet uniek; dit is mogelijk al een verrijkte versie')
    return columns


def enrich(b, a, g):
    sv = sid(b['SVAT/HRU'])
    if sid(a['SVAT']) != sv or sid(g['SVAT']) != sv:
        raise ValueError('SVAT-join mismatch')
    area = num(a['Opp_svat_m2'], 'Opp_svat_m2')
    if area <= 0:
        raise ValueError('Geen positief MetaSWAP-oppervlak voor SVAT ' + str(sv))
    close(area, num(b['Opp_svat/hru'], 'Opp_svat/hru'), 'Oppervlakte')
    gw = gxg_values(g, b, sv)
    groups = flux_groups(a)
    merged = dict(b)
    merged.update(gw)
    # Enriched audit retains original columns and values byte-for-value after CSV parsing.
    qa = dict(a)
    qa.update({'Opp_MODFLOW_cel_m2': CELL_M2, 'GLG_m_mv': gw['GLG'], 'GHG_m_mv': gw['GHG'],
               'GG_m_mv': gw['GG'], 'Dynamiek_m': gw['Dynamiek']})
    for h in MF:
        stem, volume = h[:-3], num(a[h], h)
        qa[stem + '_m3_per_jaar_MFcel'] = volume / YEARS
        qa[stem + '_mm_per_jaar_MFcel'] = native_depth(volume, CELL_M2)
        qa[stem + '_mm_per_jaar_MSW_equivalent'] = native_depth(volume, area)
    for stem in MSW:
        key = stem + '_signed_mm_per_year'
        qa[stem + '_signed_m3_per_jaar_MSW'] = num(a[key], key) * area / 1000
    for key in ('MetaSWAP_QModF_signed_mm_j', 'MSW_7term_afwijking_mm_j'):
        qa[key.replace('_mm_j', '_m3_per_jaar_MSW')] = num(a[key], key) * area / 1000
    overall = num(a['Overall_onverklaard_volume_m3_per_j_cel'], 'Overall volume')
    qa['Overall_onverklaard_mm_per_jaar_MFcel'] = overall * 1000 / CELL_M2
    qa['Overall_onverklaard_mm_per_jaar_MSW_equivalent'] = overall * 1000 / area
    close(num(b[OVERALL], OVERALL), overall * 1000 / CELL_M2, 'Overall')
    # Source reconciliation detects accidentally joining different exports.
    close(num(b['QModF'], 'QModF'), num(a['MetaSWAP_QModF_signed_mm_j'], 'QModF audit'), 'QModF')
    close(num(b['Bergingsverandering (MetaSWAP)'], 'Berging'), num(a['bdgdecstot_signed_mm_per_year'], 'decstot'), 'Berging')
    close(num(b['Waterbalansafwijking MetaSWAP'], 'MSW7'), num(a['MSW_7term_afwijking_mm_j'], 'MSW7 audit'), 'MSW7')
    output = {}
    for h, value in merged.items():
        if h == 'SVAT/HRU':
            output['SVAT'] = str(sv)
        elif h == 'Opp_svat/hru':
            output['Opp_MetaSWAP_m2'] = area
            output['Opp_MODFLOW_cel_m2'] = CELL_M2
            output['X_RD_m'] = num(a['X_RD'], 'X_RD')
            output['Y_RD_m'] = num(a['Y_RD'], 'Y_RD')
        elif h in GW:
            output[h + ('_m' if h == 'Dynamiek' else '_m_mv')] = gw[h]
        elif h in MSW_FIELDS:
            depth = num(value, h)
            output[h + ' [mm/jaar MetaSWAP]'] = depth
            output[h + ' [m3/jaar MetaSWAP]'] = depth * area / 1000
        elif h in MF_FIELDS:
            volume = groups[h]
            close(num(value, h), native_depth(volume, CELL_M2), h)
            output[h + ' [mm/jaar MFcel]'] = native_depth(volume, CELL_M2)
            output[h + ' [mm/jaar MSW-equivalent]'] = native_depth(volume, area)
            output[h + ' [m3/jaar MFcel]'] = volume / YEARS
        elif h == OVERALL:
            output['Onverklaard saldo [mm/jaar MFcel]'] = overall * 1000 / CELL_M2
            output['Onverklaard saldo [mm/jaar MSW-equivalent]'] = overall * 1000 / area
            output['Onverklaard saldo [m3/jaar celboekhouding]'] = overall
        else:
            output[h] = value
    return output, qa


def load_csv(db, table, path, idcol, required, expected):
    with path.open(encoding='utf-8-sig', newline='') as f:
        sample = f.read(8192); f.seek(0)
        delimiter = ';' if sample.splitlines()[0].count(';') > sample.splitlines()[0].count(',') else ','
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(required) <= set(headers):
            raise ValueError('{}: ontbrekende/dubbele kolommen: {}'.format(table, sorted(set(required) - set(headers))))
        db.execute('CREATE TABLE ' + table + '(svat INTEGER PRIMARY KEY, seq INTEGER, payload TEXT NOT NULL)')
        batch, count = [], 0
        for count, row in enumerate(reader, 1):
            if None in row or any(v is None for v in row.values()):
                raise ValueError('{}: onjuist aantal velden op rij {}'.format(table, count))
            batch.append((sid(row[idcol]), count, json.dumps(row, ensure_ascii=False)))
            if len(batch) == 5000:
                db.executemany('INSERT INTO ' + table + ' VALUES (?,?,?)', batch); batch.clear()
        if batch:
            db.executemany('INSERT INTO ' + table + ' VALUES (?,?,?)', batch)
        db.commit()
    if count != expected:
        raise ValueError('{}: {} SVATs, verwacht {}'.format(table, count, expected))
    print('BRON', table, count, flush=True)
    return headers


def formatted(row, human=False):
    result = {}
    for k, v in row.items():
        if isinstance(v, float):
            if not math.isfinite(v):
                raise ValueError('Niet-eindige berekening: ' + k)
            if human:
                s = format(v, '.3f')
                if s == '-0.000': s = '0.000'
                result[k] = s.replace('.', ',')
            else:
                result[k] = format(v, '.17g')
        else:
            result[k] = v
    return result


def execute(args):
    paths = {k: Path(getattr(args, k)) for k in ('base', 'audit', 'gxg', 'manifest')}
    for p in paths.values():
        if not p.is_file(): raise FileNotFoundError(str(p))
    if args.expected <= 0: raise ValueError('expected moet positief zijn')
    original = json.loads(paths['manifest'].read_text(encoding='utf-8-sig'))
    if original.get('period') != '1991-2020' or original.get('count') != args.expected:
        raise ValueError('Manifestperiode/populatie komt niet overeen')
    hashes = {k: sha256(v) for k, v in paths.items()}
    checks = {'base': original.get('outputs', {}).get('table_sha256'),
              'audit': original.get('outputs', {}).get('audit_sha256'),
              'gxg': original.get('sources', {}).get('gxg', {}).get('sha256')}
    for k, value in checks.items():
        if value != hashes[k]: raise ValueError('Bronhash wijkt af van manifest: ' + k)
    out = Path(args.out)
    if out.exists(): raise FileExistsError('Uitvoermap bestaat al; niet overschreven: ' + str(out))
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = out.parent / (out.name + '.lock')
    fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    try:
        with tempfile.TemporaryDirectory(prefix=out.name + '.partial_', dir=str(out.parent)) as td:
            stage = Path(td)
            with sqlite3.connect(str(stage / 'join.sqlite')) as db:
                db.execute('PRAGMA journal_mode=OFF'); db.execute('PRAGMA synchronous=OFF')
                base_required = ['SVAT/HRU', 'Opp_svat/hru', *MSW_FIELDS, *MF_FIELDS, OVERALL]
                audit_required = ['SVAT', 'Opp_svat_m2', 'X_RD', 'Y_RD', *MF,
                    *[s + '_signed_mm_per_year' for s in MSW], 'MetaSWAP_QModF_signed_mm_j',
                    'MSW_7term_afwijking_mm_j', 'Overall_onverklaard_volume_m3_per_j_cel']
                headers = load_csv(db, 'base', paths['base'], 'SVAT/HRU', base_required, args.expected)
                ah = load_csv(db, 'audit', paths['audit'], 'SVAT', audit_required, args.expected)
                load_csv(db, 'gxg', paths['gxg'], 'SVAT', ['SVAT', 'GHG_cm_mv', 'GLG_cm_mv', 'GW5', 'GW95'], args.expected)
                for table in ('audit', 'gxg'):
                    missing = db.execute('SELECT b.svat FROM base b LEFT JOIN ' + table +
                        ' t ON b.svat=t.svat WHERE t.svat IS NULL LIMIT 5').fetchall()
                    if missing: raise ValueError('SVATs ontbreken in {}: {}'.format(table, missing))
                # Ensure groundwater fields are grouped even if the original table omitted them.
                headers = [h for h in headers if h not in GW]
                at = headers.index('Kwelklasse4') if 'Kwelklasse4' in headers else headers.index(MSW_FIELDS[0])
                headers[at:at] = GW
                cols = audit_columns(ah)
                from contextlib import ExitStack
                with ExitStack() as stack:
                    fh = stack.enter_context((stage / READ_NAME).open('w', encoding='utf-8-sig', newline=''))
                    ft = stack.enter_context((stage / TECH_NAME).open('w', encoding='utf-8', newline=''))
                    fa = stack.enter_context((stage / AUDIT_NAME).open('w', encoding='utf-8', newline=''))
                    wa = csv.DictWriter(fa, fieldnames=cols, extrasaction='raise'); wa.writeheader()
                    wh = wt = None; count = 0
                    query = 'SELECT b.payload,a.payload,g.payload FROM base b JOIN audit a ON b.svat=a.svat JOIN gxg g ON b.svat=g.svat ORDER BY b.seq'
                    for bx, ax, gx in db.execute(query):
                        raw_b, a, g = json.loads(bx), json.loads(ax), json.loads(gx)
                        b = {h: raw_b.get(h, '') for h in headers}
                        row, qa = enrich(b, a, g)
                        if wh is None:
                            wh = csv.DictWriter(fh, fieldnames=list(row), delimiter=';'); wh.writeheader()
                            wt = csv.DictWriter(ft, fieldnames=list(row)); wt.writeheader()
                        wh.writerow(formatted(row, human=True)); wt.writerow(formatted(row)); wa.writerow(formatted(qa))
                        count += 1
                        if count % 100000 == 0: print('VERWERKT', count, flush=True)
                    if count != args.expected: raise ValueError('Onvolledige join')
                dictionary = {
                    'period': '1991-2020', 'years': YEARS, 'm3_in_original_MF_audit': 'total over 30 calendar years per full MODFLOW cell',
                    'm3_per_year': 'period volume / 30; not divided by 30 again',
                    'mm_per_year_MFcel': '1000 * V_period / (30 * 62500)',
                    'mm_per_year_MSW_equivalent': '1000 * V_period / (30 * Opp_svat_m2); full MF-cell volume, re-expressed on SVAT area, NOT apportioned',
                    'mm_per_year_MetaSWAP': 'original annual depth on represented MetaSWAP SVAT area',
                    'm3_per_year_MetaSWAP': 'original annual depth * Opp_svat_m2 / 1000',
                    'GxG': 'source GHG_cm_mv and GLG_cm_mv /100; no replacement by GW5/GW95',
                    'GG': '(GHG+GLG)/2 per owner decision 2026-11-06, not time-series mean',
                    'groundwater_sign': 'metres below surface, positive downward; negative above surface is permitted',
                    'signs': 'unchanged from original; positive gross drainage volumes remain positive; signed terms remain signed',
                    'legacy_audit_columns': ah, 'new_audit_columns': [h for h in cols if h not in ah],
                    'precision': 'human CSV 3 decimals, semicolon and decimal comma; technical CSV float64 full roundtrip precision',
                    'warning': 'Do not sum repeated full-MF-cell volumes over SVATs. No physical closure claimed; MSW7 and overall are unchanged diagnostics.',
                }
                (stage / 'KOLOMMEN_EN_EENHEDEN.json').write_text(json.dumps(dictionary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            db.close()
            (stage / 'join.sqlite').unlink()
            for k, p in paths.items():
                if sha256(p) != hashes[k]: raise ValueError('Bron gewijzigd tijdens verwerking: ' + k)
            manifest = {'status': 'COMPLETED_PRESENTATION_ENRICHMENT_NOT_NEW_PHYSICAL_CLOSURE',
                'count': count, 'period': '1991-2020', 'expected_svats': args.expected,
                'source_code_sha256': sha256(Path(__file__)), 'sources': {k: {'path': str(v), 'sha256': hashes[k]} for k, v in paths.items()},
                'source_file_mutations': 0, 'gxg_percentile_substitution': False,
                'outputs': {name: {'path': str(out / name), 'sha256': sha256(stage / name)}
                            for name in (READ_NAME, TECH_NAME, AUDIT_NAME, 'KOLOMMEN_EN_EENHEDEN.json')}}
            (stage / 'MANIFEST_FRANK_LEESBAAR_V02.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            if out.exists(): raise FileExistsError(str(out))
            stage.rename(out)
    finally:
        lock.unlink()
    print('GEREED:', out / READ_NAME, 'SVATs:', count, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name, default in DEFAULTS.items(): p.add_argument('--' + name, type=Path, default=default)
    p.add_argument('--expected', type=int, default=645582)
    try:
        execute(p.parse_args())
    except Exception as exc:
        print('STOP FRANK LEESBAAR:', str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
