from pathlib import Path

from tools.build_bodem370_lookup import (
    KNOWN_CORRECTIONS,
    UNOBSERVED,
    read,
    validate,
)


def test_known_corrections_are_guarded():
    assert KNOWN_CORRECTIONS[78]==(40,39)
    assert KNOWN_CORRECTIONS[95]==(28,31)
    assert KNOWN_CORRECTIONS[171]==(39,44)
    assert UNOBSERVED=={14,142,143,197,198}


def test_persisted_canonical_lookup_is_complete_and_qualified():
    path=Path("config/p12/bodem370_classification_lookup.csv")
    rows=read(path)
    assert validate(rows)
    observed={int(r["bodem370"]):r for r in rows if r["status"]=="QUALIFIED_REALIZED"}
    assert int(observed[78]["bofek79"])==40
    assert int(observed[79]["bofek79"])==39
    assert int(observed[147]["bofek79"])==46
    assert int(observed[148]["bofek79"])==41
