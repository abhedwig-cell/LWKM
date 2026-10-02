import argparse
import csv
import json
from pathlib import Path
import tempfile

from tools.server import lwkm_w01 as w01


def _write_spec(path, rows):
    fields = [
        "logical_id", "root_key", "provenance_class", "required_by",
        "filename_pattern", "path_hint", "required", "max_matches",
        "temporal_scope", "expected_format", "semantic_role",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_q0_q1_q2_q3_q4(tmp_path):
    run_root = tmp_path / "run"
    project_root = tmp_path / "project"
    run_root.mkdir()
    (project_root / "BasicData" / "grids").mkdir(parents=True)
    (project_root / "runtime").mkdir(parents=True)

    (run_root / "head_19710101_l1.idf").write_bytes(b"head")
    (project_root / "BasicData" / "grids" / "svat.asc").write_text("svat\n")
    (project_root / "runtime" / "control_LHM433_HRU_SWAP_10242.inp").write_text("control\n")

    spec = tmp_path / "spec.csv"
    _write_spec(spec, [
        {
            "logical_id": "HEAD",
            "root_key": "RUN",
            "provenance_class": "A",
            "required_by": "post",
            "filename_pattern": "head_*_l1.idf",
            "path_hint": "",
            "required": "true",
            "max_matches": "",
            "temporal_scope": "run_period",
            "expected_format": "IDF",
            "semantic_role": "head",
        },
        {
            "logical_id": "SVAT",
            "root_key": "PROJECT",
            "provenance_class": "B",
            "required_by": "svat",
            "filename_pattern": "svat.asc",
            "path_hint": "BasicData\\grids",
            "required": "true",
            "max_matches": "1",
            "temporal_scope": "static",
            "expected_format": "ASC",
            "semantic_role": "svat",
        },
        {
            "logical_id": "HRU_SWAP_CONTROL",
            "root_key": "PROJECT",
            "provenance_class": "D",
            "required_by": "runtime",
            "filename_pattern": "control_LHM433_HRU_SWAP_10242.inp",
            "path_hint": "runtime",
            "required": "true",
            "max_matches": "1",
            "temporal_scope": "run_bound",
            "expected_format": "INP",
            "semantic_role": "control",
        },
    ])

    prov = tmp_path / "prov"
    run_id = "TEST"
    q0_args = argparse.Namespace(
        root=[f"RUN={run_root}", f"PROJECT={project_root}"],
        output_root=str(prov),
        run_id=run_id,
        model_version="TEST",
        simulation_start="1971-01-01",
        simulation_end="1971-12-31",
        restart_history="",
        notes="",
        completed_run=True,
        force=False,
    )
    assert w01.q0(q0_args) == 0

    q0_path = prov / run_id / "00_manifest" / "q0-run.json"
    q1_dir = prov / run_id / "00_manifest"
    assert w01.q1(argparse.Namespace(
        q0=str(q0_path), spec=str(spec), output_dir=str(q1_dir)
    )) == 0

    bundle_root = tmp_path / "bundle"
    assert w01.q2(argparse.Namespace(
        q0=str(q0_path),
        q1_summary=str(q1_dir / "q1-summary.json"),
        inventory=str(q1_dir / "q1-inventory.csv"),
        spec=str(spec),
        bundle_root=str(bundle_root),
        force=False,
    )) == 0

    plan = bundle_root / "00_manifest" / "resolved-bundle-plan.json"
    archive = tmp_path / "bundle.zip"
    assert w01.q3(argparse.Namespace(
        plan=str(plan), zip_path=str(archive), force=False
    )) == 0
    assert w01.q4(argparse.Namespace(zip_path=str(archive))) == 0

    q4 = json.loads(Path(str(archive) + ".q4.json").read_text())
    assert q4["status"] == "LHM_SOURCE_Q4_IMMUTABLE_SNAPSHOT"


def test_q1_fails_on_ambiguous_singleton(tmp_path):
    project = tmp_path / "project"
    (project / "a").mkdir(parents=True)
    (project / "b").mkdir(parents=True)
    (project / "a" / "svat.asc").write_text("a")
    (project / "b" / "svat.asc").write_text("b")

    spec = tmp_path / "spec.csv"
    _write_spec(spec, [{
        "logical_id": "SVAT",
        "root_key": "PROJECT",
        "provenance_class": "B",
        "required_by": "svat",
        "filename_pattern": "svat.asc",
        "path_hint": "",
        "required": "true",
        "max_matches": "1",
        "temporal_scope": "static",
        "expected_format": "ASC",
        "semantic_role": "svat",
    }])

    q0 = tmp_path / "q0.json"
    q0.write_text(json.dumps({
        "run_id": "TEST",
        "roots": {"PROJECT": {"path": str(project)}},
    }))

    out = tmp_path / "out"
    assert w01.q1(argparse.Namespace(q0=str(q0), spec=str(spec), output_dir=str(out))) == 2
    summary = json.loads((out / "q1-summary.json").read_text())
    assert summary["ambiguous"] == ["SVAT"]
