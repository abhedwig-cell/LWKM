import csv
import sqlite3

from tools.audit_p12_static_authority import audit


def _write_lookup(path):
    rows=[
        {"bodem370":1,"grondsoort2":1,"status":"QUALIFIED_REALIZED"},
        {"bodem370":2,"grondsoort2":2,"status":"QUALIFIED_REALIZED"},
    ]
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["bodem370","grondsoort2","status"])
        w.writeheader();w.writerows(rows)


def _write_db(path):
    con=sqlite3.connect(path)
    con.executescript(
        """
        create table Runs(
          run_id real,bodem_id real,soil2_id real,lu_id real,crop_id real,SWETR real
        );
        create table lu2crop(soil2_id real,luse_id real,crop_id real);
        """
    )
    con.executemany(
        "insert into lu2crop values (?,?,?)",
        [(1,1,1),(2,1,1),(1,2,26),(2,2,6),(1,11,22),(2,11,22)]
    )
    con.executemany(
        "insert into Runs values (?,?,?,?,?,?)",
        [
            (1,1,1,1,1,0),
            (2,2,1,2,26,0),
            (3,1,1,11,22,1),
        ],
    )
    con.commit();con.close()


def test_audit_detects_soil2_and_crop_effect_but_not_swetr(tmp_path):
    db=tmp_path/"m.sqlite"
    lookup=tmp_path/"lookup.csv"
    _write_db(db);_write_lookup(lookup)
    result=audit(db,lookup)
    assert result["runs"]==3
    assert result["swetr_mismatch_count"]==0
    assert result["soil2_mismatch_count"]==1
    assert result["crop_id_mismatch_count"]==1
    assert result["missing_canonical_soil_lookup_count"]==0
    assert result["crop_id_mismatches"][0]["run_id"]==2


def test_audit_flags_missing_lookup(tmp_path):
    db=tmp_path/"m.sqlite"
    lookup=tmp_path/"lookup.csv"
    _write_db(db);_write_lookup(lookup)
    con=sqlite3.connect(db)
    con.execute("insert into Runs values (4,3,1,1,1,0)")
    con.commit();con.close()
    result=audit(db,lookup)
    assert result["missing_canonical_soil_lookup_count"]==1
    assert result["missing_canonical_soil_lookup"][0]["bodem_id"]==3
