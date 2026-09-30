import pandas as pd

from tools.compare_nature_authority import compare_nature_authority, is_nature_lgn


def test_is_nature_lgn_matches_supplied_source_rule():
    assert not is_nature_lgn(10)
    assert is_nature_lgn(11)
    assert is_nature_lgn(17)
    assert not is_nature_lgn(18)
    assert is_nature_lgn(19)
    assert is_nature_lgn(20)
    assert not is_nature_lgn(21)


def test_compare_nature_authority_separates_landuse_and_nature_discrimination():
    schema = pd.DataFrame({
        "HRU": [1, 2],
        "svat_repr": [102, 202],
    })
    relation = pd.DataFrame({
        "HRU": [1, 1, 1, 2, 2, 2],
        "svat_orig": [101, 102, 103, 201, 202, 203],
    })
    attrs = pd.DataFrame({
        "svat": [101, 102, 103, 201, 202, 203],
        # HRU 1: legacy mode 11, representative 12. Land-use differs but both are nature.
        # HRU 2: legacy mode 10, representative 11. Nature classification differs.
        "landgebruik22": [11, 12, 11, 10, 11, 10],
    })

    result = compare_nature_authority(schema, relation, attrs).set_index("hru")

    assert result.loc[1, "legacy_lgn"] == 11
    assert result.loc[1, "representative_lgn"] == 12
    assert bool(result.loc[1, "lgn_discriminating"])
    assert not bool(result.loc[1, "nature_discriminating"])

    assert result.loc[2, "legacy_lgn"] == 10
    assert result.loc[2, "representative_lgn"] == 11
    assert bool(result.loc[2, "lgn_discriminating"])
    assert bool(result.loc[2, "nature_discriminating"])


def test_lower_tie_mode_matches_lowest_value_tie_rule():
    schema = pd.DataFrame({"HRU": [1], "svat_repr": [102]})
    relation = pd.DataFrame({"HRU": [1, 1], "svat_orig": [101, 102]})
    attrs = pd.DataFrame({
        "svat": [101, 102],
        "landgebruik22": [12, 11],
    })

    result = compare_nature_authority(schema, relation, attrs).iloc[0]
    assert result["legacy_lgn"] == 11
