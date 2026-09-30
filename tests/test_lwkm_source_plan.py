from pathlib import Path

import pytest
import yaml

from tools.lwkm_source_plan import build_plan, discover_controls


def _write_profile(path:Path):
    profile={
        "schema_version":1,
        "profile":"test",
        "classes":{
            "static_input":{"keys":["static_file"]},
            "period_input":{"key_patterns":["prec_YYYY"]},
            "run_output":{
                "base":"find_ancestor",
                "markers":["modflow/results","metaswap/svat_per"],
                "patterns":[
                    {"id":"head_l1","glob":"modflow/results/head/head_*_l1.idf","producer":"TEST","required":True},
                ],
            },
            "restart":{"include_payload":False,"preserve_lineage":True},
        },
        "policy":{"missing_required_source":"fail"},
    }
    path.write_text(yaml.safe_dump(profile,sort_keys=False),encoding="utf-8")


def _write_period(root:Path,year:int,shared:Path,*,with_output=True):
    run=root/f"run_{year}"
    run.mkdir(parents=True)
    (run/"modflow/results/head").mkdir(parents=True)
    (run/"metaswap/svat_per").mkdir(parents=True)
    meteo=run/"meteo"
    meteo.mkdir()
    (meteo/f"prec_{year}_a.asc").write_text("a")
    (meteo/f"prec_{year}_b.asc").write_text("b")
    if with_output:
        (run/"modflow/results/head"/f"head_{year}0101_l1.idf").write_text("head")
    control=run/f"control_run_{year}_{year}.ini"
    control.write_text(
        f"%shared% = {shared.parent}\n"
        f"static_file = %(%shared%)s/{shared.name}\n"
        f"%prec% = {meteo}\n"
        f"prec_{year} = %(%prec%)s/prec_{year}_*.asc\n",
        encoding="utf-8",
    )
    return control


def test_build_plan_resolves_controls_wildcards_and_outputs(tmp_path):
    shared=tmp_path/"static.dat"
    shared.write_text("same")
    _write_period(tmp_path,1970,shared)
    _write_period(tmp_path,1971,shared)
    profile=tmp_path/"profile.yml"
    _write_profile(profile)

    plan=build_plan(tmp_path,profile)

    assert [c["period"] for c in plan["controls"]]==["1970-1970","1971-1971"]
    assert plan["run_chain"]["restart_payload_included"] is False

    static=[x for x in plan["sources"] if x["class"]=="static_input"]
    period=[x for x in plan["sources"] if x["class"]=="period_input"]
    output=[x for x in plan["sources"] if x["class"]=="run_output"]
    assert len(static)==2
    assert len(period)==4
    assert len(output)==2
    assert {Path(x["path"]).name for x in period}=={
        "prec_1970_a.asc","prec_1970_b.asc","prec_1971_a.asc","prec_1971_b.asc"
    }
    assert all(x["producer"]=="TEST" for x in output)


def test_control_period_gaps_fail(tmp_path):
    shared=tmp_path/"static.dat";shared.write_text("x")
    _write_period(tmp_path,1970,shared)
    _write_period(tmp_path,1972,shared)
    with pytest.raises(ValueError,match="Gap in control periods"):
        discover_controls(tmp_path)


def test_required_run_output_missing_fails(tmp_path):
    shared=tmp_path/"static.dat";shared.write_text("x")
    _write_period(tmp_path,1970,shared,with_output=False)
    profile=tmp_path/"profile.yml";_write_profile(profile)
    with pytest.raises(FileNotFoundError,match="required run output head_l1"):
        build_plan(tmp_path,profile)


def test_missing_period_input_fails(tmp_path):
    shared=tmp_path/"static.dat";shared.write_text("x")
    control=_write_period(tmp_path,1970,shared)
    text=control.read_text()
    control.write_text("\n".join(line for line in text.splitlines() if not line.startswith("prec_1970")))
    profile=tmp_path/"profile.yml";_write_profile(profile)
    with pytest.raises(ValueError,match="missing period input prec_1970"):
        build_plan(tmp_path,profile)
