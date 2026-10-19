import json
import sqlite3
import pytest
from tools.build_production_packages import build


def setup(tmp_path, runs):
    db=tmp_path/'db.sqlite'
    with sqlite3.connect(db) as c:
        c.execute('create table Runs (run_id integer)')
        c.execute('insert into Runs values (1)')
    catalogue=tmp_path/'catalogue.json'
    catalogue.write_text(json.dumps(dict(schema_version=1,profile_id='test',et_policy='datamodel',expected_population=1,runs=runs)))
    return db,catalogue


def test_unbound_hru_is_explicit_external_blocker(tmp_path):
    db,c=setup(tmp_path,{})
    result=build(db,tmp_path/'unused',c,tmp_path/'out')
    assert result['complete_packages']==0
    assert result['runs'][0]['error'].startswith('EXTERNAL_INPUT_UNBOUND')
    assert result['production_admitted'] is False


def test_unknown_hru_does_not_silently_disappear(tmp_path):
    db,c=setup(tmp_path,{'2':{}})
    with pytest.raises(ValueError,match='unknown HRU'):build(db,tmp_path/'unused',c,tmp_path/'out')
