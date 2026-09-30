import json

from tools.lwkm_source_cli import main


def test_collect_verify_unpack(tmp_path):
    control = tmp_path / "c.ini"
    control.write_text("x=a")
    source = tmp_path / "s.dat"
    source.write_text("payload")
    plan = {
        "schema": "lwkm-source-plan-v1",
        "controls": [{"path": "c.ini", "period": "p1"}],
        "sources": [
            {
                "logical_name": "s",
                "class": "static_input",
                "path": "s.dat",
                "control_file": "c.ini",
            }
        ],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    bundle = tmp_path / "bundle.zip"

    assert main(["collect", "--plan", str(plan_path), "--output", str(bundle)]) == 0
    assert main(["verify", str(bundle)]) == 0

    target = tmp_path / "snapshot"
    assert main(["unpack", str(bundle), "--target", str(target)]) == 0
    assert (target / "manifest.json").exists()
