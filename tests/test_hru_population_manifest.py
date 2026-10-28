import pytest
from tools.hru_population_manifest import build_manifest, validate_membership

def test_sparse_hru_population():
    a=build_manifest([9001,101,205],release="next")
    assert a["n_hrus"]==3
    assert a["hru_ids"]==[101,205,9001]
    assert validate_membership(a,[205,9001,101])
    with pytest.raises(ValueError,match="identity mismatch"):
        validate_membership(a,[101,205,9002])

def test_duplicate_and_corruption():
    with pytest.raises(ValueError):
        build_manifest([101,101],release="x")
    a=build_manifest([10,20],release="x")
    a["hru_ids"][0]=11
    with pytest.raises(ValueError,match="digest mismatch"):
        validate_membership(a,[11,20])

def test_release_binding_detects_same_ids_changed_membership(tmp_path):
    from tools.hru_population_manifest import bind_source_hashes, verify_source_binding
    paths={}
    for name in ("membership","representatives","soil_context"):
        p=tmp_path/(name+".csv")
        p.write_text(name+" original")
        paths[name]=p
    manifest=bind_source_hashes(build_manifest([101,205,9001],release="v1"),paths)
    assert verify_source_binding(manifest,paths)
    paths["membership"].write_text("membership altered")
    with pytest.raises(ValueError,match="source identity mismatch"):
        verify_source_binding(manifest,paths)

def test_manifest_binding_requires_exact_member_asset(tmp_path):
    from tools.hru_population_manifest import bind_source_hashes
    files={}
    for role in ("membership","representatives","soil_context"):
        p=tmp_path/(role+".csv");p.write_text(role);files[role]=p
    m=bind_source_hashes(build_manifest([101,9001],release="v2"),files)
    assert m["source_sha256"]["membership"]
    assert len(m["release_binding_sha256"])==64
