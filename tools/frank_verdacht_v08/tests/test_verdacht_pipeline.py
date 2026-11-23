"""Volledige kleine v07-bron -> vier donorvarianten en veilige publicatie."""
import argparse
import csv
import gzip
import io
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import frank_verdacht as pipeline
from donor_bindings import (DATA_NAME, SOURCE_NAME, HEADERS as DONOR_HEADERS,
                            QUALIFICATION_FLAGS)
from donor_profile import HYDRO_COLUMNS, PRESERVED_COLUMNS
from frank_io import sha
from schema import AREA, COUNT, FLAG, HEADERS, ID, NET, NUMERIC_COLUMNS, P5, P95, REGION


def write_csv(path, headers, rows):
    with Path(path).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, headers, delimiter=',')
        writer.writeheader()
        writer.writerows(rows)


def write_gzip_csv(path, headers, rows):
    with Path(path).open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as packed:
            with io.TextIOWrapper(packed, encoding='utf-8', newline='') as text:
                writer = csv.DictWriter(text, headers, delimiter=',', lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)


def read_rows(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter=','))


def row_map(path):
    return {int(row[ID]): row for row in read_rows(path)}


def tree_bytes(path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in Path(path).rglob('*') if p.is_file()}


def original_row(sid, area, kwel):
    row = {name: '0' for name in HEADERS}
    ghg = 0.2 + sid / 10.0
    glg = ghg + 1.0
    row.update({ID: str(sid), COUNT: '1', AREA: str(area), FLAG: '0',
        'Landuse LHM (22)': str(sid), 'Landuse ANIMO (4 tekst)': 'gras',
        'LU4': '1', 'LU2': '1', 'Bodem370': str(180 + sid),
        'Bodem79': str(40 + sid), 'Pawn21': str(sid),
        'Grondsoort4': str(1 + sid % 3), 'Grondsoort 2': str(1 + sid % 2),
        'Gtnr': {1: '3', 2: '7', 3: '4', 4: '6', 5: '6'}[sid],
        'GLG m-mv': format(glg, '.12g'), 'GHG m-mv': format(ghg, '.12g'),
        'GG ((GHG+GLG)/2)': format((ghg + glg) / 2, '.12g'),
        'Dynamiek (GLG-GHG)': '1', P5: format(ghg - 0.15, '.12g'),
        P95: format(glg + 0.25, '.12g'),
        'Kwelklasse4': '4' if sid == 1 else '2', REGION: str(10 + sid)})
    flow = {'Neerslag (mm/j)': 700 + 100 * sid, 'Beregening': 10 * sid,
        'Evapotranspiratie': 400 * sid, 'Verdamping gewas': 280 * sid,
        'verdamping interceptie': 50 * sid, 'Verdamping bodem': 70 * sid,
        'Oppervlakkige afstroming': 5 * sid, 'Ontwatering': 65 * sid,
        'Fldrou1': 30 * sid, 'Fldrou2': 20 * sid, 'Fldrou3': 10 * sid,
        'Fldrou4': 3 * sid, 'Fldrou5': 2 * sid, 'Infiltratie': 7 * sid,
        'Fldrin1': 4 * sid, 'Fldrin2': 2 * sid, 'Fldrin345': sid,
        NET: kwel - 2 * sid, 'Laterale stroming (netto)': -12 * sid,
        'Onttrekkingen (uit laag 1)': sid, 'General head boundary': -3 * sid,
        'Wegzijging': 2 * sid, 'Kwel': kwel, 'QModF': -40 * sid,
        'Bergingsverandering (MetaSWAP)': 0.2 * sid,
        'Waterbalansfout MetaSWAP': 0.01 * sid,
        'Waterbalansfout overall': 0.1 * sid}
    row.update({name: format(value, '.12g') for name, value in flow.items()})
    return row


class CompleteFixture:
    """Een verdachte target, een geldige nonself-target en drie zelfdonoren."""

    def __init__(self, root):
        self.root = Path(root)
        self.source = self.root / 'v07_complete'
        self.data = self.root / 'data'
        self.output = self.root / 'v08_result'
        self.source.mkdir()
        self.data.mkdir()
        self.membership = {1: 10, 2: 10, 3: 10, 4: 20, 5: 20}
        self.areas = {1: 25000, 2: 75000, 3: 50000, 4: 25000, 5: 87500}
        self.raw = {sid: original_row(sid, self.areas[sid], kwel)
                    for sid, kwel in ((1, 10), (2, 100), (3, 30), (4, 20), (5, 40))}
        self.raw[1]['Waterbalansfout overall'] = ''
        self.corrected = {sid: dict(row) for sid, row in self.raw.items()}
        for sid, delta in ((1, 4), (5, 2)):
            row = self.corrected[sid]
            row['Kwel'] = format(float(row['Kwel']) - delta, '.12g')
            row[NET] = format(float(row[NET]) - delta, '.12g')
            row['Fldrin1'] = format(float(row['Fldrin1']) + delta, '.12g')
            row['Infiltratie'] = format(float(row['Infiltratie']) + delta, '.12g')
            row['Kwelklasse4'] = '2'
            row[FLAG] = '1'
        self.write_data()
        self.write_source()

    def write_data(self):
        memberships = [{'svat': str(sid), 'HRU': str(hru),
                        'x': str(125 + sid * 250), 'y': '300125',
                        # Historisch oppervlak is bewust anders dan actueel.
                        'svat_area_m2': '50000'}
                       for sid, hru in self.membership.items()]
        schemas = [{'HRU': '10', 'N': '3', 'svat_repr': '1'},
                   {'HRU': '20', 'N': '2', 'svat_repr': '4'}]
        write_gzip_csv(self.data / 'SVAT_HRU.csv.gz',
                       ['svat', 'HRU', 'x', 'y', 'svat_area_m2'], memberships)
        write_gzip_csv(self.data / 'HRU_SCHEMA.csv.gz', ['HRU', 'N', 'svat_repr'], schemas)
        self.old_sources = {'outputs': {name: {'sha256': sha(self.data / name)}
            for name in ('SVAT_HRU.csv.gz', 'HRU_SCHEMA.csv.gz')},
            'checks': {'membership_rows': 5, 'unique_hrus': 2}}
        (self.data / 'SOURCES.json').write_text(json.dumps(self.old_sources), encoding='utf-8')
        rows = []
        for sid, hru in self.membership.items():
            rows.append({'svat': str(sid), 'HRU': str(hru),
                'hru_cluster_donor_svat': '1' if sid in (2, 3) else str(sid),
                'is_suspect': '1' if sid == 2 else '0',
                'qualification_reason_ids': 'ghg_sel|kwel_sel' if sid == 2 else '',
                'label': 'Toegevoegd' if sid in (2, 3) else 'valid'})
        write_gzip_csv(self.data / DATA_NAME, DONOR_HEADERS, rows)
        metadata = {'schema_version': 1, 'headers': DONOR_HEADERS,
            'qualification_flags': list(QUALIFICATION_FLAGS),
            'outputs': {DATA_NAME: {'sha256': sha(self.data / DATA_NAME),
                                  'size_bytes': (self.data / DATA_NAME).stat().st_size}},
            'checks': {'membership_rows': 5, 'unique_hrus': 2,
                'suspect_svats': 1, 'nonsuspect_svats': 4, 'nonself_donors': 2,
                'suspect_nonself_svats': 1, 'nonsuspect_nonself_svats': 1,
                'self_donors': 3,
                'qualification_flag_counts': {name: int(name in ('ghg_sel', 'kwel_sel'))
                                              for name in QUALIFICATION_FLAGS}}}
        (self.data / SOURCE_NAME).write_text(json.dumps(metadata), encoding='utf-8')

    def source_hru_rows(self, records):
        result = []
        for hru in (10, 20):
            rows = [records[sid] for sid in self.membership if self.membership[sid] == hru]
            area = sum(float(row[AREA]) for row in rows)
            output = dict(rows[0])
            output.update({ID: str(hru), COUNT: str(len(rows)), AREA: str(area),
                           FLAG: '1' if any(row[FLAG] == '1' for row in rows) else '0',
                           REGION: '|'.join(sorted({row[REGION] for row in rows})),
                           'Gtnr': '8'})  # Oude schemacategorie mag niet overheersen.
            for field in NUMERIC_COLUMNS:
                output[field] = '' if any(row[field] == '' for row in rows) else format(
                    math.fsum(float(row[field]) * float(row[AREA]) for row in rows) / area, '.15g')
            result.append(output)
        return result

    def write_source(self):
        outputs = {}
        for variant, rows in zip(pipeline.VARIANTS, (self.raw, self.corrected)):
            write_csv(self.source / variant['source_svat'], HEADERS, rows.values())
            write_csv(self.source / variant['source_hru'], HEADERS, self.source_hru_rows(rows))
            for key, count in (('source_svat', 5), ('source_hru', 2)):
                filename = variant[key]
                outputs[filename] = {'rows': count, 'sha256': sha(self.source / filename)}
        manifest = {'status': 'COMPLETE_BOOKKEEPING_COMPARISON_NOT_NEW_MODEL_RUN',
            'version': '07.1', 'headers': HEADERS, 'delimiter': ',', 'decimal': '.',
            'period': '1991-2020', 'years': 30, 'days': 10958,
            'selection': {'selected_svats': 5, 'hrus': 2},
            'identity': {'sources': {'data': self.old_sources['outputs']}},
            'tables': {'outputs': outputs}}
        (self.source / pipeline.SOURCE_MANIFEST).write_text(json.dumps(manifest), encoding='utf-8')

    def args(self, check_only=False):
        return argparse.Namespace(root=str(self.root), source=str(self.source),
                                  out=str(self.output), data=str(self.data), check_only=check_only)


class VerdachtPipelineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='frank_verdacht_pipeline_')
        self.addCleanup(temporary.cleanup)
        self.fixture = CompleteFixture(Path(temporary.name))
        self.messages = []

    def run_pipeline(self, check_only=False):
        return pipeline.run(self.fixture.args(check_only), progress=self.messages.append)

    def assert_no_partial_output(self):
        self.assertFalse(self.fixture.output.exists())
        self.assertEqual(list(self.fixture.root.glob(self.fixture.output.name + '.gereed_*')), [])
        self.assertFalse((self.fixture.root / 'FRANK_VERDACHT_V08.lock.json').exists())
        self.assertFalse(any(path.suffix in ('.sqlite', '.db') for path in self.fixture.root.rglob('*')))

    def test_four_tables_preserve_targets_and_use_whole_profiles_from_each_variant(self):
        before_source, before_data = tree_bytes(self.fixture.source), tree_bytes(self.fixture.data)
        self.assertEqual(self.run_pipeline(), 0)
        for variant, source in zip(pipeline.VARIANTS, (self.fixture.raw, self.fixture.corrected)):
            with self.subTest(variant=variant['key']):
                svats = row_map(self.fixture.output / variant['svat'])
                hrus = row_map(self.fixture.output / variant['hru'])
                self.assertEqual(set(svats), {1, 2, 3, 4, 5})
                self.assertEqual(set(hrus), {10, 20})
                for key in PRESERVED_COLUMNS:
                    self.assertEqual(svats[2][key], source[2][key], key)
                for key in HYDRO_COLUMNS:
                    self.assertEqual(svats[2][key], source[1][key], key)
                self.assertEqual(svats[2][AREA], '75000')
                self.assertEqual(svats[2][REGION], '12')
                self.assertEqual(svats[2][FLAG], '1')
                self.assertEqual(svats[2]['Waterbalansfout overall'], '')
                self.assertNotEqual(source[2]['Waterbalansfout overall'], '')
                self.assertEqual(svats[3], source[3])  # Nonself is hier niet verdacht.
                self.assertEqual(svats[1], source[1])
                self.assertEqual(svats[5], source[5])
                self.assertEqual(hrus[10][COUNT], '3')
                self.assertEqual(float(hrus[10][AREA]), 150000)
                self.assertEqual(float(hrus[20][AREA]), 112500)
                self.assertEqual(hrus[10]['Gtnr'], '3|4')
                self.assertNotEqual(hrus[10]['Gtnr'], '8')
                self.assertEqual(hrus[10][FLAG], '1')
                self.assertEqual(hrus[10]['Waterbalansfout overall'], '')
                self.assertEqual(hrus[10][REGION], '11|12|13')
                for name in pipeline.STATIC_CATEGORIES:
                    original_hru = row_map(self.fixture.source / variant['source_hru'])[10]
                    self.assertEqual(hrus[10][name], original_hru[name])
                for key in ('svat', 'hru'):
                    with (self.fixture.output / variant[key]).open(encoding='utf-8', newline='') as stream:
                        rows = list(csv.reader(stream, delimiter=','))
                    self.assertEqual(rows[0], HEADERS)
                    self.assertTrue(all(len(row) == 49 for row in rows))
        raw = row_map(self.fixture.output / pipeline.VARIANTS[0]['svat'])
        corrected = row_map(self.fixture.output / pipeline.VARIANTS[1]['svat'])
        self.assertEqual(float(raw[2]['Kwel']), 10)
        self.assertEqual(float(corrected[2]['Kwel']), 6)
        self.assertEqual(float(raw[2]['Fldrin1']), 4)
        self.assertEqual(float(corrected[2]['Fldrin1']), 8)
        self.assertEqual(tree_bytes(self.fixture.source), before_source)
        self.assertEqual(tree_bytes(self.fixture.data), before_data)
        manifest = json.loads((self.fixture.output / pipeline.MANIFEST_NAME).read_text())
        for key in ('ONGECORRIGEERD', 'FLEVOLAND'):
            self.assertEqual(manifest['results'][key]['replaced_svats'], 1)
            self.assertEqual(manifest['results'][key]['retained_nonself_nonsuspect'], 1)
        self.assertEqual(manifest['results']['FLEVOLAND']['replaced_using_flevoland_donor_profile'], 1)
        self.assertEqual(manifest['results']['FLEVOLAND']['replaced_targets_originally_flevoland'], 0)
        for name, record in manifest['files'].items():
            self.assertEqual(sha(self.fixture.output / name), record['sha256'])

    def test_hru_uses_all_target_area_and_reports_mm_and_equivalent_volumes(self):
        self.run_pipeline()
        expected = {'ONGECORRIGEERD': (2500.0, 9250.0, 10.0),
                    'FLEVOLAND': (2100.0, 9150.0, 6.0)}
        for variant in pipeline.VARIANTS:
            new_volume, old_volume, donor_intensity = expected[variant['key']]
            hrus = row_map(self.fixture.output / variant['hru'])
            actual = float(hrus[10]['Kwel'])
            self.assertAlmostEqual(actual, new_volume * 1000 / 150000)
            self.assertNotAlmostEqual(actual, donor_intensity)  # P12 zou alleen donor 1 gebruiken.
            control = self.fixture.output / 'controle'
            rows = read_rows(control / ('HRU_WATERTERMEN_' + variant['key'] + '.csv'))
            kwel = next(r for r in rows if r['HRU'] == '10' and r['Waterterm'] == 'Kwel')
            self.assertAlmostEqual(float(kwel['Na_mm_jaar']), actual)
            self.assertAlmostEqual(float(kwel['Na_m3eq_jaar']), new_volume)
            self.assertAlmostEqual(float(kwel['Voor_m3eq_jaar']), old_volume)
            self.assertAlmostEqual(float(kwel['Verschil_m3eq_jaar']), new_volume - old_volume)
            support = next(r for r in read_rows(control / ('HRU_VERVANGING_' + variant['key'] + '.csv'))
                           if r['HRU'] == '10')
            self.assertEqual(support['N_SVAT'], '3')
            self.assertEqual(support['N_vervangen'], '1')
            self.assertEqual(float(support['Opp_vervangen_m2']), 75000)
            self.assertEqual(float(support['Aandeel_opp_vervangen']), 0.5)
            self.assertEqual(support['N_nietverdacht_met_andere_donor_behouden'], '1')
            self.assertEqual(support['N_P12_donorgelijke_bronleden'], '1')
            self.assertEqual(float(support['Opp_P12_donorgelijke_bronleden_m2']), 25000)
            self.assertEqual(support['P12_selectie_gebruikt_voor_deze_tabel'], '0')
            audit = read_rows(control / ('SVAT_VERVANGING_' + variant['key'] + '.csv'))
            self.assertEqual(len(audit), 1)
            self.assertEqual(audit[0]['SVAT'], '2')
            self.assertEqual(audit[0]['Donor_SVAT'], '1')
            self.assertEqual(audit[0]['Kwalificatieredenen'], 'ghg_sel|kwel_sel')
            self.assertEqual(float(audit[0]['Oppervlakfactor_target_donor']), 3)
            self.assertEqual(audit[0]['Gebied_target'], '12')
            self.assertEqual(audit[0]['Gebied_donor'], '11')
            self.assertEqual(float(audit[0]['X_target_RD']), 625)
            self.assertEqual(float(audit[0]['X_donor_RD']), 375)
            self.assertEqual(float(audit[0]['Y_target_RD']), 300125)
        large = read_rows(self.fixture.output / 'controle/SVAT_OPPERVLAK_BOVEN_62500.csv')
        self.assertEqual({int(row['SVAT']) for row in large}, {2, 5})

    def test_identical_profiles_still_receive_replacement_flag_and_audit(self):
        for records in (self.fixture.raw, self.fixture.corrected):
            for field in HYDRO_COLUMNS:
                records[2][field] = records[1][field]
        self.fixture.corrected[2][FLAG] = '1'
        self.fixture.write_source()
        self.run_pipeline()
        manifest = json.loads((self.fixture.output / pipeline.MANIFEST_NAME).read_text())
        for variant in pipeline.VARIANTS:
            row = row_map(self.fixture.output / variant['svat'])[2]
            self.assertEqual(row[FLAG], '1')
            result = manifest['results'][variant['key']]
            self.assertEqual(result['replaced_svats'], 1)
            self.assertEqual(result['replaced_with_numeric_change'], 0)
            self.assertEqual(result['changed_profile_fields'], {})
            audit = read_rows(self.fixture.output / ('controle/SVAT_VERVANGING_' + variant['key'] + '.csv'))
            self.assertEqual(audit[0]['Aantal_gewijzigde_profielvelden'], '0')
            self.assertEqual(audit[0]['Vervanging_toegepast'], '1')

    def test_check_only_checks_complete_sources_without_creating_output(self):
        before = tree_bytes(self.fixture.source)
        self.assertEqual(self.run_pipeline(check_only=True), 0)
        self.assert_no_partial_output()
        self.assertEqual(tree_bytes(self.fixture.source), before)
        self.assertTrue(any('CONTROLE OK' in text for text in self.messages))

    def test_repeated_run_preserves_every_output_byte(self):
        self.run_pipeline()
        before = tree_bytes(self.fixture.output)
        source = tree_bytes(self.fixture.source)
        self.assertEqual(self.run_pipeline(), 0)
        self.assertEqual(tree_bytes(self.fixture.output), before)
        self.assertEqual(tree_bytes(self.fixture.source), source)
        self.assertTrue(any('opnieuw gecontroleerd' in text for text in self.messages))

    def test_modified_output_and_control_file_are_rejected_without_overwrite(self):
        self.run_pipeline()
        for name in (pipeline.VARIANTS[0]['svat'], 'controle/HRU_WATERTERMEN_FLEVOLAND.csv'):
            path = self.fixture.output / name
            original = path.read_bytes()
            path.write_bytes(original + b'changed\n')
            current = tree_bytes(self.fixture.output)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.run_pipeline()
            self.assertEqual(tree_bytes(self.fixture.output), current)
            path.write_bytes(original)

    def test_changed_valid_source_cannot_replace_completed_output(self):
        self.run_pipeline()
        before = tree_bytes(self.fixture.output)
        self.fixture.raw[4]['Neerslag (mm/j)'] = '1200'
        self.fixture.corrected[4]['Neerslag (mm/j)'] = '1200'
        self.fixture.write_source()  # Nieuwe geldige bronhashes en HRU-gemiddelden.
        source = tree_bytes(self.fixture.source)
        with self.assertRaises(FileExistsError):
            self.run_pipeline()
        self.assertEqual(tree_bytes(self.fixture.output), before)
        self.assertEqual(tree_bytes(self.fixture.source), source)

    def test_unregistered_source_change_and_different_reference_identity_are_rejected(self):
        original = tree_bytes(self.fixture.source)
        path = self.fixture.source / pipeline.VARIANTS[0]['source_svat']
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaises(ValueError):
            self.run_pipeline()
        self.assert_no_partial_output()
        for name, contents in original.items():
            (self.fixture.source / name).write_bytes(contents)
        manifest_path = self.fixture.source / pipeline.SOURCE_MANIFEST
        manifest = json.loads(manifest_path.read_text())
        manifest['identity']['sources']['data']['SVAT_HRU.csv.gz']['sha256'] = 'f' * 64
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_pipeline()
        self.assert_no_partial_output()

    def test_injected_midwrite_failure_closes_partial_files_and_retry_succeeds(self):
        before_source = tree_bytes(self.fixture.source)
        apply = pipeline.apply_profile
        calls = []

        def interrupted(*args, **kwargs):
            calls.append(1)
            if len(calls) == 7:  # Eerste variant compleet, tweede gedeeltelijk geschreven.
                raise OSError('Geinjecteerde schrijffout')
            return apply(*args, **kwargs)

        with mock.patch.object(pipeline, 'apply_profile', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'Geinjecteerde'):
                self.run_pipeline()
        self.assert_no_partial_output()
        self.assertEqual(tree_bytes(self.fixture.source), before_source)
        self.assertEqual(self.run_pipeline(), 0)

    def test_source_change_during_processing_prevents_publication(self):
        write = pipeline.write_variant
        changed = []
        source_path = self.fixture.source / pipeline.VARIANTS[0]['source_svat']

        def mutate_after_write(*args, **kwargs):
            result = write(*args, **kwargs)
            if not changed:
                source_path.write_bytes(source_path.read_bytes() + b'\n')
                changed.append(source_path.read_bytes())
            return result

        with mock.patch.object(pipeline, 'write_variant', side_effect=mutate_after_write):
            with self.assertRaisesRegex(ValueError, 'Bron gewijzigd tijdens verwerking'):
                self.run_pipeline()
        self.assert_no_partial_output()
        self.assertEqual(source_path.read_bytes(), changed[0])

    def test_mismatched_target_area_between_variants_is_rejected_after_safe_staging(self):
        self.fixture.corrected[2][AREA] = '80000'
        self.fixture.write_source()
        before = tree_bytes(self.fixture.source)
        with self.assertRaisesRegex(ValueError, 'Targetidentiteiten'):
            self.run_pipeline()
        self.assert_no_partial_output()
        self.assertEqual(tree_bytes(self.fixture.source), before)


if __name__ == '__main__':
    unittest.main()
