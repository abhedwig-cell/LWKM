import math
import unittest

from hru_aggregate import HruAggregator
from schema import HEADERS, NUMERIC_COLUMNS


def row(svat, area, value=10.0, flag=0, region="1"):
    result = {column: "" for column in HEADERS}
    result.update({
        HEADERS[0]: str(svat), HEADERS[1]: "1", HEADERS[2]: str(area),
        HEADERS[47]: str(flag), HEADERS[48]: region,
    })
    for column in NUMERIC_COLUMNS:
        result[column] = str(value)
    result.update({HEADERS[13]: "2.0", HEADERS[14]: "0.5", HEADERS[15]: "1.25", HEADERS[16]: "1.5"})
    return result


class TestHruAggregator(unittest.TestCase):
    def test_unequal_areas_conserve_weighted_flux_and_have_49_columns(self):
        aggregation = HruAggregator()
        aggregation.add(8, row(30, 100, 20))
        aggregation.add(8, row(10, 300, 60))
        result = list(aggregation.rows())[0]
        self.assertEqual(list(result), HEADERS)
        self.assertEqual(len(result), 49)
        self.assertEqual(result[HEADERS[0]], "8")
        self.assertEqual(result[HEADERS[1]], "2")
        self.assertEqual(float(result[HEADERS[2]]), 400)
        self.assertEqual(float(result[HEADERS[20]]), 50)
        self.assertEqual(float(result[HEADERS[20]]) * 400 / 1000, (20 * 100 + 60 * 300) / 1000)
        self.assertEqual(aggregation.diagnostics()["total_area_m2"], 400)

    def test_any_flag_and_multiple_regions_are_not_averaged(self):
        aggregation = HruAggregator()
        aggregation.add(3, row(1, 100, flag=0, region="10"))
        aggregation.add(3, row(2, 300, flag=1, region="2"))
        result = list(aggregation.rows())[0]
        self.assertEqual(result[HEADERS[47]], "1")
        self.assertEqual(result[HEADERS[48]], "2|10")
        diagnostics = aggregation.diagnostics()
        self.assertEqual(diagnostics["corrected_svats"], 1)
        self.assertEqual(diagnostics["corrected_hrus"], 1)
        self.assertEqual(diagnostics["corrected_area_m2"], 300)
        self.assertEqual(len(diagnostics["regions_multiple_or_missing"]), 1)

    def test_missing_numeric_blanks_entire_field_and_reports_area_coverage(self):
        aggregation = HruAggregator()
        first = row(1, 100, 20)
        second = row(2, 300, 60)
        second[HEADERS[20]] = ""
        aggregation.add(1, first)
        aggregation.add(1, second)
        result = list(aggregation.rows())[0]
        self.assertEqual(result[HEADERS[20]], "")
        self.assertEqual(float(result[HEADERS[21]]), 50)
        missing = aggregation.diagnostics()["numeric_missing"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["valid_svats"], 1)
        self.assertEqual(missing[0]["valid_area_fraction"], 0.25)
        self.assertEqual(missing[0]["output"], "blank")

    def test_all_missing_numeric_is_blank_not_zero(self):
        aggregation = HruAggregator()
        first = row(1, 100)
        first[HEADERS[20]] = None
        aggregation.add(1, first)
        self.assertEqual(list(aggregation.rows())[0][HEADERS[20]], "")
        self.assertEqual(aggregation.diagnostics()["numeric_missing"][0]["valid_area_m2"], 0)

    def test_official_categories_and_member_fallback_without_new_mode(self):
        aggregation = HruAggregator({7: {HEADERS[3]: "14"}})
        first, second = row(1, 100), row(2, 300)
        first[HEADERS[3]], second[HEADERS[3]] = "1", "9"
        first[HEADERS[7]], second[HEADERS[7]] = "10", "2"
        aggregation.add(7, first)
        aggregation.add(7, second)
        result = list(aggregation.rows())[0]
        self.assertEqual(result[HEADERS[3]], "14")
        self.assertEqual(result[HEADERS[7]], "2|10")
        diagnostics = aggregation.diagnostics()
        self.assertEqual(diagnostics["category_sources"][HEADERS[3]]["official_hru_schema"], 1)
        self.assertEqual(diagnostics["category_sources"][HEADERS[7]]["member_values"], 1)
        self.assertEqual(len(diagnostics["schema_values_not_present_in_members"]), 1)

    def test_current_kwel_classes_can_override_historical_schema(self):
        aggregation = HruAggregator({7: {HEADERS[19]: "4"}}, use_schema_kwelklasse=False)
        first, second = row(1, 100), row(2, 300)
        first[HEADERS[19]], second[HEADERS[19]] = "1", "2"
        aggregation.add(7, first)
        aggregation.add(7, second)
        result = list(aggregation.rows())[0]
        self.assertEqual(result[HEADERS[19]], "1|2")
        self.assertFalse(aggregation.diagnostics()["kwelklasse_uses_schema"])

    def test_region_missing_is_not_a_fake_region(self):
        aggregation = HruAggregator()
        aggregation.add(1, row(1, 100, region="4"))
        aggregation.add(1, row(2, 300, region=""))
        self.assertEqual(list(aggregation.rows())[0][HEADERS[48]], "4")
        coverage = aggregation.diagnostics()["regions_multiple_or_missing"][0]
        self.assertEqual(coverage["valid_svats"], 1)
        self.assertEqual(coverage["valid_area_fraction"], 0.25)

    def test_gg_and_dynamics_recomputed_from_glg_and_ghg(self):
        aggregation = HruAggregator()
        first, second = row(1, 100), row(2, 300)
        first.update({HEADERS[13]: "2", HEADERS[14]: "0", HEADERS[15]: "999", HEADERS[16]: "999"})
        second.update({HEADERS[13]: "4", HEADERS[14]: "2", HEADERS[15]: "999", HEADERS[16]: "999"})
        aggregation.add(1, first)
        aggregation.add(1, second)
        result = list(aggregation.rows())[0]
        self.assertEqual(float(result[HEADERS[13]]), 3.5)
        self.assertEqual(float(result[HEADERS[14]]), 1.5)
        self.assertEqual(float(result[HEADERS[15]]), 2.5)
        self.assertEqual(float(result[HEADERS[16]]), 2)

    def test_missing_glg_also_blanks_derived_fields(self):
        aggregation = HruAggregator()
        first, second = row(1, 100), row(2, 300)
        second[HEADERS[13]] = ""
        aggregation.add(1, first)
        aggregation.add(1, second)
        result = list(aggregation.rows())[0]
        self.assertEqual(result[HEADERS[13]], "")
        self.assertEqual(result[HEADERS[15]], "")
        self.assertEqual(result[HEADERS[16]], "")
        self.assertEqual(float(result[HEADERS[14]]), 0.5)

    def test_percentiles_are_member_summaries(self):
        aggregation = HruAggregator()
        first, second = row(1, 100), row(2, 300)
        first[HEADERS[17]], second[HEADERS[17]] = "0", "4"
        first[HEADERS[18]], second[HEADERS[18]] = "2", "8"
        aggregation.add(1, first)
        aggregation.add(1, second)
        result = list(aggregation.rows())[0]
        self.assertEqual(float(result[HEADERS[17]]), 3)
        self.assertEqual(float(result[HEADERS[18]]), 6.5)
        self.assertIn("not statistics recalculated", aggregation.diagnostics()["groundwater_statistics"])

    def test_duplicates_are_rejected_across_hrus(self):
        aggregation = HruAggregator()
        aggregation.add(1, row(5, 100))
        with self.assertRaisesRegex(ValueError, "Dubbele SVAT"):
            aggregation.add(2, row(5, 100))

    def test_membership_must_match(self):
        aggregation = HruAggregator(membership={1: 3})
        with self.assertRaisesRegex(ValueError, "membership"):
            aggregation.add(2, row(1, 100))
        with self.assertRaisesRegex(ValueError, "ontbreekt"):
            aggregation.add(3, row(4, 100))
        aggregation.add(3, row(1, 100))
        self.assertEqual(list(aggregation.rows())[0][HEADERS[0]], "3")

    def test_invalid_area_flag_count_and_nonfinite_values_rejected(self):
        for column, value in [(HEADERS[2], 0), (HEADERS[2], -1), (HEADERS[2], "nan"),
                              (HEADERS[47], 2), (HEADERS[1], 2), (HEADERS[20], "inf"),
                              (HEADERS[20], "nan"), (HEADERS[20], "geen getal")]:
            with self.subTest(column=column, value=value):
                aggregation = HruAggregator()
                bad = row(1, 100)
                bad[column] = value
                with self.assertRaises(ValueError):
                    aggregation.add(1, bad)
                self.assertEqual(list(aggregation.rows()), [])

    def test_sorted_hrus_and_no_correction_remain_zero(self):
        aggregation = HruAggregator()
        aggregation.add(10, row(1, 100))
        aggregation.add(2, row(2, 100))
        result = list(aggregation.rows())
        self.assertEqual([r[HEADERS[0]] for r in result], ["2", "10"])
        self.assertTrue(all(r[HEADERS[47]] == "0" for r in result))

    def test_signed_sum_keeps_small_contribution(self):
        aggregation = HruAggregator()
        for svat, value in enumerate((1e16, 1, -1e16), 1):
            aggregation.add(1, row(svat, 1, value))
        result = list(aggregation.rows())[0]
        self.assertTrue(math.isclose(float(result[HEADERS[38]]), 1 / 3, rel_tol=1e-14))

    def test_total_volume_conserved_across_multiple_hrus(self):
        aggregation = HruAggregator()
        source = [(1, 100, 42, 7), (2, 320, -23, 7), (3, 270, 15, 9), (4, 40, 0, 9)]
        for svat, area, flux, hru in source:
            aggregation.add(hru, row(svat, area, flux))
        svat_volume = math.fsum(area * flux / 1000 for _, area, flux, _ in source)
        hru_volume = math.fsum(float(r[HEADERS[2]]) * float(r[HEADERS[38]]) / 1000 for r in aggregation.rows())
        self.assertTrue(math.isclose(svat_volume, hru_volume, rel_tol=1e-13, abs_tol=1e-13))


if __name__ == "__main__":
    unittest.main()
