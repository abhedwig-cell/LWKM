"""Contract tests for one-command DRA qualification orchestration."""
import json
from pathlib import Path
from tools import run_dra_end_to_end_qualification as workflow


def test_orchestration_passes_actual_handoff_and_reviews(monkeypatch,tmp_path):
    called={}
    def fake_diagnose(*args,**kwargs):
        out=Path(args[3]);out.mkdir(parents=True,exist_ok=True)
        (out/"protected_physical_inputs.json").write_text(
            json.dumps({"schema_version":1,"hrus":[]}),encoding="utf-8")
        (out/"protected_candidate_summary.csv").write_text(
            "hru,status,groups,max_error_m,compression_required\n"
            "1,NO_COMPRESSION,P,0,False\n",encoding="utf-8")
        called["diagnose"]=True
    def fake_run(source,destination):
        called["handoff"]=json.loads(source.read_text())
        return {"failed_hru_count":0,"hru_count":1}
    def fake_review(path):
        called["review_path"]=path.name
        return {"failed_hru_count":0,"hru_count":1}
    monkeypatch.setattr(workflow,"diagnose",fake_diagnose)
    monkeypatch.setattr(workflow,"run",fake_run)
    monkeypatch.setattr(workflow,"review",fake_review)
    result=workflow.execute(
        relation=tmp_path/"relation",h1_mvg_zip=tmp_path/"h1",
        remaining_zip=tmp_path/"remaining",schema=tmp_path/"schema",
        dqsat_grid=tmp_path/"dqsat",output_dir=tmp_path/"out",
        stage_start="2025-01-01",stage_end="2025-12-01",
        expected_h1_sha256="abc",expected_remaining_sha256="def")
    assert result["status"]=="QUALIFICATION_CANDIDATE_PASS"
    assert result["production_admission"] is False
    assert called["diagnose"]
    assert called["handoff"]["schema_version"]==1
    assert called["review_path"]=="protected_candidate_summary.csv"


def test_candidate_failure_blocks_overall_status(monkeypatch,tmp_path):
    def fake_diagnose(*args,**kwargs):
        out=Path(args[3]);out.mkdir(parents=True,exist_ok=True)
        (out/"protected_physical_inputs.json").write_text('{"schema_version":1,"hrus":[]}')
    monkeypatch.setattr(workflow,"diagnose",fake_diagnose)
    monkeypatch.setattr(workflow,"run",lambda *args:{"failed_hru_count":1,"hru_count":1})
    monkeypatch.setattr(workflow,"review",lambda *args:{"failed_hru_count":0,"hru_count":1})
    result=workflow.execute(
        relation=tmp_path/"relation",h1_mvg_zip=tmp_path/"h1",
        remaining_zip=tmp_path/"remaining",schema=tmp_path/"schema",
        dqsat_grid=tmp_path/"dqsat",output_dir=tmp_path/"out",
        stage_start="2025-01-01",stage_end="2025-12-01",
        expected_h1_sha256="abc",expected_remaining_sha256="def")
    assert result["status"]=="QUALIFICATION_CANDIDATE_FAIL"
