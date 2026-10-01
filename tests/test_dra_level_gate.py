import unittest
from tools.dra_semantic_oracle import parse_dra, compare_dra


class LevelGateTests(unittest.TestCase):
    def test_changed_and_missing_seasonal_levels_are_failures(self):
        original = parse_dra('DRARES1 = 20\nDATOWL1 LEVEL1\n01-jan-1971 -50\n01-apr-1971 -30\n* End of table\n')
        changed = parse_dra('DRARES1 = 20\nDATOWL1 LEVEL1\n01-jan-1971 -50\n01-apr-1971 -31\n* End of table\n')
        self.assertEqual([d.path for d in compare_dra(original, changed)], ['systems.1.LEVEL.01-apr-1971'])
        missing = parse_dra('DRARES1 = 20\n')
        self.assertEqual(len(compare_dra(original, missing)), 2)

    def test_extra_assignment_is_a_failure(self):
        self.assertEqual([d.path for d in compare_dra(parse_dra(''), parse_dra('SWDIVD = 1'))], ['global.SWDIVD'])

    def test_duplicate_dates_rejected(self):
        with self.assertRaises(ValueError):
            parse_dra('DATOWL1 LEVEL1\n01-jan-1971 -50\n01-jan-1971 -40\n')
