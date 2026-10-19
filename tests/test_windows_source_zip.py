from zipfile import ZipFile
import pytest
from tools.diagnose_dra_10242 import _extract_bundle


def test_windows_member_paths_are_portably_extracted(tmp_path):
    p=tmp_path/'source.zip'
    with ZipFile(p,'w') as z:
        z.writestr('10_H1\\COND_HL1_250.IDF',b'original bytes')
    out=_extract_bundle(p,tmp_path/'out')
    assert (out/'10_H1/COND_HL1_250.IDF').read_bytes()==b'original bytes'


def test_windows_traversal_rejected(tmp_path):
    p=tmp_path/'source.zip'
    with ZipFile(p,'w') as z:z.writestr('..\\escape',b'bad')
    with pytest.raises(ValueError,match='unsafe'):
        _extract_bundle(p,tmp_path/'out')
