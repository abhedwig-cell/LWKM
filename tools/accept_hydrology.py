"""Acceptance manifest gate for downstream handoff."""
from __future__ import annotations
import json
from pathlib import Path

def build_acceptance(*,svat_version,qualification_version,hru_version,mapping_version,
                     swap_version,run_manifest_hash,extraction_version,qa_passed,qa_summary):
    if not qa_passed: raise ValueError("Cannot accept unqualified hydrology")
    return {"schema_version":1,"status":"ACCEPTED","svat_version":svat_version,
            "qualification_version":qualification_version,"hru_version":hru_version,
            "mapping_version":mapping_version,"swap_version":swap_version,
            "run_manifest_hash":run_manifest_hash,"extraction_version":extraction_version,
            "qa_passed":True,"qa_summary":qa_summary}

def write_acceptance(manifest,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding="utf-8")
