"""Restartable SWAP run-state management."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import json
from pathlib import Path

STATES=("PLANNED","STAGED","RUNNING","SUCCEEDED","FAILED","EXTRACTED","QUALIFIED")
ALLOWED={
 "PLANNED":{"STAGED"},"STAGED":{"RUNNING"},"RUNNING":{"SUCCEEDED","FAILED"},
 "FAILED":{"STAGED"},"SUCCEEDED":{"EXTRACTED"},"EXTRACTED":{"QUALIFIED"},"QUALIFIED":set()
}
def now():return datetime.now(timezone.utc).isoformat()

@dataclass
class CaseState:
    hru:int
    dependency_hash:str
    state:str="PLANNED"
    attempt:int=0
    exit_code:int|None=None
    updated_at:str=""
    message:str=""
    def __post_init__(self):
        if not self.updated_at:self.updated_at=now()
    def transition(self,new:str,*,exit_code=None,message=""):
        if new not in ALLOWED[self.state]:raise ValueError(f"Invalid transition {self.state}->{new}")
        if new=="RUNNING":self.attempt+=1
        self.state=new; self.exit_code=exit_code; self.message=message; self.updated_at=now()

def save(states:list[CaseState],path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps([asdict(x) for x in states],indent=2),encoding="utf-8")

def load(path:Path)->list[CaseState]:
    return [CaseState(**x) for x in json.loads(path.read_text())]

def runnable(states:list[CaseState])->list[int]:
    return [x.hru for x in states if x.state in ("PLANNED","FAILED")]
