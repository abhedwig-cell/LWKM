import hashlib
import pytest
from tools.file_qualification_gate import require_admitted


def record(tmp_path):
    p=tmp_path/'source';p.write_bytes(b'data')
    return {'x':{'path':str(p),'size_bytes':4,'sha256':hashlib.sha256(b'data').hexdigest(),
                 'qualification_status':'PRODUCTION_ADMITTED','consumers':['W06'],
                 'semantic_contract':'test-v1','evidence_refs':['test-evidence'],
                 'kind':'source','provenance':'explicit-test'}}


def test_consumer_identity_and_status_all_required(tmp_path):
    r=record(tmp_path)
    require_admitted(r,'x','W06')
    with pytest.raises(ValueError,match='consumer'):require_admitted(r,'x','W07')
    r['x']['qualification_status']='REGRESSION_QUALIFIED'
    with pytest.raises(ValueError,match='not production'):require_admitted(r,'x','W06')


def test_byte_change_rejected(tmp_path):
    r=record(tmp_path);(tmp_path/'source').write_bytes(b'edit')
    with pytest.raises(ValueError,match='identity'):require_admitted(r,'x','W06')


def test_cycle_rejected(tmp_path):
    r=record(tmp_path);r['x'].update(kind='derived',parents=['x'],producer='W06',
                                   code_commit='test',config_sha256='test')
    with pytest.raises(ValueError,match='cyclic'):require_admitted(r,'x','W06')
