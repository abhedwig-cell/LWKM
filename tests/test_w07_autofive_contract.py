from tools.w07_autofive_full_records import partitions


def test_five_level_search_covers_seven_sources():
    assert len(list(partitions(6, 4))) == 65
