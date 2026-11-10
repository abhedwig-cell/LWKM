"""Synthetic read-only binding tests; not a numerical or NHI qualification."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'tools/lwkm_frank/run_source_binding.py'
spec = importlib.util.spec_from_file_location('run_source_binding', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.msw = self.root / 'run_1970_1979/metaswap'
        self.msw.mkdir(parents=True)
        self.area = self.msw / 'area_svat.inp'
        self.area.write_bytes(b'fixture-only area data\r\n')
        (self.root / 'LWKM_run_resultaten_totaal').mkdir()
        self.config = {'schema_version': 1, 'source_profile': 'run_local',
                       'runs_root': str(self.root), 'static_reference_run': 'run_1970_1979',
                       'static_files': {'area_svat.inp': {'path': 'area_svat.inp', 'required': True}}}
        self.cp = self.root / 'config.json'

    def save(self):
        self.cp.write_text(json.dumps(self.config), encoding='utf-8')
        return self.cp

    def test_direct_area_path_and_no_production(self):
        r, target = m.build_binding(self.save())
        self.assertEqual(r['static_files']['area_svat.inp']['sha256'], m.digest(self.area))
        self.assertEqual(r['metaswap_input_root'], str(self.msw))
        self.assertFalse(r['production_enabled'])
        self.assertEqual(r['producers_executed'], 0)
        self.assertFalse(target.exists())

    def test_no_implicit_inp_lookup(self):
        (self.msw / 'inp').mkdir()
        self.area.rename(self.msw / 'inp/area_svat.inp')
        with self.assertRaises(FileNotFoundError):
            m.build_binding(self.save())

    def test_explicit_inp_path_is_accepted(self):
        (self.msw / 'inp').mkdir()
        self.area.rename(self.msw / 'inp/area_svat.inp')
        self.config['static_files']['area_svat.inp']['path'] = 'inp/area_svat.inp'
        r, _ = m.build_binding(self.save())
        self.assertEqual(Path(r['static_files']['area_svat.inp']['path']).parts[-2:],
                         ('inp', 'area_svat.inp'))

    def test_missing_required_input_fails(self):
        self.area.unlink()
        with self.assertRaises(FileNotFoundError):
            m.build_binding(self.save())

    def test_missing_optional_is_reported(self):
        self.config['static_files']['mod2svat.inp'] = {'path': 'mod2svat.inp', 'required': False}
        r, _ = m.build_binding(self.save())
        self.assertEqual(len(r['optional_files_not_present']), 1)

    def test_present_optional_is_fingerprinted(self):
        (self.msw / 'mod2svat.inp').write_bytes(b'mapping fixture')
        self.config['static_files']['mod2svat.inp'] = {'path': 'mod2svat.inp', 'required': False}
        r, _ = m.build_binding(self.save())
        self.assertIn('mod2svat.inp', r['static_files'])

    def test_global_legacy_profile_rejected(self):
        self.config['source_profile'] = 'legacy_reference'
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_absolute_global_path_rejected(self):
        self.config['static_files']['area_svat.inp']['path'] = r'E:\LHM_4.3.3\area_svat.inp'
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_parent_traversal_rejected(self):
        self.config['static_files']['area_svat.inp']['path'] = '../area_svat.inp'
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_svat_border_not_an_allowed_input(self):
        self.config['static_files']['svat_border.inp'] = {'path': 'svat_border.inp'}
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_area_cannot_be_optional(self):
        self.config['static_files']['area_svat.inp']['required'] = False
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_missing_output_authority_rejected(self):
        (self.root / 'LWKM_run_resultaten_totaal').rmdir()
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_no_cross_run_comparison_or_required_ini(self):
        self.config['ini_inventory'] = 'missing_inventory.json'
        r, _ = m.build_binding(self.save())
        self.assertEqual(r['declared_run_context']['status'], 'NOT_AVAILABLE')
        self.assertIn('NOT_PERFORMED', r['cross_run_hash_comparison'])
        self.assertEqual(r['source_executable_authority'], m.SOURCE_DECISION)

    def test_ini_variants_preserved_without_selection(self):
        ini = self.root / 'inventory.json'
        contexts = [{'path': 'control_run_1970_1979.ini', 'period_hint': '1970_1979'},
                    {'path': 'control_run_1970_1979_MS_daily.ini', 'period_hint': '1970_1979'}]
        ini.write_text(json.dumps({'ini_files': contexts}), encoding='utf-8')
        self.config['ini_inventory'] = 'inventory.json'
        r, _ = m.build_binding(self.save())
        self.assertEqual(r['declared_run_context']['run_contexts'], contexts)
        self.assertEqual(r['declared_run_context']['status'], 'DECLARED_CONTEXT_ONLY')

    def test_write_atomic_and_sources_unchanged(self):
        before = self.area.read_bytes()
        target = m.write_binding(self.save())
        self.assertTrue(target.is_file())
        self.assertEqual(self.area.read_bytes(), before)
        self.assertEqual(list(target.parent.glob('*.partial')), [])
        self.assertEqual(json.loads(target.read_text())['source_file_mutations'], 0)

    def test_failed_validation_preserves_previous_binding(self):
        target = m.write_binding(self.save())
        previous = target.read_bytes()
        self.area.unlink()
        with self.assertRaises(FileNotFoundError):
            m.write_binding(self.cp)
        self.assertEqual(target.read_bytes(), previous)

    def test_unrelated_target_not_overwritten(self):
        target = self.root / 'LWKM_tools' / m.BINDING_FOLDER / 'run_source_binding.json'
        target.parent.mkdir(parents=True)
        target.write_text('{"kind": "OTHER"}')
        with self.assertRaises(ValueError):
            m.write_binding(self.save())
        self.assertEqual(target.read_text(), '{"kind": "OTHER"}')

    def test_cli_has_real_nonzero_failure(self):
        self.save()
        good = subprocess.run([sys.executable, str(MODULE), '--config', str(self.cp)], capture_output=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.area.unlink()
        bad = subprocess.run([sys.executable, str(MODULE), '--config', str(self.cp)], capture_output=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn(b'STOP:', bad.stderr)

    def test_input_symlink_escape_rejected(self):
        outside = self.root / 'area_svat.inp'
        outside.write_bytes(b'not run-local')
        self.area.unlink()
        try:
            self.area.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_non_object_config_rejected(self):
        self.cp.write_text('[]')
        with self.assertRaises(ValueError):
            m.build_binding(self.cp)

    def test_malformed_inventory_rejected(self):
        (self.root / 'inventory.json').write_text('[]')
        self.config['ini_inventory'] = 'inventory.json'
        with self.assertRaises(ValueError):
            m.build_binding(self.save())

    def test_redirected_run_directory_rejected(self):
        with tempfile.TemporaryDirectory() as external:
            moved = Path(external) / 'run_1970_1979'
            (self.root / 'run_1970_1979').rename(moved)
            try:
                (self.root / 'run_1970_1979').symlink_to(moved, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest('Symlinks unavailable')
            with self.assertRaises(ValueError):
                m.build_binding(self.save())

    def test_redirected_tools_directory_rejected(self):
        with tempfile.TemporaryDirectory() as external:
            try:
                (self.root / 'LWKM_tools').symlink_to(Path(external), target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest('Symlinks unavailable')
            with self.assertRaises(ValueError):
                m.build_binding(self.save())

    def test_failed_replace_cleans_temp_and_preserves_old(self):
        target = m.write_binding(self.save())
        old = target.read_bytes()
        with patch.object(m.os, 'replace', side_effect=OSError('fixture lock')):
            with self.assertRaises(OSError):
                m.write_binding(self.cp)
        self.assertEqual(target.read_bytes(), old)
        self.assertEqual(list(target.parent.glob('*.partial')), [])


if __name__ == '__main__':
    unittest.main()
