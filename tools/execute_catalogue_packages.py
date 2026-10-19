"""Execute complete immutable catalogue candidates with byte-verified incremental reuse."""
import argparse,hashlib,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tools.assemble_swap_package import sha256
from tools.execute_swap_candidate import execute
from tools.run_dra_protected_population import atomic_json,canonical


def run(build,output,executable,library):
    summary=json.loads(build.read_text());rows=[]
    def one(r):
        package=Path(r['package']);period=json.loads((package/'preflight.json').read_text())
        identity=dict(package=r['fingerprint'],engine=sha256(executable),libimf=sha256(library/'libimf.so'),
            runner=sha256(Path(__file__).with_name('execute_swap_candidate.py')))
        key=hashlib.sha256(canonical(identity).encode()).hexdigest();dest=output/key
        reused=dest.exists()
        if reused:
            execution=json.loads((dest/'execution.json').read_text())
            for n,h in execution['input_sha256'].items():
                if sha256(package/n)!=h:raise ValueError('cached execution input changed')
            for n,h in execution['output_sha256'].items():
                if sha256(dest/n)!=h:raise ValueError('cached execution output changed')
        else:
            execution=execute(executable,package,dest,library_path=library,expected_start=period['start'],expected_end=period['end'])
        return dict(run_id=r['run_id'],execution=execution,execution_directory=str(dest.resolve()),
            execution_reused=reused,package=str(package.resolve()),fingerprint=r['fingerprint'])
    ready=[r for r in summary['runs'] if r['status']=='COMPLETE_CANDIDATE_PACKAGE']
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,ready))
    report=dict(run_count=len(rows),execution_pass=sum(r['execution']['status']=='EXECUTION_PASS' for r in rows),
        executions_reused=sum(r['execution_reused'] for r in rows),production_admitted=False,runs=rows)
    output.mkdir(exist_ok=True,parents=True);atomic_json(output/'summary.json',report);print(json.dumps({k:v for k,v in report.items() if k!='runs'}));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['build','output','executable','library']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.build,a.output,a.executable,a.library)
