import json, hashlib
import pandas as pd
import pytest
from tools.hru_population_manifest import build_manifest, bind_source_hashes
from tools.process_daily_budget_plan import verify_hru_release

def test_w08_release_binding_sparse_and_mismatch(tmp_path):
    member=tmp_path/"members.csv"
    member.write_text("hru_id,cell_id\n101,1\n9001,2\n")
    reps=tmp_path/"rep.csv"; reps.write_text("hru_id\n101\n9001\n")
    soil=tmp_path/"soil.json"; soil.write_text("{}")
    sources={"membership":member,"representatives":reps,"soil_context":soil}
    manifest=bind_source_hashes(build_manifest([101,9001],release="v2"),sources)
    p=tmp_path/"population.json";p.write_text(json.dumps(manifest))
    sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
    cfg={"membership":{"path":str(member),"sha256":sha(member)},
         "hru_population_manifest":{"path":str(p),"sha256":sha(p)},
         "release_binding_sha256":manifest["release_binding_sha256"]}
    assert verify_hru_release(cfg,pd.DataFrame({"hru_id":[101,9001]}))==manifest["release_binding_sha256"]
    with pytest.raises(ValueError,match="identity mismatch"):
        verify_hru_release(cfg,pd.DataFrame({"hru_id":[101,9002]}))
    cfg["release_binding_sha256"]="f"*64
    with pytest.raises(ValueError,match="release binding mismatch"):
        verify_hru_release(cfg,pd.DataFrame({"hru_id":[101,9001]}))
    cfg["release_binding_sha256"]=manifest["release_binding_sha256"]
    cfg["membership"]["sha256"]="0"*64
    with pytest.raises(ValueError,match="membership bytes differ"):
        verify_hru_release(cfg,pd.DataFrame({"hru_id":[101,9001]}))
