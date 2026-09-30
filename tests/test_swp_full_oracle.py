from tools.swp_full_oracle import compare_text, parse_full_swp


BASE="""TSTART = 1971-01-01
RDS = 40.0
DRFIL = '2000'
BBCFIL = '2000'

    CROPSTART     CROPEND       CROPNAME        CROPFIL  CROPTYPE
1971-01-01 1971-12-31 'grass' 'grass' 2
* End of table

   ISUBLAY  ISOILLAY  HSUBLAY  NCOMP
1 1 25.0 25
* End of table

   ORES      OSAT      ALFA      NPAR   KSATFIT      LEXP  H_ENPR   KSATEXM     BDENS      ELAS
0.02 0.43 0.02 1.4 80.0 3.0 0.0 80.0 1400.0 0.000001
* End of table

   PSAND  PSILT  PCLAY  ORGMAT
0.87 0.10 0.03 0.057
* End of table
"""


def test_full_parser_preserves_quoted_numeric_references_and_tables():
    parsed=parse_full_swp(BASE)
    assert parsed["assignments"]["DRFIL"]==["2000"]
    assert parsed["assignments"]["BBCFIL"]==["2000"]
    assert parsed["tables"]["TABLE_CROPROTATION"][0][2]=="grass"
    assert parsed["tables"]["TABLE_SOILHYDRFUNC"][0][-1]==1e-6


def test_full_compare_ignores_comments_and_numeric_formatting():
    changed=BASE.replace("RDS = 40.0","RDS = 40.000 ! same")
    assert compare_text(BASE,changed)==[]


def test_full_compare_reports_scalar_and_table_paths():
    changed=BASE.replace("RDS = 40.0","RDS = 120.0")
    changed=changed.replace("0.000001","0.000002")
    paths=[d.path for d in compare_text(BASE,changed)]
    assert "assignments.RDS" in paths
    assert "tables.TABLE_SOILHYDRFUNC[0][9]" in paths
