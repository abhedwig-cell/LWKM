import sqlite3

from tools.swp_context import build_context, validate_context


def _make_db(path):
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
        create table Scenario(
          scenario_id text, SWDRA real, SWBOTB real, GWLI real, SWINCO real
        );
        create table Output(crop_id real, INLIST_CSV text);
        create table Gewasweerstand(crop_id real, RSOIL real);
        create table DZNEW(dikte_id real, ICOMP real, DZNEW real);
        create table Wortelzone(soil_id real, croporg_id real, RDS real);
        """
    )
    con.execute(
        "insert into Runs values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            2000,"direct",79,"__",1,2,"2000","2000","2000.met",
            "max",2,-47,40,0.2,0.25,365,18992,0,3015,1,1,1700,2,
        ),
    )
    con.executemany(
        "insert into discretisatie values (?,?,?,?,?,?)",
        [(79,1,1,25,25,1700),(79,2,2,15,15,1700)],
    )
    con.executemany(
        "insert into eigenschappen values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (79,1,0.02,0.433878,0.021645,1.34877,83.241635,7.202077,0,83.241635,1364.866969,1e-6,0.87,0.10,0.03,0.057),
            (79,2,0.02,0.387064,0.016083,1.524418,22.761756,2.439662,0,22.761756,1575.905892,1e-6,0.89,0.08,0.03,0.022),
        ],
    )
    con.executemany(
        "insert into Gewasrotatie values (?,?,?,?,?,?,?,?)",
        [
            ("__",1,"max",0,364,"gras_maaien","gras_maaien",2),
            ("__",1,"max",365,729,"gras_maaien","gras_maaien",2),
        ],
    )
    # Scenario.SWINCO deliberately differs. Runs.SWINCO is the render authority.
    con.execute("insert into Scenario values ('direct',1,2,null,3)")
    con.execute("insert into Output values (1,'VOLACT,GWL,WATBAL')")
    con.execute("insert into Gewasweerstand values (1,600)")
    con.executemany("insert into DZNEW values (?,?,?)",[(1700,1,5),(1700,2,10)])
    # Deliberate legacy QA mismatch: this must not block current production RDS.
    con.execute("insert into Wortelzone values (3015,1,120)")
    con.commit()
    con.close()


def test_context_binds_current_10242_authority(tmp_path):
    db=tmp_path/"model.sqlite"
    _make_db(db)
    ctx=build_context(db,2000)
    validate_context(ctx)

    assert ctx["renderable"]
    assert ctx["TSTART"]=="1971-01-01"
    assert ctx["TEND"]=="2021-12-31"
    assert ctx["METFIL"]=="'2000.met'"
    assert ctx["SWETR"]==0
    assert ctx["SWINCO"]==2
    assert ctx["SWITCH_SWINCO_OPTION_2"]
    assert ctx["GWLI"]==-47
    assert ctx["RDS"]==40
    assert ctx["RDS_effective"]==40
    assert ctx["RDS_wortelzone"]==120
    assert any("Runs is production authority" in x for x in ctx["diagnostics"])
    assert ctx["SWDRA"]==1
    assert ctx["DRFIL"]=="'2000'"
    assert ctx["BBCFIL"]=="'2000'"
    assert ctx["SWBOTB"]==2
    assert ctx["NUMNODNEW"]==2
    assert ctx["DZNEW"]=="5.0 10.0"
    assert ctx["TABLE_SOILHYDRFUNC"][0]["ELAS"]==1e-6
    assert ctx["TABLE_CROPROTATION"][0]=={
        "CROPSTART":"1970-01-01",
        "CROPEND":"1970-12-31",
        "CROPNAME":"'gras_maaien'",
        "CROPFIL":"'gras_maaien'",
        "CROPTYPE":2,
    }


def test_context_fails_when_dznew_count_disagrees(tmp_path):
    db=tmp_path/"model.sqlite"
    _make_db(db)
    con=sqlite3.connect(db)
    con.execute("delete from DZNEW where ICOMP=2")
    con.commit()
    con.close()
    ctx=build_context(db,2000)
    assert not ctx["renderable"]
    assert any("DZNEW row count" in x for x in ctx["issues"])
