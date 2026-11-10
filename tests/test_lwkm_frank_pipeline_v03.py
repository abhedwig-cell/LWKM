"""Contract tests and a real 30-year / three-SVAT synthetic producer replay.

Only the fixture launcher changes EXPECTED_SVATS from 645582 to 3 in memory.
No production source file or arithmetic is changed. The actual deployment
configuration still requires 645582 SVATs. No real NHI outputs are used.
"""
import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tools/lwkm_frank/pipeline_v03.py'
spec = importlib.util.spec_from_file_location('pipeline_v03', MODULE)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def make_fixture(root):
    source = root / 'LWKM_run_resultaten_totaal'
    source.mkdir()
    metaswap = root / 'run_1970_1979/metaswap'
    metaswap.mkdir(parents=True)
    area = metaswap / 'area_svat.inp'
    area.write_text('\n'.join(f'{i} {a} 10 1 1 1 1 1 1 {x} 375 1 1 1' for i, a, x
                             in ((1, 12500, 125), (2, 40000, 375), (3, 20000, 625))) + '\n')
    binding = dict(kind='LWKM_RUN_SOURCE_BINDING', source_profile='run_local',
                   source_executable_authority=p.SOURCE_DECISION,
                   static_input_identity='OWNER_ESTABLISHED_IDENTICAL_BETWEEN_RUNS',
                   output_authority_root=str(source), static_reference_run='run_1970_1979',
                   metaswap_input_root=str(metaswap), static_files={'area_svat.inp':
                   {'path': str(area), 'sha256': p.sha(area)}})
    bf = root / 'binding.json'; bf.write_text(json.dumps(binding))
    config = dict(schema_version=3, period=[1991, 2020], expected_svats=645582,
                  production_enabled=False, source_hash_mode='metadata', binding_file=str(bf),
                  binding_sha256=p.sha(bf), output_name='Frank_v03_fixture', ibound_l1=str(root / 'mask.idf'))
    cp = root / 'config.json'; cp.write_text(json.dumps(config))
    return cp


def write_idf(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = list(values) + [0, 0, 0]
    header = struct.pack('<3i7f4B2f', 1271, 3, 2, 0., 750., 0., 500.,
                         min(data), max(data), -9999., 0, 0, 0, 0, 250., 250.)
    path.write_bytes(header + struct.pack('<6f', *data))


class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cp = make_fixture(self.root)
        self.ctx = p.load_context(self.cp)

    def change(self, key, value):
        c = json.loads(self.cp.read_text()); c[key] = value; self.cp.write_text(json.dumps(c))

    def test_twelve_original_hashes(self):
        self.assertEqual(len(p.verify_code()), 12)

    @unittest.skipUnless(all((p.DATA / n).is_file() for n in p.ASSETS), 'Full data assets are supplied in the server ZIP')
    def test_all_packaged_assets_exact(self):
        for name, expected in p.ASSETS.items():
            self.assertEqual(p.sha(p.DATA / name), expected)

    def test_dependency_selection_not_a_prefix(self):
        self.assertEqual(p.selection('qmodf'), ['msw_basic', 'qmodf'])
        self.assertEqual(p.selection('gebied_n'), ['gxg', 'gw_percentielen', 'gebied_n'])

    def test_full_dependency_order(self):
        selected = p.selection('svat_basis')
        self.assertEqual(set(selected), set(p.PRODUCERS))
        for step in selected:
            for dep in p.DEPENDENCIES[step]:
                self.assertLess(selected.index(dep), selected.index(step))

    def test_all_explicit_out_paths(self):
        for step in p.PRODUCERS:
            out = self.ctx['output'] / 'work' / step
            cmd = p.command(self.ctx, step, out)
            destination = Path(cmd[cmd.index('--out')+1])
            self.assertTrue(p.inside(destination, out))
            self.assertFalse(p.inside(destination, self.ctx['source']))

    def test_all_area_arguments_use_run_local(self):
        for step in ('msw_basic', 'modflow_original', 'gxg', 'et_componenten', 'statisch_gt'):
            cmd = p.command(self.ctx, step, self.root / 'out')
            self.assertEqual(cmd[cmd.index('--area')+1], str(self.ctx['area']))

    def test_no_legacy_export_dependencies(self):
        for step in p.PRODUCERS:
            cmd = p.command(self.ctx, step, self.root / 'out')
            self.assertFalse(any('frank_export' in item for item in cmd))

    def test_signed_input_is_second_artifact(self):
        cmd = p.command(self.ctx, 'svat_basis', self.root / 'out')
        self.assertEqual(cmd[cmd.index('--signed')+1], str(p.artifacts(self.ctx, 'msw_basic')[1]))

    def test_nine_original_cli_help(self):
        for name in p.PRODUCERS.values():
            r = subprocess.run([sys.executable, '-B', str(p.LEGACY / name), '--help'], capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_plan_performs_no_output_write(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(p.main(['plan', '--config', str(self.cp), '--through', 'all']), 0)
        self.assertFalse(self.ctx['output'].exists())

    def test_bad_binding_pin_rejected(self):
        self.change('binding_sha256', '0'*64)
        with self.assertRaises(ValueError): p.load_context(self.cp)

    def test_production_cannot_be_switched_on(self):
        self.change('production_enabled', True)
        with self.assertRaises(ValueError): p.load_context(self.cp)

    def test_population_change_rejected(self):
        self.change('expected_svats', 3)
        with self.assertRaises(ValueError): p.load_context(self.cp)

    def test_period_change_rejected(self):
        self.change('period', [1992, 2020])
        with self.assertRaises(ValueError): p.load_context(self.cp)

    def test_parent_path_rejected(self):
        self.change('output_name', '../LWKM_run_resultaten_totaal')
        with self.assertRaises(ValueError): p.load_context(self.cp)

    def test_unknown_hash_mode_rejected(self):
        self.change('source_hash_mode', 'fast')
        with self.assertRaises(ValueError): p.load_context(self.cp)

    def test_output_symlink_escape_rejected(self):
        target = self.root / 'LWKM_rebuilds'
        try: target.symlink_to(self.ctx['source'], target_is_directory=True)
        except OSError: self.skipTest('No symlink support')
        with self.assertRaises(ValueError): p.load_context(self.cp)

    def test_lock_excludes_second_writer(self):
        with p.output_lock(self.ctx['output']):
            with self.assertRaises(RuntimeError):
                with p.output_lock(self.ctx['output']): pass
        self.assertFalse((self.ctx['output'] / 'RUNNING.lock').exists())

    def test_lock_released_after_failure(self):
        with self.assertRaises(ValueError):
            with p.output_lock(self.ctx['output']): raise ValueError('fixture')
        self.assertFalse((self.ctx['output'] / 'RUNNING.lock').exists())

    def test_atomic_json_failure_preserves_old(self):
        dest = self.root / 'old.json'; dest.write_text('{"old": true}')
        with patch.object(p.os, 'replace', side_effect=OSError('fixture lock')):
            with self.assertRaises(OSError): p.atomic_json(dest, {'old': False})
        self.assertEqual(dest.read_text(), '{"old": true}')
        self.assertEqual(list(self.root.glob('.json_*.partial')), [])

    def test_csv_blank_nodata_allowed(self):
        f = self.root / 'x.csv'; f.write_text('SVAT,Gebied,N\n1,,1\n2,5,1\n')
        self.assertEqual(p.validate_csv(f, ['SVAT', 'Gebied', 'N'], {1,2})['rows'], 2)

    def test_csv_duplicate_rejected(self):
        f = self.root / 'x.csv'; f.write_text('SVAT,N\n1,1\n1,1\n')
        with self.assertRaises(ValueError): p.validate_csv(f, ['SVAT'], {1,2})

    def test_csv_wrong_population_rejected(self):
        f = self.root / 'x.csv'; f.write_text('SVAT,N\n1,1\n3,1\n')
        with self.assertRaises(ValueError): p.validate_csv(f, ['SVAT'], {1,2})

    def test_csv_wrong_width_rejected(self):
        f = self.root / 'x.csv'; f.write_text('SVAT,N\n1,1,0\n')
        with self.assertRaises(ValueError): p.validate_csv(f, ['SVAT'], {1})

    def test_snapshot_area_changed_rejected(self):
        self.ctx['area'].write_text('changed')
        with self.assertRaises(ValueError): p.snapshot(self.ctx, 'msw_basic')

    def test_content_hash_detects_preserved_metadata_change(self):
        f = self.root / 'x'; f.write_bytes(b'1111'); st = f.stat()
        a = p.file_record(f, True); f.write_bytes(b'2222')
        os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns))
        b = p.file_record(f, True)
        self.assertNotEqual(a['sha256'], b['sha256'])
        self.assertEqual(a['mtime_ns'], b['mtime_ns'])

    def test_metadata_mode_does_not_claim_content_hash(self):
        f = self.root / 'x'; f.write_bytes(b'1111')
        self.assertNotIn('sha256', p.file_record(f, False))

    def test_modified_original_source_blocked(self):
        with patch.object(p, 'sha', return_value='0'*64):
            with self.assertRaises(ValueError): p.verify_code()


class NumericalReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.root = Path(cls.tmp.name)
        cls.cp = make_fixture(cls.root); cls.ctx = p.load_context(cls.cp)
        cls.m = p.module('build_svat_base'); cls.reader = p.module('wb10_reader')
        values = {'bdgpm': [.020,.030,.010], 'bdgetact': [-.005,-.006,-.002],
                  'bdgqrun': [-.001,-.002,-.0005], 'bdgdecstot': [-.0001,.0001,0],
                  'bdgpssw': [.0001,.0002,0], 'bdgpsgw': [.0003,0,0]}
        for period in cls.reader.decades(1991, 2020):
            for role, data in values.items():
                data = list(data)
                if role == 'bdgetact' and period['date_end'] == '19960720': data[2] = -9999.
                write_idf(cls.ctx['source'] / 'metaswap' / role / f'{role}_{period["date_end"]}_l1.idf', data)
        cls.launcher = cls.root / 'fixture_launcher.py'
        cls.launcher.write_text("import sys,runpy\nsys.path.insert(0,sys.argv[1])\nimport wb10_reader\nwb10_reader.EXPECTED_SVATS=3\nsys.argv=sys.argv[2:]\nrunpy.run_path(sys.argv[0],run_name='__main__')\n")
        cls.original_command = p.command
        cls.direct = cls.root / 'direct_original'
        direct_cmd = cls.original_command(cls.ctx, 'msw_basic', cls.direct)
        cmd = [sys.executable, '-B', str(cls.launcher), str(p.LEGACY), *direct_cmd[3:]]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: raise AssertionError(r.stderr)
        def fixture_command(ctx, step, out):
            cmd = cls.original_command(ctx, step, out)
            return [sys.executable, '-B', str(cls.launcher), str(p.LEGACY), *cmd[3:]]
        with patch.object(p, 'command', side_effect=fixture_command), contextlib.redirect_stdout(io.StringIO()):
            cls.receipt = p.run_step(cls.ctx, 'msw_basic', {1,2,3})
        cls.final = cls.ctx['output'] / 'results/msw_basic'

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_actual_original_and_controlled_csv_byte_identical(self):
        for name in p.ARTIFACTS['msw_basic']:
            self.assertEqual((self.direct/name).read_bytes(), (self.final/name).read_bytes())

    def test_thirty_years_6480_idfs_in_identity(self):
        inputs = json.loads((self.final/'INPUTS_V03.json').read_text())
        self.assertEqual(len(inputs['raw_idfs']), 6480)
        self.assertEqual(inputs['raw_idf_fingerprint_mode'], 'metadata')

    def test_unit_scale_and_outflow_sign_preserved(self):
        with (self.final / p.ARTIFACTS['msw_basic'][0]).open() as f: rows=list(csv.DictReader(f))
        self.assertAlmostEqual(float(rows[0]['Neerslag']), 720., places=3)
        self.assertAlmostEqual(float(rows[0]['Evapotranspiratie']), 180., places=3)
        self.assertAlmostEqual(float(rows[0]['Oppervlakkige afstroming']), 36., places=3)

    def test_nodata_not_zero(self):
        with (self.final / p.ARTIFACTS['msw_basic'][0]).open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(rows[2]['Neerslag'], '')
        with (self.final / p.ARTIFACTS['msw_basic'][1]).open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(rows[2]['complete_source'], '0')

    def test_clean_publish_preserves_source_authority(self):
        self.assertFalse((self.ctx['output'] / 'work/msw_basic').exists())
        self.assertFalse(any(self.ctx['source'].rglob('*.csv')))
        self.assertFalse(self.receipt['production_enabled'])

    def test_complete_result_reused_without_producer_execution(self):
        with patch.object(p.subprocess, 'Popen', side_effect=AssertionError('must not execute')), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(p.run_step(self.ctx, 'msw_basic', {1,2,3}), self.receipt)

    def test_tampered_result_cannot_be_reused(self):
        f=self.final / p.ARTIFACTS['msw_basic'][0]; original=f.read_bytes()
        try:
            f.write_bytes(original.replace(b'720.', b'721.', 1) if b'720.' in original else original+b'\n')
            with self.assertRaises(ValueError): p.run_step(self.ctx, 'msw_basic', {1,2,3})
        finally: f.write_bytes(original)

    def test_changed_raw_source_cannot_reuse_result(self):
        f=next((self.ctx['source']/'metaswap/bdgpm').iterdir()); old=f.read_bytes(); st=f.stat()
        try:
            f.write_bytes(old + b'changed')
            with self.assertRaises(ValueError): p.run_step(self.ctx, 'msw_basic', {1,2,3})
        finally:
            f.write_bytes(old); os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns))

    def test_failed_producer_never_publishes_result(self):
        ctx=dict(self.ctx, output=self.root/'LWKM_rebuilds/Frank_v03_failure')
        with patch.object(p, 'command', return_value=[sys.executable,'-c','raise SystemExit(7)']), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(RuntimeError): p.run_step(ctx,'msw_basic',{1,2,3})
        self.assertFalse((ctx['output']/'results/msw_basic').exists())
        self.assertTrue((ctx['output']/'work/msw_basic/producer.log').exists())


if __name__ == '__main__': unittest.main(verbosity=2)
