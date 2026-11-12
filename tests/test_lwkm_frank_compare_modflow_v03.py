"""Synthetic comparison/receipt tests; not an actual MODFLOW producer run."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1] / 'tools/lwkm_frank'
sys.path.insert(0, str(HERE))
import compare_modflow_v03 as c


class ModflowComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.ctx = dict(output=root / 'new', source=root / 'old',
                        binding_sha='a'*64, config_sha='b'*64, controller_sha='c'*64,
                        code_sha={'producer.py':'d'*64},
                        config={'expected_svats':2, 'period':[1991,2020]})
        self.folder = self.ctx['output'] / 'results' / c.STEP
        self.folder.mkdir(parents=True)
        self.ref = self.ctx['source'] / c.REFERENCE_FOLDER / c.FILENAME
        self.ref.parent.mkdir(parents=True)
        self.table = 'SVAT,FLF_KWEL_m3,RIV_SYS1_ONTWATERING_m3\n1,2,3\n2,,4\n'
        self.ref.write_text(self.table)
        self.candidate = self.folder / c.FILENAME
        self.candidate.write_text(self.table)
        self.msw = {'status':'FIRST_STAGE_VALUES_EQUAL', 'production_enabled':False,
                    'source_binding_sha256':self.ctx['binding_sha'], 'files':{}}
        for name in c.p.ARTIFACTS['msw_basic']:
            self.msw['files'][name] = dict(rows=2, equal_values=True, byte_identical=True,
                changed_cells_by_column={}, reference_sha256='e'*64, candidate_sha256='e'*64)
        self.msw_path = self.ctx['output'] / 'COMPARE_MSW_REFERENCE_V03.json'
        self.save_msw()
        self.inputs = dict(step=c.STEP, binding_sha256=self.ctx['binding_sha'],
            config_sha256=self.ctx['config_sha'], controller_sha256=self.ctx['controller_sha'],
            code_sha256=self.ctx['code_sha'], raw_idf_fingerprint_mode='metadata')
        self.record()

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def save_msw(self):
        self.write(self.msw_path, self.msw)

    def record(self):
        self.write(self.folder / 'INPUTS_V03.json', self.inputs)
        self.receipt = dict(status='COMPUTED_STRUCTURAL_QA_ONLY', production_enabled=False,
            identity_sha256=c.p.object_sha(self.inputs), outputs={c.FILENAME:dict(
            sha256=c.p.sha(self.candidate), bytes=self.candidate.stat().st_size, rows=2)})
        self.write(self.folder / 'RECEIPT_V03.json', self.receipt)

    def test_equal_and_no_production(self):
        before = self.ref.read_bytes()
        r=c.compare_stage(self.ctx)
        self.assertEqual(r['status'],'MODFLOW_STAGE_VALUES_EQUAL')
        self.assertTrue(r['files'][c.FILENAME]['byte_identical'])
        self.assertFalse(r['production_enabled'])
        self.assertFalse(r['drn_audit_compared'])
        self.assertEqual(before,self.ref.read_bytes())
        self.assertTrue((self.ctx['output']/c.REPORT).is_file())
        self.assertFalse((self.ctx['output']/'RUNNING.lock').exists())

    def test_changed_value(self):
        self.candidate.write_text(self.table.replace('1,2,3','1,9,3'));self.record()
        r=c.compare_stage(self.ctx)
        self.assertEqual(r['status'],'MODFLOW_STAGE_DIFFERENCES_FOUND')
        self.assertEqual(r['files'][c.FILENAME]['changed_cells_by_column'],{'FLF_KWEL_m3':1})

    def test_format_only_is_equal(self):
        self.candidate.write_text(self.table.replace('1,2,3','1,2.00,3'));self.record()
        r=c.compare_stage(self.ctx)
        self.assertTrue(r['files'][c.FILENAME]['equal_values'])
        self.assertFalse(r['files'][c.FILENAME]['byte_identical'])

    def test_blank_not_zero(self):
        self.candidate.write_text(self.table.replace('2,,4','2,0,4'));self.record()
        self.assertFalse(c.compare_stage(self.ctx)['files'][c.FILENAME]['equal_values'])

    def test_missing_reference_precheck(self):
        self.ref.unlink()
        with self.assertRaises(FileNotFoundError):c.check_reference(self.ctx)

    def test_precheck_needs_no_candidate(self):
        self.candidate.unlink()
        self.assertEqual(c.check_reference(self.ctx)[0],self.ref)

    def test_wrong_msw_binding(self):
        self.msw['source_binding_sha256']='f'*64;self.save_msw()
        with self.assertRaises(ValueError):c.check_reference(self.ctx)

    def test_incomplete_msw(self):
        self.msw['files'].pop(next(iter(self.msw['files'])));self.save_msw()
        with self.assertRaises(ValueError):c.check_reference(self.ctx)

    def test_msw_mismatch(self):
        next(iter(self.msw['files'].values()))['candidate_sha256']='f'*64;self.save_msw()
        with self.assertRaises(ValueError):c.check_reference(self.ctx)

    def test_msw_wrong_count(self):
        next(iter(self.msw['files'].values()))['rows']=3;self.save_msw()
        with self.assertRaises(ValueError):c.check_reference(self.ctx)

    def test_wrong_input_identity(self):
        self.inputs['step']='gxg';self.record()
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_tampered_inputs(self):
        self.inputs['config_sha256']='f'*64
        self.write(self.folder/'INPUTS_V03.json',self.inputs)
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_different_config(self):
        self.inputs['config_sha256']='f'*64;self.record()
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_different_code(self):
        self.inputs['controller_sha256']='f'*64;self.record()
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_tampered_candidate(self):
        self.candidate.write_text(self.table.replace('1,2,3','1,9,3'))
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_locked_output(self):
        (self.ctx['output']/'RUNNING.lock').write_text('another process')
        with self.assertRaises(RuntimeError):c.compare_stage(self.ctx)
        self.assertTrue((self.ctx['output']/'RUNNING.lock').exists())

    def test_error_preserves_existing_report(self):
        report=self.ctx['output']/c.REPORT;report.write_text('previous')
        self.candidate.unlink()
        with self.assertRaises(FileNotFoundError):c.compare_stage(self.ctx)
        self.assertEqual(report.read_text(),'previous')

    def test_mutation_during_compare(self):
        original=c.original.compare
        def change(*args):
            r=original(*args);self.ref.write_text(self.table+'3,1,2\n');return r
        with patch.object(c.original,'compare',side_effect=change):
            with self.assertRaises(ValueError):c.compare_stage(self.ctx)
        self.assertFalse((self.ctx['output']/c.REPORT).exists())

    def test_candidate_symlink_outside(self):
        outside=Path(self.tmp.name)/'elsewhere.csv';outside.write_text(self.table)
        self.candidate.unlink()
        try:self.candidate.symlink_to(outside)
        except OSError:self.skipTest('Symlinks unavailable')
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_headers_disagree(self):
        self.candidate.write_text(self.table.replace('FLF_KWEL_m3','other'));self.record()
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_row_count(self):
        self.candidate.write_text(self.table+'3,1,2\n');self.record()
        with self.assertRaises(ValueError):c.compare_stage(self.ctx)

    def test_cli_returns_2_for_difference(self):
        self.candidate.write_text(self.table.replace('1,2,3','1,9,3'));self.record()
        with patch.object(c.p,'load_context',return_value=self.ctx):
            self.assertEqual(c.main(['compare']),2)

    def test_cli_check_reference(self):
        with patch.object(c.p,'load_context',return_value=self.ctx):
            self.assertEqual(c.main(['check-reference']),0)


if __name__=='__main__':unittest.main()
