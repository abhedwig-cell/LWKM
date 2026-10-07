from tools.dra_package_guard import resolve_lineage_level, resolve_numlevrapdra


LEVELS=[
    {"source_ids":("H1","P")},
    {"source_ids":("S","T")},
    {"source_ids":("PIPE",)},
    {"source_ids":("MVG","OLF")},
]


def test_lineage_level_is_postcompression_not_historical_number():
    assert resolve_lineage_level(LEVELS,["PIPE"])==3
    assert resolve_lineage_level(LEVELS,["H1","P"])==1


def test_no_index_binding_needed_when_macropore_rapid_drainage_is_off():
    assert resolve_numlevrapdra(
        LEVELS,swmacro=0,swdrrap=1,rapid_drainage_source_ids=None
    ) is None
    assert resolve_numlevrapdra(
        LEVELS,swmacro=1,swdrrap=0,rapid_drainage_source_ids=None
    ) is None


def test_active_macropore_rapid_drainage_requires_lineage():
    try:
        resolve_numlevrapdra(LEVELS,swmacro=1,swdrrap=1)
    except ValueError as exc:
        assert "explicit rapid-drainage source lineage" in str(exc)
    else:
        raise AssertionError("expected unbound rapid-drainage lineage to fail")


def test_configured_numlevrapdra_must_match_compressed_lineage():
    assert resolve_numlevrapdra(
        LEVELS,
        swmacro=1,
        swdrrap=1,
        rapid_drainage_source_ids=["PIPE"],
        configured_numlevrapdra=3,
    )==3
    try:
        resolve_numlevrapdra(
            LEVELS,
            swmacro=1,
            swdrrap=1,
            rapid_drainage_source_ids=["PIPE"],
            configured_numlevrapdra=4,
        )
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("expected stale hard-coded level number to fail")


def test_lineage_spanning_multiple_levels_cannot_be_bound_as_one_index():
    try:
        resolve_lineage_level(LEVELS,["H1","S"])
    except ValueError as exc:
        assert "exactly one SWAP level" in str(exc)
    else:
        raise AssertionError("expected split lineage to fail")
