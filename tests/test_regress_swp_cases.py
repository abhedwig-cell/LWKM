import json
import sqlite3

import yaml

from tools.regress_swp_cases import regress_cases


LEGACY_TEMPLATE="""TSTART = {{TSTART}}
TEND = {{TEND}}
SWWBA = 0 ! output
PERIOD = 0 ! output
SWAUN = 2 ! output
SWODAT = 1 ! output
INLIST_CSV = {{INLIST_CSV}}
METFIL = {{METFIL}}
SWETR = 0 ! evap
SWINCO = {{SWINCO}}
GWLI = {{GWLI}}
PONDMX = {{PONDMX}}
RSRO = {{RSRO}}
RDS = {{RDS}}
SWDRA = {{SWDRA}}
DRFIL = {{DRFIL}}
SWBBCFILE = {{SWBBCFILE}}
BBCFIL = {{BBCFIL}}
SWBOTB = {{SWBOTB}}
NUMNODNEW = {{NUMNODNEW}}

{{#TABLE_CROPROTATION}}
{{CROPSTART}} {{CROPEND}} {{CROPNAME}} {{CROPFIL}} {{CROPTYPE}}
{{/TABLE_CROPROTATION}}

{{#TABLE_SOILPROFILE}}
{{ISUBLAY}} {{ISOILLAY}} {{HSUBLAY}} {{NCOMP}}
{{/TABLE_SOILPROFILE}}

{{#TABLE_SOILHYDRFUNC}}
{{ORES}} {{OSAT}} {{ALFA}} {{NPAR}} {{KSATFIT}} {{LEXP}} {{H_ENPR}} {{KSATEXM}} {{BDENS}} {{ELAS}}
{{/TABLE_SOILHYDRFUNC}}

{{#TABLE_SOILTEXTURES}}
{{PSAND}} {{PSILT}} {{PCLAY}} {{ORGMAT}}
{{/TABLE_SOILTEXTURES}}
"""


ORACLE="""TSTART = 1971-01-01
TEND = 2021-12-31
SWWBA = 1
PERIOD = 1
SWAUN = 0
SWODAT = 0
INLIST_CSV = 'WATBAL'
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
NUMNODNEW = 1

    CROPSTART     CROPEND       CROPNAME        CROPFIL  CROPTYPE
1970-01-01 1970-12-31 'grass' 'grass' 2
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


def _db(path):
    con=sqlite3.connect(path)
    con.executescript(
        """
        create table Runs(
          run_id real, scenario_id text, bodem_id real, climate_id text,
          SWBBCFILE real, SWBOTB real, BBCFIL text, DRFIL text, METFIL text,
          rotation_id text, SWINCO real, GWLI real, RDS real, PONDMX real,
          RSRO real, TSTART real, TEND real, SWETR real, soil_id real,
          crop_id real, croporg_id real, dikte_id real, NUMNODNEW real
        );
        create table discretisatie(
          bodem_id real, ISUBLAY real, ISOILLAY real, HSUBLAY real,
          NCOMP real, dikte_id real
        );
        create table eigenschappen(
          bodem_id real, ISOILLAY real, ORES real, OSAT real, ALFA real,
          NPAR real, KSATFIT real, LEXP real, H_ENPR real, KSATEXM real,
          BDENS real, ELAS real, PSAND real, PSILT real, PCLAY real, ORGMAT real
        );
        create table Gewasrotatie(
          climate_id text, crop_id real, rotation_id text, CROPSTART real,
          CROPEND real, CROPNAME text, CROPFIL text, CROPTYPE real
        );
        create table Scenario(scenario_id text, SWDRA real, SWBOTB real, GWLI real, SWINCO real);
        create table Output(crop_id real, INLIST_CSV text);
        create table Gewasweerstand(crop_id real, RSOIL real);
        create table DZNEW(dikte_id real, ICOMP real, DZNEW real);
        create table Wortelzone(soil_id real, croporg_id real, RDS real);
        """
    )
    con.execute(
        "insert into Runs values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (2000,"direct",79,"__",1,2,"2000","2000","2000.met","max",2,-47,40,0.2,0.25,365,18992,0,3015,1,1,1700,1),
    )
    con.execute("insert into discretisatie values (79,1,1,25,25,1700)")
    con.execute(
        "insert into eigenschappen values (79,1,0.02,0.43,0.02,1.4,80,3,0,80,1400,0.000001,0.87,0.10,0.03,0.057)"
    )
    con.execute("insert into Gewasrotatie values ('__',1,'max',0,364,'grass','grass',2)")
    con.execute("insert into Scenario values ('direct',1,2,null,3)")
    con.execute("insert into Output values (1,'OLD')")
    con.execute("insert into Gewasweerstand values (1,600)")
    con.execute("insert into DZNEW values (1700,1,5)")
    con.execute("insert into Wortelzone values (3015,1,120)")
    con.commit()
    con.close()


def _profile(path):
    path.write_text(yaml.safe_dump({
        "renderer_output":{
            "SWWBA":1,"PERIOD":1,"SWAUN":0,"SWODAT":0,
            "INLIST_CSV":"'WATBAL'",
        }
    }))


def test_multirun_harness_passes_exact_case(tmp_path):
    db=tmp_path/"m.sqlite";_db(db)
    template=tmp_path/"legacy.swp";template.write_text(LEGACY_TEMPLATE)
    profile=tmp_path/"profile.yml";_profile(profile)
    case=tmp_path/"cases"/"run_000002000";case.mkdir(parents=True)
    (case/"swap.swp").write_text(ORACLE)

    result=regress_cases(
        database=db,legacy_template=template,profile_path=profile,cases_root=tmp_path/"cases"
    )
    assert result["case_count"]==1
    assert result["admission_candidate"]
    assert result["cases"][0]["status"]=="PASS"


def test_expected_difference_must_be_observed_exactly(tmp_path):
    db=tmp_path/"m.sqlite";_db(db)
    template=tmp_path/"legacy.swp";template.write_text(LEGACY_TEMPLATE)
    profile=tmp_path/"profile.yml";_profile(profile)
    case=tmp_path/"cases"/"run_000002000";case.mkdir(parents=True)
    (case/"swap.swp").write_text(ORACLE.replace("RDS = 40.0","RDS = 120.0"))

    no_expected=regress_cases(
        database=db,legacy_template=template,profile_path=profile,cases_root=tmp_path/"cases"
    )
    assert not no_expected["admission_candidate"]
    assert no_expected["cases"][0]["unexplained"]==["assignments.RDS"]

    expected=tmp_path/"expected.yml"
    expected.write_text("expected_differences:\n  2000:\n    - assignments.RDS\n")
    qualified=regress_cases(
        database=db,legacy_template=template,profile_path=profile,cases_root=tmp_path/"cases",
        expected_differences=expected,
    )
    assert qualified["admission_candidate"]
    assert qualified["cases"][0]["status"]=="EXPECTED_DIFFERENCE"
