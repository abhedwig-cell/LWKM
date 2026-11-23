import copy
import math
import unittest

from donor_profile import (HYDRO_COLUMNS, PRESERVED_COLUMNS, apply_profile,
                           equivalent_annual_volume, validate_row)
from schema import AREA, COUNT, FLAG, HEADERS, ID, NET, P5, P95, REGION


def sample(sid=11, area='75000', factor=1.0):
    row = {column: '0' for column in HEADERS}
    row.update({ID: str(sid), COUNT: '1', AREA: str(area),
                'Landuse LHM (22)': '1', 'Landuse ANIMO (4 tekst)': 'gras',
                'LU4': '1', 'LU2': '1', 'Bodem370': '181', 'Bodem79': '47',
                'Pawn21': '4', 'Grondsoort4': '3', 'Grondsoort 2': '2',
                'Gtnr': '3', 'Kwelklasse4': '4', REGION: '17', FLAG: '0',
                'GLG m-mv': '1.2', 'GHG m-mv': '0.4',
                'GG ((GHG+GLG)/2)': '0.8', 'Dynamiek (GLG-GHG)': '0.8',
                P5: '0.13', P95: '1.63'})
    flows = {'Neerslag (mm/j)': 800, 'Beregening': 25, 'Evapotranspiratie': 600,
             'Verdamping gewas': 450, 'verdamping interceptie': 100,
             'Verdamping bodem': 50, 'Oppervlakkige afstroming': 40,
             'Ontwatering': 170, 'Fldrou1': 80, 'Fldrou2': 40, 'Fldrou3': 30,
             'Fldrou4': 15, 'Fldrou5': 5, 'Infiltratie': 36,
             'Fldrin1': 10, 'Fldrin2': 20, 'Fldrin345': 6, NET: 10,
             'Laterale stroming (netto)': -12, 'Onttrekkingen (uit laag 1)': 7,
             'General head boundary': -3, 'Wegzijging': 5, 'Kwel': 15,
             'QModF': -99, 'Bergingsverandering (MetaSWAP)': 2,
             'Waterbalansfout MetaSWAP': 0.125, 'Waterbalansfout overall': -0.25}
    row.update({column: str(value * factor) for column, value in flows.items()})
    return row


class DonorProfileTests(unittest.TestCase):
    def test_whole_profile_uses_donor_intensities_and_target_identity_area(self):
        target = sample(area='87500')
        donor = sample(sid=22, area='25000', factor=1.25)
        donor.update({'Landuse LHM (22)': '12', 'Landuse ANIMO (4 tekst)': 'natuur',
                      'LU4': '4', 'LU2': '2', 'Bodem370': '80', 'Bodem79': '19',
                      'Pawn21': '2', 'Grondsoort4': '1', 'Grondsoort 2': '1',
                      REGION: '26', 'Gtnr': '7', 'Kwelklasse4': '2'})
        before = (copy.deepcopy(target), copy.deepcopy(donor))
        result = apply_profile(target, donor, True)
        self.assertEqual(len(result), 49)
        self.assertEqual({key: result[key] for key in PRESERVED_COLUMNS},
                         {key: target[key] for key in PRESERVED_COLUMNS})
        self.assertEqual({key: result[key] for key in HYDRO_COLUMNS},
                         {key: donor[key] for key in HYDRO_COLUMNS})
        self.assertEqual(result[FLAG], '1')
        self.assertEqual(result['Neerslag (mm/j)'], '1000.0')
        self.assertEqual(equivalent_annual_volume(result, 'Neerslag (mm/j)'), 87500)
        self.assertEqual(equivalent_annual_volume(donor, 'Neerslag (mm/j)'), 25000)
        self.assertEqual(result['Gtnr'], '7')
        self.assertEqual(result['Kwelklasse4'], '2')
        self.assertNotEqual(result['QModF'], target['QModF'])
        self.assertEqual(result['Waterbalansfout overall'], '-0.3125')
        self.assertEqual((target, donor), before)
        validate_row(result)

    def test_nonsuspect_different_donor_does_not_trigger_replacement(self):
        target = sample()
        target[FLAG] = '1'  # Een al toegepaste Flevolandcorrectie blijft staan.
        donor = sample(sid=99, factor=4)
        result = apply_profile(target, donor, False)
        self.assertEqual(result, target)
        self.assertIsNot(result, target)
        self.assertEqual(apply_profile(target, None, False), target)
        self.assertEqual(apply_profile(target, {'unused': 'invalid'}, False), target)

    def test_equal_profile_still_marks_applied_replacement(self):
        target, donor = sample(sid=11), sample(sid=22)
        result = apply_profile(target, donor, True)
        self.assertEqual(result[FLAG], '1')
        self.assertEqual(result[ID], '11')
        self.assertEqual(result['Kwel'], target['Kwel'])

    def test_missing_donor_values_are_not_filled_from_target_or_zero(self):
        target, donor = sample(sid=11), sample(sid=22)
        for column in ('QModF', 'Waterbalansfout MetaSWAP', 'Waterbalansfout overall',
                       'Fldrou3', P5):
            donor[column] = ''
        result = apply_profile(target, donor, True)
        for column in ('QModF', 'Waterbalansfout MetaSWAP', 'Waterbalansfout overall',
                       'Fldrou3', P5):
            self.assertEqual(result[column], '')
        self.assertIsNone(equivalent_annual_volume(result, 'QModF'))
        self.assertEqual(result['Ontwatering'], donor['Ontwatering'])

    def test_groundwater_statistics_remain_distinct_and_literal(self):
        target, donor = sample(sid=11), sample(sid=22)
        donor.update({'GLG m-mv': '2.50', 'GHG m-mv': '0.50',
                      'GG ((GHG+GLG)/2)': '1.50', 'Dynamiek (GLG-GHG)': '2.00',
                      P5: '0.100', P95: '3.700'})
        result = apply_profile(target, donor, True)
        self.assertEqual(result['GLG m-mv'], '2.50')
        self.assertEqual(result['GHG m-mv'], '0.50')
        self.assertEqual(result[P5], '0.100')
        self.assertEqual(result[P95], '3.700')
        self.assertNotEqual(result['GLG m-mv'], result[P95])
        self.assertNotEqual(result['GHG m-mv'], result[P5])

    def test_source_variant_is_preserved_without_second_flevoland_change(self):
        target = sample(sid=11)
        raw = sample(sid=22)
        corrected = dict(raw)
        corrected.update({'Kwel': '12.0', NET: '7.0', 'Fldrin1': '13.0',
                          'Infiltratie': '39.0', FLAG: '1', 'Kwelklasse4': '2'})
        result_raw = apply_profile(target, raw, True)
        result_corrected = apply_profile(target, corrected, True)
        self.assertEqual(result_raw['Kwel'], '15.0')
        self.assertEqual(result_corrected['Kwel'], '12.0')
        self.assertEqual(result_corrected['Fldrin1'], '13.0')
        self.assertEqual(result_corrected['Waterbalansfout overall'], raw['Waterbalansfout overall'])
        # De gelijke tegengestelde veranderingen blijven in hetzelfde profiel.
        self.assertAlmostEqual(float(result_corrected[NET]) + float(result_corrected['Infiltratie']),
                               float(result_raw[NET]) + float(result_raw['Infiltratie']))

    def test_nonpositive_and_nonfinite_areas_are_rejected_but_large_areas_pass(self):
        for value in ('0', '-1', 'nan', 'inf', '-inf', ''):
            with self.subTest(area=value):
                with self.assertRaises(ValueError):
                    validate_row(sample(area=value))
        for value in ('62500', '62500.01', '75000', '87500'):
            validate_row(sample(area=value))

    def test_nonfinite_numeric_fields_are_rejected(self):
        for column in ('QModF', P5, 'Waterbalansfout overall', 'Beregening'):
            for value in ('nan', 'inf', '-inf', 'not-a-number'):
                with self.subTest(column=column, value=value):
                    row = sample()
                    row[column] = value
                    with self.assertRaises(ValueError):
                        validate_row(row)

    def test_required_shape_identity_count_and_flag_are_checked(self):
        for field, value in ((ID, '0'), (ID, '11.0'), (COUNT, '2'), (COUNT, ''),
                             (FLAG, ''), (FLAG, '2'), (FLAG, '0.0')):
            with self.subTest(field=field, value=value):
                row = sample()
                row[field] = value
                with self.assertRaises(ValueError):
                    validate_row(row)
        for mutation in ('missing', 'extra', 'null', 'bool'):
            row = sample()
            if mutation == 'missing':
                del row[P95]
            elif mutation == 'extra':
                row['HRU'] = '5'
            elif mutation == 'null':
                row['QModF'] = None
            else:
                row['QModF'] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_row(row)

    def test_head_order_and_component_relationships_are_checked(self):
        invalid = [('GHG m-mv', '1.3'), (P5, '2'),
                   ('GG ((GHG+GLG)/2)', '0.9'), ('Dynamiek (GLG-GHG)', '0.7'),
                   (NET, '11'), ('Ontwatering', '171'), ('Infiltratie', '37')]
        for field, value in invalid:
            row = sample()
            row[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_row(row)
        # Afronding van de aanwezige bronsommen mag geen nieuwe stop veroorzaken.
        row = sample()
        row['Ontwatering'] = '170.00001'
        validate_row(row)

    def test_partial_missing_relations_are_not_recomputed(self):
        row = sample()
        row['GLG m-mv'] = ''
        row['Fldrin2'] = ''
        row[NET] = ''
        validate_row(row)
        result = apply_profile(sample(sid=22), row, True)
        self.assertEqual(result['GLG m-mv'], '')
        self.assertEqual(result['GG ((GHG+GLG)/2)'], '0.8')
        self.assertEqual(result['Infiltratie'], '36.0')
        self.assertEqual(result[NET], '')

    def test_explicit_suspect_boolean_and_required_donor(self):
        for status in (0, 1, '0', '1', None):
            with self.subTest(status=status), self.assertRaises(ValueError):
                apply_profile(sample(), sample(sid=22), status)
        with self.assertRaises(ValueError):
            apply_profile(sample(), None, True)

    def test_volume_conversion_has_signed_and_missing_semantics(self):
        row = sample(area='75000')
        self.assertEqual(equivalent_annual_volume(row, 'Laterale stroming (netto)'), -900)
        self.assertAlmostEqual(equivalent_annual_volume(row, 'Waterbalansfout MetaSWAP'), 9.375)
        with self.assertRaises(ValueError):
            equivalent_annual_volume(row, 'GLG m-mv')
        row['QModF'] = '1e308'
        with self.assertRaises(ValueError):
            equivalent_annual_volume(row, 'QModF')


if __name__ == '__main__':
    unittest.main()
