from pathlib import Path

import yaml

from tools.lhm_upstream_qualification import qualify


def _profile(path:Path):
    path.write_text(yaml.safe_dump({
        "schema_version":1,
        "profile":"qtest",
        "classes":{
            "static_input":{"keys":["static_file"]},
            "period_input":{"key_patterns":["prec_YYYY"]},
            "run_output":{
                "base":"find_ancestor",
                "markers":["modflow/results","metaswap/svat_per"],
                "patterns":[
                    {"id":"head_l1","glob":"modflow/results/head/head_*_l1.idf","required":True},
                ],
            },
            "restart":{"include_payload":False},
        },
        "policy":{"missing_required_source":"fail"},
    },sort_keys=False))


def _run(root:Path,year:int,*,end_date=True,zero=False):
    run=root/f"run_{year}"
    (run/"modflow/results/head").mkdir(parents=True)
    (run/"metaswap/svat_per").mkdir(parents=True)
    static=root/"static.dat"
    static.write_text("static")
    meteo=run/"meteo";meteo.mkdir()
    (meteo/f"prec_{year}.asc").write_text("rain")
    date_token=f"{year}1231" if end_date else f"{year}0630"
    out=run/"modflow/results/head"/f"head_{date_token}_l1.idf"
    out.write_text("" if zero else "head")
    control=run/f"control_run_{year}_{year}.ini"
    control.write_text(
        f"static_file = {static}\n"
        f"prec_{year} = {meteo}/prec_{year}.asc\n"
    )


def test_q0_to_q3_pass(tmp_path):
    _run(tmp_path,1970)
    _run(tmp_path,1971)
    profile=tmp_path/"profile.yml";_profile(profile)
    result=qualify(tmp_path,profile)
    assert result["qualified_through"]=="Q3"
    assert result["q4_ready_for_bundle_gate"] is True
    assert [g["status"] for g in result["gates"]]==["PASS","PASS","PASS","PASS"]


def test_q3_fails_on_zero_byte_required_output(tmp_path):
    _run(tmp_path,1970,zero=True)
    profile=tmp_path/"profile.yml";_profile(profile)
    result=qualify(tmp_path,profile)
    assert result["qualified_through"]=="Q2"
    assert result["gates"][3]["status"]=="FAIL"
    assert result["gates"][3]["details"]["zero_byte_files"]


def test_q3_fails_if_dated_output_stops_before_period_end(tmp_path):
    _run(tmp_path,1970,end_date=False)
    profile=tmp_path/"profile.yml";_profile(profile)
    result=qualify(tmp_path,profile)
    assert result["qualified_through"]=="Q2"
    assert result["gates"][3]["status"]=="FAIL"


def test_q1_failure_stops_later_gates(tmp_path):
    _run(tmp_path,1970)
    _run(tmp_path,1972)
    profile=tmp_path/"profile.yml";_profile(profile)
    result=qualify(tmp_path,profile)
    assert result["gates"][0]["status"]=="FAIL"
    assert result["gates"][1]["status"]=="NOT_REACHED"
