"""Run declared immutable SWAP inputs in a fresh execution directory.

SWAP can return zero after fatal input errors. Normal completion and a parsed
finite output time series are required independently of the process code.
Execution PASS is explicitly not scientific/production admission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import pandas as pd


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def execute(executable, source, destination, *, timeout=300, library_path=None):
    executable, source, destination = map(lambda x: Path(x).resolve(), (executable, source, destination))
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    inputs={}
    for p in sorted(source.iterdir()):
        if p.is_file() and p.suffix.lower() in (".swp", ".bbc", ".dra", ".met", ".crp", ".co2", ".end"):
            shutil.copyfile(p,destination/p.name)
            inputs[p.name]=digest(p)
    if "swap.swp" not in inputs:
        raise ValueError("missing swap.swp")
    env=os.environ.copy()
    if library_path:
        env["LD_LIBRARY_PATH"]=str(Path(library_path).resolve())
    start=time.monotonic()
    try:
        p=subprocess.run([str(executable),"swap"],cwd=destination,env=env,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        stdout=p.stdout.decode("utf-8",errors="replace")
        returncode=p.returncode
    except subprocess.TimeoutExpired as e:
        stdout=(e.stdout or b"").decode("utf-8",errors="replace")
        returncode=None
    (destination/"runtime.log").write_text(stdout)
    complete="Swap normal completion!" in stdout
    output=destination/"result_output.csv"
    rows=0
    output_error=None
    first_date=last_date=None
    if complete and output.exists():
        try:
            frame=pd.read_csv(output,comment="*")
            rows=len(frame)
            if 'DATE' not in frame or frame.DATE.duplicated().any():
                raise ValueError('missing/duplicate output dates')
            dates=pd.to_datetime(frame.DATE,format='%Y-%m-%d',errors='raise')
            if not dates.is_monotonic_increasing or not dates.diff().dropna().eq(pd.Timedelta(days=1)).all():
                raise ValueError('output calendar is not gap-free daily')
            first_date,last_date=str(frame.DATE.iloc[0]),str(frame.DATE.iloc[-1])
            numeric=frame.select_dtypes(include="number")
            import numpy as np
            if not rows or numeric.empty or not np.isfinite(numeric.to_numpy()).all():
                output_error="empty or nonfinite numeric output"
        except Exception as e:
            output_error=str(e)
    else:
        output_error="missing normal completion or output"
    # Distributed 4.3.1 swap_main.f90 explicitly calls Exit(100) on success.
    result={"schema_version":1,"status":"EXECUTION_PASS" if complete and returncode in (0,100) and not output_error else "EXECUTION_FAIL",
            "production_admitted":False,"elapsed_seconds":time.monotonic()-start,
            "returncode":returncode,"normal_completion":complete,"output_rows":rows,
            "first_output_date":first_date,"last_output_date":last_date,
            "output_error":output_error,"executable_sha256":digest(executable),"input_sha256":inputs,
            "output_sha256":{p.name:digest(p) for p in destination.iterdir() if p.is_file() and p.name not in inputs},
            "runtime_library_sha256":{p.name:digest(p) for p in Path(library_path).glob("libimf.so")} if library_path else {}}
    (destination/"execution.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("executable","source","destination"):
        p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--library-path",type=Path)
    p.add_argument("--timeout",type=int,default=300)
    a=p.parse_args()
    r=execute(a.executable,a.source,a.destination,timeout=a.timeout,library_path=a.library_path)
    print(json.dumps(r))
    return 0 if r["status"]=="EXECUTION_PASS" else 1


if __name__=="__main__":raise SystemExit(main())
