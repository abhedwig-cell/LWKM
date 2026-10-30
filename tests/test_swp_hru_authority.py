import unittest
from tools.swp_hru_authority import resolve


class AuthorityTests(unittest.TestCase):
    def run_case(self, hru=None, svats=None):
        return list(resolve(
            [hru or {'HRU': '1', 'svat_repr': '5', 'bodem370': '261'}],
            svats or [{'svat': '5', 'landgebruik22': '2', 'bodem370': '99'}],
            [{'bodem370': '261', 'grondsoort2': '1'}],
            [{'soil2_id': '1', 'luse_id': '2', 'crop_id': '26'},
             {'soil2_id': '1', 'luse_id': '10', 'crop_id': '19'}]))[0]

    def test_soil_is_from_hru_and_landuse_from_selected_svat(self):
        result = self.run_case()
        self.assertEqual((result['bodem370'], result['crop_id']), (261, 26))

    def test_explicit_landuse_wins(self):
        result = self.run_case({'HRU': '1', 'svat_repr': '5', 'bodem370': '261', 'landgebruik22': '10'})
        self.assertEqual((result['crop_id'], result['SWETR']), (19, 1))

    def test_ambiguous_svat_fails(self):
        with self.assertRaises(ValueError):
            self.run_case(svats=[{'svat': '5'}, {'svat': '5'}])

    def test_missing_representative_fails(self):
        with self.assertRaises(KeyError):
            self.run_case(svats=[{'svat': '6', 'landgebruik22': '2'}])
