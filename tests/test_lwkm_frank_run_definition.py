"""Unit checks for LHM config discovery; no NHI server dependency."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tools.lwkm_frank.run_definition import parse_ini, produce

class RunDefinitionTests(unittest.TestCase):
    def test_nested_sections_interpolation_and_sha(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            ini = root / 'control_run_1970_1979.ini'
            ini.write_text(
                '[DATA]\n'
                'model = E:\\LHM_4.3.3\n'
                '[[MODFLOW]]\n'
                'head = %(model)s\\Data\\2_Model_Input\\modflow\\head.idf\n'
                '# ignored = C:\\ignore\n'
                '[RESTART]\nrestart = G:\\run\\prior.rst\n',
                encoding='utf8')
            parsed = parse_ini(ini)
            self.assertEqual(parsed['period_hint'], '1970_1979')
            paths = [p['resolved'] for p in parsed['path_candidates']]
            self.assertIn('E:\\LHM_4.3.3\\Data\\2_Model_Input\\modflow\\head.idf', paths)
            self.assertIn('G:\\run\\prior.rst', paths)
            self.assertEqual(len(parsed['sha256']), 64)
            out = root / 'reports'
            result = produce([root], 'control_run_*.ini', out, root/'output')
            self.assertEqual(result['ini_count'], 1)
            self.assertEqual(result['status'], 'INPUT_CONFIG_AUTHORITY_PARTIAL')
            self.assertEqual(result['source_file_mutations'], 0)
            self.assertEqual(json.loads((out/'lhm_run_definition.json').read_text())['ini_count'], 1)
            self.assertTrue((out/'lhm_ini_references.csv').is_file())

    def test_missing_ini_is_explicit_blocker(self):
        with TemporaryDirectory() as d:
            p = Path(d)
            result = produce([p], 'control_run_*.ini', p/'report', p/'output')
            self.assertEqual(result['status'], 'BLOCKED_NO_INI_FOUND')
            self.assertEqual(result['ini_count'], 0)

if __name__ == '__main__':
    unittest.main()
