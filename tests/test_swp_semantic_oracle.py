from tools.swp_semantic_oracle import compare_text, extract_semantics


BASE = """TSTART = 1971-01-01
TEND = 2021-12-31
METFIL = '2000.met'
SWETR = 0
SWINCO = 2
GWLI = -47.0
PONDMX = 0.2
RSRO = 0.25
RDS = 40.0
SWDRA = 1
DRFIL = '2000'
SWBBCFILE = 1
BBCFIL = '2000'
SWBOTB = 2
NUMNODNEW = 43

ISUBLAY ISOILLAY HSUBLAY NCOMP
1 1 20.0 4
2 2 30.0 6
* End of table

ORES OSAT ALFA NPAR KSATFIT LEXP H_ENPR KSATEXM BDENS ELAS
0.02 0.433878 0.021645 1.348770 83.24164 7.202077 0.0 83.24164 1364.867 0.000001
0.01 0.365847 0.015987 2.162751 22.32215 2.867967 0.0 22.32215 1671.779 0.000001
* End of table

PSAND PSILT PCLAY ORGMAT
70.0 20.0 10.0 2.0
30.0 30.0 40.0 4.0
* End of table
"""


def test_extract_run2000_gate_shape():
    got = extract_semantics(BASE)
    assert got["scalars"]["METFIL"] == "2000.met"
    assert got["scalars"]["GWLI"] == -47.0
    assert got["scalars"]["RDS"] == 40.0
    assert got["tables"]["soil_hydraulics"][0]["ELAS"] == 1e-6
    assert len(got["tables"]["soil_profile"]) == 2


def test_comments_and_whitespace_do_not_matter():
    changed = BASE.replace("RDS = 40.0", "  RDS = 40.0000 ! same value")
    assert compare_text(BASE, changed) == []


def test_scalar_difference_is_discriminating():
    changed = BASE.replace("RDS = 40.0", "RDS = 120.0")
    diffs = compare_text(BASE, changed)
    assert [d.path for d in diffs] == ["scalars.RDS"]


def test_hydraulic_difference_is_discriminating():
    changed = BASE.replace("0.000001\n0.01", "0.000002\n0.01", 1)
    diffs = compare_text(BASE, changed)
    assert [d.path for d in diffs] == ["tables.soil_hydraulics[0].ELAS"]
