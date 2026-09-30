import json
import zipfile

import pytest

from tools.lwkm_source_bundle import build_bundle_from_plan, unpack_bundle, verify_bundle


def test_v2_deduplicates_and_verifies(tmp_path):
    c1 = tmp_path / "control_run_1970_1979.ini"
    c1.write_text("x=a\n")
    c2 = tmp_path / "control_run_1980_1989.ini"
    c2.write_text("x=b\n")
    shared = tmp_path / "uopp.asc"
    shared.write_text("same")
    period = tmp_path / "head.idf"
    period.write_text("head")
    plan = {
        "schema": "lwkm-source-plan-v1",
        "controls": [
            {"path": c1.name, "period": "1970-1979"},
            {"path": c2.name, "period": "1980-1989"},
        ],
        "sources": [
            {
                "logical_name": "uopp",
                "class": "static_input",
                "path": shared.name,
                "control_file": c1.name,
            },
            {
                "logical_name": "uopp",
                "class": "static_input",
                "path": shared.name,
                "control_file": c2.name,
                "period": "1980-1989",
            },
            {
                "logical_name": "head_l1",
                "class": "run_output",
                "path": period.name,
                "control_file": c2.name,
                "period": "1980-1989",
            },
        ],
        "run_chain": {"periods": ["1970-1979", "1980-1989"]},
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))

    bundle = tmp_path / "bundle.zip"
    manifest = build_bundle_from_plan(plan_path, bundle)

    assert len(manifest["objects"]) == 2
    assert len(manifest["sources"]) == 3
    assert verify_bundle(bundle)["schema"] == "lwkm-source-bundle-v2"
    with zipfile.ZipFile(bundle) as z:
        names = z.namelist()
        assert sum(name.startswith("objects/") for name in names) == 2
        assert "provenance/run_chain.json" in names


def test_unknown_control_rejected(tmp_path):
    control = tmp_path / "c.ini"
    control.write_text("x=a")
    source = tmp_path / "s"
    source.write_text("s")
    plan = {
        "schema": "lwkm-source-plan-v1",
        "controls": [{"path": "c.ini"}],
        "sources": [
            {
                "logical_name": "s",
                "class": "static_input",
                "path": "s",
                "control_file": "missing.ini",
            }
        ],
    }
    plan_path = tmp_path / "p.json"
    plan_path.write_text(json.dumps(plan))
    with pytest.raises(ValueError):
        build_bundle_from_plan(plan_path, tmp_path / "z.zip")


def test_unpack_refuses_nonempty_target(tmp_path):
    control = tmp_path / "c.ini"
    control.write_text("x=a")
    plan = {
        "schema": "lwkm-source-plan-v1",
        "controls": [{"path": "c.ini"}],
        "sources": [],
    }
    plan_path = tmp_path / "p.json"
    plan_path.write_text(json.dumps(plan))
    bundle = tmp_path / "z.zip"
    build_bundle_from_plan(plan_path, bundle)

    target = tmp_path / "out"
    target.mkdir()
    (target / "old").write_text("x")
    with pytest.raises(FileExistsError):
        unpack_bundle(bundle, target)

    (target / "old").unlink()
    unpack_bundle(bundle, target)
    assert (target / ".lwkm-source-verified").exists()
