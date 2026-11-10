"""Synthetic IDF and filesystem tests. These do not qualify real NHI results."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('msw_adapter', ROOT / 'tools/lwkm_frank/msw_basic_run.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def idf(path, values):
    # Two 250m cells, centres (125,125) and (375,125).
    header = struct.pack('<iii7f4B2f', 1271, 2, 1, 0, 500, 0, 250,
                         min(values), max(values), -9999, 0, 0, 0, 0, 250, 250)
    path.write_bytes(header + struct.pack('<2f', *values))


class StageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runs = Path(self.tmp.name)
        self.metaswap = self.runs / 'run_1970_1979/metaswap'
        self.metaswap.mkdir(parents=True)
        self.area = self.metaswap / 'area_svat.inp'
        self.area.write_text('1 100 2 0 1 1 1 1 1 125 125 1 1 1\n2 200 2 0 1 1 1 1 1 375 125 1 1 1\n')
        self.output = self.runs / 'LWKM_run_resultaten_totaal'
        self.root = self.output / 'metaswap'
        reader, _, _ = m.frozen_modules()
        values = {'bdgpm': .01, 'bdgetact': -.002, 'bdgqrun': -.001,
                  'bdgdecstot': 0, 'bdgpssw': .003, 'bdgpsgw': .004}
        for role, value in values.items():
            folder = self.root / role
            folder.mkdir(parents=True)
            for d in reader.decades(2020, 2020):
                idf(folder / (role + '_' + d['date_end'] + '_l1.idf'), [value, value])
        self.binding = self.runs / 'binding.json'
        self.b = {'kind': 'LWKM_RUN_SOURCE_BINDING', 'source_profile': 'run_local',
                  'production_enabled': False,
                  'source_executable_authority': 'LWKM-LHM-SOURCE-20261110-01',
                  'output_authority_root': str(self.output),
                  'metaswap_input_root': str(self.metaswap), 'static_reference_run': 'run_1970_1979',
                  'static_files': {'area_svat.inp': {'path': str(self.area), 'sha256': m.sha(self.area)}}}
        self.config = self.runs / 'config.json'
        self.c = {'schema_version': 1, 'binding': str(self.binding), 'from_year': 2020, 'to_year': 2020}
        self.bind()

    def bind(self):
        self.b['static_files']['area_svat.inp']['sha256'] = m.sha(self.area)
        self.binding.write_text(json.dumps(self.b))
        self.c['binding_sha256'] = m.sha(self.binding)
        self.save()

    def save(self):
        self.config.write_text(json.dumps(self.c))

    def run_stage(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return m.run_stage(self.config)

    def test_read_only_check_and_actual_population(self):
        r = m.prepare(self.config)[0]
        self.assertEqual(r['svat_count'], 2)
        self.assertEqual(r['idf_files'], 216)
        self.assertFalse(r['historical_count_enforced'])
        self.assertEqual(r['producers_executed'], 0)
        self.assertFalse(Path(r['target']).parent.exists())

    def test_csv_byte_equivalence_to_original_kernel(self):
        r, p, args, _ = m.prepare(self.config)
        args.out = self.runs / 'original_reference'
        with contextlib.redirect_stdout(io.StringIO()):
            p.execute(args)
        result = self.run_stage()
        target = Path(result['target'])
        for old in args.out.glob('*.csv'):
            self.assertEqual(old.read_bytes(), (target / old.name).read_bytes(), old.name)
        self.assertEqual(result['producers_executed'], 1)
        self.assertFalse(result['whole_chain_production_enabled'])
        self.assertTrue((target / 'RUN_RECEIPT.json').is_file())
        import csv
        with (target / 'FRANK_LHM_SVAT_BASE_2020_2020.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertAlmostEqual(float(rows[0]['Neerslag']), 360, places=4)
        self.assertAlmostEqual(float(rows[0]['Evapotranspiratie']), 72, places=4)
        self.assertAlmostEqual(float(rows[0]['Oppervlakkige afstroming']), 36, places=4)

    def test_missing_cell_remains_blank(self):
        idf(self.root / 'bdgpm/bdgpm_20200110_l1.idf', [.01, -9999])
        r = self.run_stage()
        import csv
        with (Path(r['target']) / 'FRANK_LHM_SVAT_BASE_2020_2020.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertNotEqual(rows[0]['Neerslag'], '')
        self.assertEqual(rows[1]['Neerslag'], '')
        self.assertEqual(rows[1]['Evapotranspiratie'], '')

    def test_changed_area_rejected(self):
        self.area.write_text(self.area.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'differs'):
            m.prepare(self.config)

    def test_changed_binding_rejected(self):
        self.binding.write_text(self.binding.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'binding differs'):
            m.prepare(self.config)

    def test_duplicate_svat_rejected(self):
        self.area.write_text(self.area.read_text().replace('\n2 ', '\n1 '))
        self.bind()
        with self.assertRaisesRegex(ValueError, 'duplicate IDs'):
            m.prepare(self.config)

    def test_malformed_area_rejected(self):
        self.area.write_text('1 100 2\n')
        self.bind()
        with self.assertRaisesRegex(ValueError, '14 columns'):
            m.prepare(self.config)

    def test_missing_idf_rejected(self):
        (self.root / 'bdgpm/bdgpm_20200110_l1.idf').unlink()
        with self.assertRaises(FileNotFoundError):
            m.prepare(self.config)

    def test_duplicate_idf_rejected(self):
        p = self.root / 'bdgpm/bdgpm_20200110_l1.idf'
        p.with_name('bdgpm_20200110000000_l1.idf').write_bytes(p.read_bytes())
        with self.assertRaisesRegex(ValueError, 'Dubbele'):
            m.prepare(self.config)

    def test_existing_output_not_overwritten(self):
        r = self.run_stage()
        receipt = Path(r['target']) / 'RUN_RECEIPT.json'
        before = receipt.read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_stage()
        self.assertEqual(before, receipt.read_bytes())

    def test_source_change_during_run_not_published(self):
        original_prepare = m.prepare
        def changed_prepare(c):
            r, producer, args, inputs = original_prepare(c)
            original_execute = producer.execute
            def mutate(a):
                original_execute(a)
                self.area.write_text(self.area.read_text() + '\n')
            producer.execute = mutate
            return r, producer, args, inputs
        with patch.object(m, 'prepare', side_effect=changed_prepare):
            with self.assertRaisesRegex(ValueError, 'Dependency changed'):
                self.run_stage()
        parent = self.runs / 'LWKM_tools/LWKM_Frank_Rebuild_v03'
        self.assertFalse((parent / 'msw_basic_2020_2020').exists())
        self.assertEqual(len(list(parent.glob('*/FAILED.json'))), 1)

    def test_invalid_raster_not_published(self):
        (self.root / 'bdgpm/bdgpm_20200110_l1.idf').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'Short IDF'):
            self.run_stage()
        self.assertFalse((self.runs / 'LWKM_tools/LWKM_Frank_Rebuild_v03/msw_basic_2020_2020').exists())

    def test_global_area_fallback_rejected(self):
        other = self.runs / 'global/area_svat.inp'
        other.parent.mkdir()
        other.write_bytes(self.area.read_bytes())
        self.b['static_files']['area_svat.inp']['path'] = str(other)
        self.bind()
        with self.assertRaisesRegex(ValueError, 'not inside'):
            m.prepare(self.config)

    def test_source_files_not_modified_and_legacy_hashes_unchanged(self):
        paths = [p for p in self.runs.rglob('*') if p.is_file()]
        before = {p: m.sha(p) for p in paths}
        self.run_stage()
        self.assertEqual(before, {p: m.sha(p) for p in paths})
        self.assertEqual(len(m.frozen_modules()[2]), 12)

    def test_invalid_period_rejected(self):
        self.c['from_year'] = 2021
        self.save()
        with self.assertRaises(ValueError):
            m.prepare(self.config)

    def test_entrypoint_reports_failed_check(self):
        (self.root / 'bdgpm/bdgpm_20200110_l1.idf').unlink()
        report = self.runs / 'CONTROL.json'
        with contextlib.redirect_stderr(io.StringIO()):
            code = m.main(['--config', str(self.config), '--report', str(report)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(report.read_text())['status'], 'STOPPED')

    def test_entrypoint_reports_successful_check(self):
        report = self.runs / 'CONTROL.json'
        with contextlib.redirect_stdout(io.StringIO()):
            code = m.main(['--config', str(self.config), '--report', str(report)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(report.read_text())['producers_executed'], 0)


if __name__ == '__main__':
    unittest.main()
