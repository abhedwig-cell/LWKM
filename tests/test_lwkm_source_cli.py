import json

import yaml

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


def test_plan_and_collect_directly_from_controls(tmp_path):
    run=tmp_path/"run"
    (run/"modflow/results/head").mkdir(parents=True)
    (run/"metaswap/svat_per").mkdir(parents=True)
    static=tmp_path/"static.dat";static.write_text("static")
    meteo=run/"meteo";meteo.mkdir()
    (meteo/"prec_1970_a.asc").write_text("rain")
    (run/"modflow/results/head/head_19701231_l1.idf").write_text("head")

    control=run/"control_run_1970_1970.ini"
    control.write_text(
        f"static_file = {static}\n"
        f"prec_1970 = {meteo}/prec_1970_*.asc\n"
    )
    profile=tmp_path/"profile.yml"
    profile.write_text(yaml.safe_dump({
        "schema_version":1,
        "profile":"cli-test",
        "classes":{
            "static_input":{"keys":["static_file"]},
            "period_input":{"key_patterns":["prec_YYYY"]},
            "run_output":{
                "base":"find_ancestor",
                "markers":["modflow/results","metaswap/svat_per"],
                "patterns":[
                    {"id":"head","glob":"modflow/results/head/head_*_l1.idf","required":True}
                ],
            },
            "restart":{"include_payload":False},
        },
        "policy":{"missing_required_source":"fail"},
    },sort_keys=False))

    resolved=tmp_path/"resolved.json"
    assert main([
        "plan","--controls",str(tmp_path),"--profile",str(profile),"--output",str(resolved)
    ])==0
    data=json.loads(resolved.read_text())
    assert len(data["controls"])==1
    assert len(data["sources"])==3

    bundle=tmp_path/"direct.zip"
    persisted=tmp_path/"persisted-plan.json"
    assert main([
        "collect","--controls",str(tmp_path),"--profile",str(profile),
        "--write-plan",str(persisted),"--output",str(bundle)
    ])==0
    assert persisted.exists()
    assert main(["verify",str(bundle)])==0

    report=tmp_path/"qualification.json"
    assert main([
        "qualify","--controls",str(tmp_path),"--profile",str(profile),
        "--bundle",str(bundle),"--output",str(report)
    ])==0
    q=json.loads(report.read_text())
    assert q["qualified_through"]=="Q4"
    assert q["q4"]["status"]=="PASS"
