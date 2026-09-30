import json
from pathlib import Path

from tools.dra_semantic_oracle import compare_dra, parse_dra


FIXTURE=Path("tests/fixtures/dra/run_2000_dra_oracle.json")


def _text():
    d=json.loads(FIXTURE.read_text())
    lines=[
        "DRAMET = 3",
        "SWDIVD = 1",
        "SWDISLAY = 0",
        "NRLEVS = 5",
        "SWINTFL = 0",
        "SWTOPNRSRF = 0",
    ]
    for sy in range(1,6):
        r=d["systems"][str(sy)]
        for key in ("DRARES","INFRES","SWALLO","L","ZBOTDR","SWDTYP"):
            lines.append(f"{key}{sy} = {r[key]}")
    return "\n".join(lines)+"\n"


def test_run2000_fixture_parses_and_matches():
    expected=json.loads(FIXTURE.read_text())
    actual=parse_dra(_text())
    assert compare_dra(expected,actual)==[]


def test_parser_detects_spacing_change():
    expected=json.loads(FIXTURE.read_text())
    actual=parse_dra(_text().replace("L2 = 80.0","L2 = 84.0"))
    diffs=compare_dra(expected,actual)
    assert [d.path for d in diffs]==["systems.2.L"]


def test_comments_are_ignored():
    expected=json.loads(FIXTURE.read_text())
    actual=parse_dra(_text().replace("DRARES2 = 824.0","DRARES2 = 824.0 ! same"))
    assert compare_dra(expected,actual)==[]
