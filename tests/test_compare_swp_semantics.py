import json
from pathlib import Path

from tools.compare_swp_semantics import compare_candidate, main


FIXTURE = Path("tests/fixtures/swp/run_2000_semantics.json")


def _minimal_run2000_text() -> str:
    d = json.loads(FIXTURE.read_text())
    s = d["scalars"]
    p = d["tables"]["soil_profile"]
    h = d["tables"]["soil_hydraulics"]
    t = d["tables"]["soil_textures"]
    lines = [
        f"TSTART = {s['TSTART']}",
        f"TEND = {s['TEND']}",
        f"METFIL = '{s['METFIL']}'",
        f"SWETR = {s['SWETR']}",
        f"SWINCO = {s['SWINCO']}",
        f"GWLI = {s['GWLI']}",
        f"PONDMX = {s['PONDMX']}",
        f"RSRO = {s['RSRO']}",
        f"RDS = {s['RDS']}",
        f"SWDRA = {s['SWDRA']}",
        f"DRFIL = '{s['DRFIL']}'",
        f"SWBBCFILE = {s['SWBBCFILE']}",
        f"BBCFIL = '{s['BBCFIL']}'",
        f"SWBOTB = {s['SWBOTB']}",
        f"NUMNODNEW = {s['NUMNODNEW']}",
        "",
        "ISUBLAY ISOILLAY HSUBLAY NCOMP",
    ]
    lines += [f"{r['ISUBLAY']} {r['ISOILLAY']} {r['HSUBLAY']} {r['NCOMP']}" for r in p]
    lines += ["* End of table", "", "ORES OSAT ALFA NPAR KSATFIT LEXP H_ENPR KSATEXM BDENS ELAS"]
    lines += [
        " ".join(str(r[k]) for k in ("ORES","OSAT","ALFA","NPAR","KSATFIT","LEXP","H_ENPR","KSATEXM","BDENS","ELAS"))
        for r in h
    ]
    lines += ["* End of table", "", "PSAND PSILT PCLAY ORGMAT"]
    lines += [
        " ".join(str(r[k]) for k in ("PSAND","PSILT","PCLAY","ORGMAT"))
        for r in t
    ]
    lines += ["* End of table", ""]
    return "\n".join(lines)


def test_run2000_fixture_matches_candidate(tmp_path):
    candidate = tmp_path / "2000.swp"
    candidate.write_text(_minimal_run2000_text())
    assert compare_candidate(candidate, FIXTURE) == []
    assert main([str(candidate), str(FIXTURE)]) == 0


def test_run2000_fixture_detects_rds_change(tmp_path):
    candidate = tmp_path / "2000.swp"
    candidate.write_text(_minimal_run2000_text().replace("RDS = 40.0", "RDS = 120.0"))
    diffs = compare_candidate(candidate, FIXTURE)
    assert [d.path for d in diffs] == ["scalars.RDS"]
    assert main([str(candidate), str(FIXTURE)]) == 1
