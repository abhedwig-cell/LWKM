import json
import subprocess
import sys
from pathlib import Path
from tools.server.build_python_bundle import make

def test_minimal_python_server_bundle(tmp_path):
    root=Path(__file__).resolve().parents[1]
    out=tmp_path/"LWKM_Python_Server"
    info=make(root,out)
    assert info["input_data_included"] is False
    assert not (out/"tests").exists()
    assert (out/"run_probe.cmd").is_file()
    for item in info["code"]:
        assert (out/item["path"]).is_file()
    result=subprocess.run([sys.executable,"-m","tools.server.check_deltaforge_compatibility"],cwd=out,capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    payload=json.loads(result.stdout)
    assert payload["changed_environment"] is False
    assert payload["ran_model"] is False
