import sqlite3

from tools.audit_swp_datamodel import audit_database


def _make_db(path):
    con=sqlite3.connect(path)
    con.executescript(
        """
        create table Runs(
          run_id real, scenario_id text, bodem_id real, dikte_id real,
          climate_id text, crop_id real, rotation_id text, soil_id real,
          croporg_id real, NUMNODNEW real, SWINCO real, SWBBCFILE real,
          SWBOTB real, SWETR real, irrigation_id real, TSTART real, TEND real,
          RDS real
        );
        create table discretisatie(bodem_id real,dikte_id real);
        create table eigenschappen(bodem_id real,ELAS real);
        create table Gewasrotatie(climate_id text,crop_id real,rotation_id text);
        create table Output(crop_id real);
        create table Gewasweerstand(crop_id real);
        create table Scenario(scenario_id text);
        create table DZNEW(dikte_id real,ICOMP real);
        create table Wortelzone(soil_id real,croporg_id real,RDS real);
        """
    )
    con.execute(
        "insert into Runs values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (1,"direct",79,1700,"__",1,"max",3015,1,2,2,1,2,0,0,365,18992,40),
    )
    con.execute("insert into discretisatie values (79,1700)")
    con.execute("insert into eigenschappen values (79,0.000001)")
    con.execute("insert into Gewasrotatie values ('__',1,'max')")
    con.execute("insert into Output values (1)")
    con.execute("insert into Gewasweerstand values (1)")
    con.execute("insert into Scenario values ('direct')")
    con.executemany("insert into DZNEW values (?,?)",[(1700,1),(1700,2)])
    con.execute("insert into Wortelzone values (3015,1,120)")
    con.commit()
    con.close()


def test_datamodel_audit_separates_required_joins_from_rds_qa(tmp_path):
    db=tmp_path/"m.sqlite"
    _make_db(db)
    result=audit_database(db)
    assert result["runs"]==1
    assert result["all_required_renderer_joins_complete"]
    assert all(v==0 for v in result["checks"].values())
    assert result["rds_wortelzone_qa"]["missing"]==0
    assert result["rds_wortelzone_qa"]["mismatch"]==1
    assert result["distributions"]["SWINCO"]=={"2.0":1}
