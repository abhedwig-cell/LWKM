import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1] / 'tools/lwkm_frank'
sys.path.insert(0, str(HERE))
import compare_v03 as c


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup)
        self.a, self.b = Path(self.t.name)/'a.csv', Path(self.t.name)/'b.csv'

    def run_compare(self, left, right, n=2):
        self.a.write_text(left); self.b.write_text(right)
        return c.compare(self.a, self.b, n)

    def test_exact(self):
        r=self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,x\n1,2\n2,3\n')
        self.assertTrue(r['equal_values']); self.assertTrue(r['byte_identical'])

    def test_numeric_format_not_value_difference(self):
        r=self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,x\n1,2.000\n2,3e0\n')
        self.assertTrue(r['equal_values']); self.assertFalse(r['byte_identical'])

    def test_no_rounding_tolerance(self):
        r=self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,x\n1,2.0000000000001\n2,3\n')
        self.assertFalse(r['equal_values'])

    def test_blank_not_zero(self):
        r=self.run_compare('SVAT,x\n1,\n2,3\n','SVAT,x\n1,0\n2,3\n')
        self.assertEqual(r['changed_cells_by_column'], {'x':1})

    def test_order_mismatch_stops(self):
        with self.assertRaises(ValueError): self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,x\n2,3\n1,2\n')

    def test_duplicate_stops(self):
        with self.assertRaises(ValueError): self.run_compare('SVAT,x\n1,2\n1,3\n','SVAT,x\n1,2\n1,3\n')

    def test_rowcount_stops(self):
        with self.assertRaises(ValueError): self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,x\n1,2\n')

    def test_header_stops(self):
        with self.assertRaises(ValueError): self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,y\n1,2\n2,3\n')

    def test_expected_count_stops(self):
        with self.assertRaises(ValueError): self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,x\n1,2\n2,3\n',3)

    def test_mutated_numeric_nan_not_equal_to_number(self):
        r=self.run_compare('SVAT,x\n1,2\n2,3\n','SVAT,x\n1,nan\n2,3\n')
        self.assertFalse(r['equal_values'])


if __name__ == '__main__': unittest.main()
