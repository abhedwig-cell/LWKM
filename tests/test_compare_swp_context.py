import json
import sqlite3

from tools.compare_swp_context import compare_context, main


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
        "insert into eigenschappen values (79,1,0.02,0.433878,0.021645,1.34877,83.24164,7.202077,0,83.24164,1364.867,0.000001,0.87,0.10,0.03,0.057)"
    )
    con.execute("insert into Gewasrotatie values ('__',1,'max',0,364,'gras_maaien','gras_maaien',2)")
    con.execute("insert into Scenario values ('direct',1,2,null,3)")
    con.execute("insert into Output values (1,'VOLACT,GWL,WATBAL')")
    con.execute("insert into Gewasweerstand values (1,600)")
    con.execute("insert into DZNEW values (1700,1,5)")
    con.execute("insert into Wortelzone values (3015,1,120)")
    con.commit()
    con.close()


def _oracle(path,rds=40):
    path.write_text(json.dumps({
        "scalars":{
            "TSTART":"1971-01-01","TEND":"2021-12-31","METFIL":"2000.met",
            "SWETR":0,"SWINCO":2,"GWLI":-47,"PONDMX":0.2,"RSRO":0.25,
            "RDS":rds,"SWDRA":1,"DRFIL":"2000","SWBBCFILE":1,
            "BBCFIL":"2000","SWBOTB":2,"NUMNODNEW":1,
        },
        "tables":{
            "soil_profile":[{"ISUBLAY":1,"ISOILLAY":1,"HSUBLAY":25,"NCOMP":25}],
            "soil_hydraulics":[{"ORES":0.02,"OSAT":0.433878,"ALFA":0.021645,"NPAR":1.34877,"KSATFIT":83.24164,"LEXP":7.202077,"H_ENPR":0,"KSATEXM":83.24164,"BDENS":1364.867,"ELAS":0.000001}],
            "soil_textures":[{"PSAND":0.87,"PSILT":0.10,"PCLAY":0.03,"ORGMAT":0.057}],
        },
    }))


def test_context_gate_matches_oracle(tmp_path):
    db=tmp_path/"m.sqlite"; oracle=tmp_path/"oracle.json"
    _db(db);_oracle(oracle)
    diffs,ctx=compare_context(db,2000,oracle)
    assert diffs==[]
    assert ctx["diagnostics"]
    assert main([str(db),"2000",str(oracle)])==0


def test_context_gate_detects_authority_difference(tmp_path):
    db=tmp_path/"m.sqlite"; oracle=tmp_path/"oracle.json"
    _db(db);_oracle(oracle,rds=120)
    diffs,_=compare_context(db,2000,oracle)
    assert [d.path for d in diffs]==["scalars.RDS"]
    assert main([str(db),"2000",str(oracle)])==1
