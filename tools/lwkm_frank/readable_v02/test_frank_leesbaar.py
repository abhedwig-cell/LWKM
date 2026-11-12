"""Synthetic tests only. No historical server data used."""
import argparse
import contextlib
import csv
import io
import json
import math
import tempfile
import unittest
from pathlib import Path
import maak_frank_leesbaar as m


def rows(sv=1, area=12500):
    a = {'SVAT': str(sv), 'Opp_svat_m2': str(area), 'X_RD': '149625', 'Y_RD': '496625',
         'GG_14_28_gemiddeld_cm_mv': '107', 'GVG_cm_mv': '60', 'GW5_cm_mv': '10', 'GW95_cm_mv': '250',
         'LU7': '1', 'Meteoregio_nm': 'a; b, c', 'MetaSWAP_signed_som6_mm_j': '12.5',
         'MetaSWAP_QModF_signed_mm_j': '1.5', 'MSW_7term_afwijking_mm_j': '14',
         'Overall_onverklaard_volume_m3_per_j_cel': '-200',
         'Flux_ruimtebasis': 'MF_FUL_62500m2_plus_MSW_ARK',
         'Balans_interpretatie': 'DIAGNOSTISCH_ZONDER_MODFLOW_STORAGE_OF_BND'}
    a.update({k: str((i + 1) * 30000) for i, k in enumerate(m.MF)})
    a['WEL_NETTO_m3'] = '-9999'  # valid physical volume, NOT a NoData marker
    a['LAT_NETTO_m3'] = '-30000'
    a.update({v + '_signed_mm_per_year': str(x) for v, x in zip(m.MSW, [-10, 800, 10, 20, -700, -107.5])})
    a['MSW_ET_componentensom_mm_j'] = '700'; a['MSW_ET_verschil_mm_j'] = '0'
    b = {'SVAT/HRU': str(sv), 'Gebied': '', 'N': '1', 'Opp_svat/hru': str(area),
         'Landuse LHM (22)': '1', 'Landuse ANIMO (4 tekst)': 'gras',
         'LU4': '1', 'LU2': '1', 'Bodem370': '248', 'Bodem79': '71', 'Pawn21': '15',
         'Grondsoort4': '3', 'Grondsoort2': '1', 'Gtnr': '7',
         'GLG': '1.8', 'GHG': '0.4', 'GG': '1.1', 'Dynamiek': '1.4',
         'GW5': '0.1', 'GW95': '2.5', 'Kwelklasse4': '2'}
    b.update({f: str(i + 1) for i, f in enumerate(m.MSW_FIELDS)})
    b.update({'Neerslag': '800', 'Beregening': '30', 'Evapotranspiratie': '700',
              'Verdamping gewas': '500', 'Verdamping interceptie': '100', 'Verdamping bodem': '100',
              'Oppervlakkige afstroming': '107.5', 'QModF': '1.5',
              'Bergingsverandering (MetaSWAP)': '-10', 'Waterbalansafwijking MetaSWAP': '14'})
    b.update({k: format(m.native_depth(v, m.CELL_M2), '.12g') for k, v in m.flux_groups(a).items()})
    b[m.OVERALL] = '-3.2'; b['Indicator gecorrigeerd/vervangen SVAT'] = ''
    g = {'SVAT': str(sv), 'GHG_cm_mv': '40', 'GLG_cm_mv': '180', 'GW5': '10', 'GW95': '250'}
    return b, a, g


def write_csv(path, data, delimiter=','):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]), delimiter=delimiter); w.writeheader(); w.writerows(data)


def fixture(d, missing_gxg=False, delimiter=','):
    b, a, g = rows(1); b2, a2, g2 = rows(2, area=62500)
    if missing_gxg:
        for bb in (b, b2):
            for key in ('GLG', 'GHG', 'GG', 'Dynamiek'): bb.pop(key)
    paths = {k: d / (k + '.csv') for k in ('base', 'audit', 'gxg')}
    write_csv(paths['base'], [b, b2], delimiter)
    write_csv(paths['audit'], [a2, a], delimiter)  # different source order by design
    write_csv(paths['gxg'], [g2, g], delimiter)
    manifest = d / 'manifest.json'
    manifest.write_text(json.dumps({'period': '1991-2020', 'count': 2,
        'outputs': {'table_sha256': m.sha256(paths['base']), 'audit_sha256': m.sha256(paths['audit'])},
        'sources': {'gxg': {'sha256': m.sha256(paths['gxg'])}}}))
    return argparse.Namespace(**paths, manifest=manifest, out=d / 'out', expected=2)


class NumericTests(unittest.TestCase):
    def test_period_factor_30(self):
        self.assertEqual(m.native_depth(30000, 12500), 80)
        self.assertEqual(m.native_depth(30000, 62500), 16)

    def test_signed_volume(self):
        self.assertEqual(m.native_depth(-30000, 12500), -80)
        self.assertEqual(m.num('-9999', 'physical flux'), -9999)

    def test_zero_negative_bad_area(self):
        for a in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError): m.native_depth(30000, a)

    def test_nonfinite_or_blank(self):
        for x in ('', None, 'NaN', 'inf', '-inf', 'a', '1,000.2'):
            with self.assertRaises(ValueError): m.num(x, 'test')

    def test_decimal_comma(self): self.assertEqual(m.num('1,25', 'test'), 1.25)

    def test_true_gxg_not_percentiles(self):
        b, a, g = rows(); o, _ = m.enrich(b, a, g)
        self.assertEqual(o['GHG_m_mv'], .4); self.assertEqual(o['GLG_m_mv'], 1.8)
        self.assertEqual(o['GW5_m_mv'], .1); self.assertEqual(o['GW95_m_mv'], 2.5)
        self.assertEqual(o['GG_m_mv'], 1.1)

    def test_missing_original_gxg_is_added(self):
        b, a, g = rows(); b.pop('GHG'); b['GLG'] = ''
        o, _ = m.enrich(b, a, g)
        self.assertEqual(o['GHG_m_mv'], .4); self.assertEqual(o['GLG_m_mv'], 1.8)

    def test_no_percentile_fallback(self):
        b, a, g = rows(); g.pop('GHG_cm_mv')
        with self.assertRaises(ValueError): m.enrich(b, a, g)

    def test_bad_gxg(self):
        for value in ('-9999', '1e30', 'inf', ''):
            b, a, g = rows(); g['GLG_cm_mv'] = value
            with self.assertRaises(ValueError): m.enrich(b, a, g)

    def test_inconsistent_existing_gxg(self):
        b, a, g = rows(); b['GHG'] = '0.1'
        with self.assertRaises(ValueError): m.enrich(b, a, g)

    def test_above_surface_allowed(self):
        b, a, g = rows(); b['GHG'] = ''; b['GG'] = ''; b['Dynamiek'] = ''; g['GHG_cm_mv'] = '-10'
        o, _ = m.enrich(b, a, g); self.assertEqual(o['GHG_m_mv'], -.1)

    def test_gxg_order(self):
        b, a, g = rows(); g['GHG_cm_mv'] = '200'
        with self.assertRaises(ValueError): m.enrich(b, a, g)

    def test_area_consistency(self):
        b, a, g = rows(); b['Opp_svat/hru'] = '13000'
        with self.assertRaises(ValueError): m.enrich(b, a, g)

    def test_msw_to_volume_uses_svat_area(self):
        b, a, g = rows(); o, _ = m.enrich(b, a, g)
        self.assertEqual(o['Neerslag [m3/jaar MetaSWAP]'], 10000)
        self.assertEqual(o['Neerslag [mm/jaar MetaSWAP]'], 800)

    def test_mf_not_apportioned(self):
        b, a, g = rows(); _, q = m.enrich(b, a, g)
        s = 'RIV_SYS1_ONTWATERING'
        self.assertEqual(q[s + '_m3'], '30000')
        self.assertEqual(q[s + '_m3_per_jaar_MFcel'], 1000)
        self.assertEqual(q[s + '_mm_per_jaar_MFcel'], 16)
        self.assertEqual(q[s + '_mm_per_jaar_MSW_equivalent'], 80)

    def test_all_audit_original_fields_retained(self):
        b, a, g = rows(); _, q = m.enrich(b, a, g)
        for key, value in a.items(): self.assertEqual(q[key], value)
        self.assertEqual(set(m.audit_columns(list(a))), set(q))

    def test_annual_overall_not_divided_again(self):
        b, a, g = rows(); o, q = m.enrich(b, a, g)
        self.assertEqual(o['Onverklaard saldo [mm/jaar MSW-equivalent]'], -16)
        self.assertEqual(q['Overall_onverklaard_mm_per_jaar_MFcel'], -3.2)

    def test_adjacency(self):
        b, a, g = rows(); cols = m.audit_columns(list(a)); at = cols.index('RIV_SYS1_ONTWATERING_m3')
        self.assertEqual(cols[at + 3], 'RIV_SYS1_ONTWATERING_mm_per_jaar_MSW_equivalent')

    def test_mapping_primary_plus_h1_and_drains(self):
        _, a, _ = rows(); p = m.flux_groups(a)
        self.assertEqual(p['Fldrou1'], float(a['RIV_SYS1_ONTWATERING_m3']) + float(a['RIV_SYS4_ONTWATERING_m3']))
        self.assertEqual(p['Fldrou5'], float(a['DRN_SYS2_ONTWATERING_m3']) + float(a['DRN_SYS3_ONTWATERING_m3']))
        self.assertEqual(p['Ontwatering'], sum(p['Fldrou'+str(i)] for i in range(1, 6)))

    def test_display_locale_and_negative_zero(self):
        self.assertEqual(m.formatted({'a': 12.3456, 'b': -0.00001}, True), {'a':'12,346', 'b':'0,000'})

    def test_invalid_svat_id(self):
        for x in ('0', '-1', '1.0', '', None):
            with self.assertRaises(ValueError): m.sid(x)


class FileTests(unittest.TestCase):
    def run_fixture(self, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            args = fixture(Path(tmp), **kwargs)
            before = {k: m.sha256(getattr(args,k)) for k in ('base','audit','gxg','manifest')}
            with contextlib.redirect_stdout(io.StringIO()): m.execute(args)
            for k, h in before.items(): self.assertEqual(m.sha256(getattr(args,k)), h)
            with (args.out / m.READ_NAME).open(encoding='utf-8-sig', newline='') as f:
                r = csv.DictReader(f, delimiter=';'); headers = r.fieldnames; data = list(r)
            self.assertEqual([x['SVAT'] for x in data], ['1','2'])
            self.assertEqual(data[0]['GHG_m_mv'], '0,400')
            self.assertEqual(data[0]['GLG_m_mv'], '1,800')
            self.assertEqual(data[0]['GW5_m_mv'], '0,100')
            self.assertEqual(data[0]['Neerslag [m3/jaar MetaSWAP]'], '10000,000')
            self.assertLess(headers.index('GLG_m_mv'), headers.index('GW5_m_mv'))
            manifest = json.loads((args.out / 'MANIFEST_FRANK_LEESBAAR_V02.json').read_text())
            self.assertEqual(manifest['count'], 2)
            self.assertFalse(manifest['gxg_percentile_substitution'])
            for info in manifest['outputs'].values(): self.assertEqual(m.sha256(Path(info['path'])), info['sha256'])
            self.assertFalse((args.out.parent / 'out.lock').exists())
            self.assertFalse((args.out / 'join.sqlite').exists())

    def test_end_to_end_shuffled_ids_and_source_hashes(self): self.run_fixture()
    def test_missing_gxg_columns_filled_end_to_end(self): self.run_fixture(missing_gxg=True)
    def test_semicolon_input(self): self.run_fixture(delimiter=';')

    def test_manifest_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = fixture(Path(tmp)); a.base.write_text(a.base.read_text() + '\n')
            with self.assertRaises(ValueError): m.execute(a)
            self.assertFalse(a.out.exists())

    def test_existing_output_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = fixture(Path(tmp)); a.out.mkdir(); f = a.out / 'keep.txt'; f.write_text('keep')
            with self.assertRaises(FileExistsError): m.execute(a)
            self.assertEqual(f.read_text(), 'keep')

    def test_duplicate_svat_is_rejected(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'a.csv'; write_csv(p, [{'SVAT':'1'}, {'SVAT':'1'}])
            with sqlite3.connect(':memory:') as db:
                with self.assertRaises(sqlite3.IntegrityError): m.load_csv(db,'a',p,'SVAT',['SVAT'],2)

    def test_join_mismatch_no_partial_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = fixture(Path(tmp)); g = rows(3)[2]; g2 = rows(2)[2]
            write_csv(a.gxg, [g, g2]); man = json.loads(a.manifest.read_text())
            man['sources']['gxg']['sha256'] = m.sha256(a.gxg); a.manifest.write_text(json.dumps(man))
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError): m.execute(a)
            self.assertFalse(a.out.exists()); self.assertFalse((a.out.parent / 'out.lock').exists())
            self.assertEqual(list(a.out.parent.glob('out.partial_*')), [])

    def test_period_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = fixture(Path(tmp)); man = json.loads(a.manifest.read_text()); man['period']='2011-2020'; a.manifest.write_text(json.dumps(man))
            with self.assertRaises(ValueError): m.execute(a)

if __name__ == '__main__': unittest.main(verbosity=2)
