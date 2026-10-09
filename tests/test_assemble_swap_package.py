import hashlib
import pytest
from tools.assemble_swap_package import assemble,sha256

def test_immutable_qualified_package(tmp_path):
    swp=tmp_path/"source.swp";swp.write_text("SWAP TEST\n")
    met=tmp_path/"source.met";met.write_text("MET TEST\n")
    assets={
      "swap.swp":{"path":str(swp),"sha256":sha256(swp),"qualification_id":"W10-Q"},
      "1.met":{"path":str(met),"sha256":sha256(met),"qualification_id":"W09-Q"},
    }
    result=assemble(1,assets,tmp_path/"runs",profile_id="modern-v1",code_commit="abc123")
    assert result["status"]=="PACKAGE_CANDIDATE_NOT_ADMITTED"
    assert (tmp_path/"runs"/"run_00001"/"manifest.json").is_file()
    with pytest.raises(FileExistsError):
        assemble(1,assets,tmp_path/"runs",profile_id="modern-v1",code_commit="abc123")

def test_rejects_unqualified_asset(tmp_path):
    swp=tmp_path/"source.swp";swp.write_text("test")
    with pytest.raises(ValueError,match="unqualified"):
        assemble(1,{"swap.swp":{"path":str(swp),"sha256":sha256(swp)}},
                 tmp_path/"runs",profile_id="p",code_commit="c")
    assert not (tmp_path/"runs"/"run_00001").exists()

def test_rejects_wrong_hash_and_traversal(tmp_path):
    swp=tmp_path/"source.swp";swp.write_text("test")
    with pytest.raises(ValueError,match="SHA mismatch"):
        assemble(1,{"swap.swp":{"path":str(swp),"sha256":"0"*64,"qualification_id":"Q"}},
                 tmp_path/"runs",profile_id="p",code_commit="c")
    with pytest.raises(ValueError,match="unsafe"):
        assemble(1,{"swap.swp":{"path":str(swp),"sha256":sha256(swp),"qualification_id":"Q"},
                    "../bad":{"path":str(swp),"sha256":sha256(swp),"qualification_id":"Q"}},
                 tmp_path/"runs",profile_id="p",code_commit="c")

def test_missing_declared_referenced_asset_fails_closed(tmp_path):
    swp=tmp_path/"source.swp";swp.write_text("METFIL=1.met")
    assets={"swap.swp":{"path":str(swp),"sha256":sha256(swp),
                         "qualification_id":"W10-Q"}}
    with pytest.raises(ValueError,match="missing required referenced assets"):
        assemble(1,assets,tmp_path/"runs",profile_id="modern-v1",
                 code_commit="abc123",required_assets=["swap.swp","1.met"])
    assert not (tmp_path/"runs"/"run_00001").exists()
