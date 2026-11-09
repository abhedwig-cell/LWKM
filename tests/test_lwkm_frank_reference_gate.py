"""Regression for frozen original Frank SVAT manifest semantics."""
import unittest
from tools.lwkm_frank.reference_gate import REFERENCE_SHA, SOURCES, verify

def baseline():
    return {
        'expected_svats': 645582, 'count': 645582, 'period': '1991-2020',
        'missing_gebied': 88581,
        'outputs': {'table_sha256': REFERENCE_SHA},
        'sources': {key: {'sha256': 'a' * 64, 'path': key + '.csv'} for key in SOURCES},
        'formulas': {'GG': '(GHG+GLG)/2',
                     'OVERALL': 'signed sum; NO QMODF, NO MODFLOW STO/BND'}
    }

class TestReferenceGate(unittest.TestCase):
    def test_admit_manifest_contract(self):
        self.assertEqual(verify(baseline()), [])

    def test_reject_unauthorized_correction(self):
        m = baseline()
        m['outputs']['table_sha256'] = '0' * 64
        self.assertTrue(any('reference' in s for s in verify(m)))

    def test_reject_qmodf_double_count(self):
        m = baseline()
        m['formulas']['OVERALL'] = 'WRONG: plus qmodf'
        self.assertTrue(any('QModF' in s for s in verify(m)))

    def test_reject_incomplete_sources(self):
        m = baseline()
        del m['sources']['qmodf']
        self.assertTrue(any('source' in s for s in verify(m)))

if __name__ == '__main__':
    unittest.main()
