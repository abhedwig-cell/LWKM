"""Standalone offline consumer of existing owner-approved daily IDFs."""
import argparse
import json
from pathlib import Path
from tools.server.bind_reconstructed_daily import bind
from tools.process_daily_budget_plan import process
from tools.export_daily_budget_transfer import export

def run(plan,output,*,bindings=False):
    if bindings:
        result=bind(plan,output/'bindings')
        if not result['complete']:raise ValueError('Missing existing daily source products; see binding-report.json')
        plan=output/'bindings/processing-plan.json'
    cfg=json.loads(plan.read_text())
    for r in cfg['intervals']:
        if set(r['components'])!={'flf','frf','fff','ghb','wel'}:
            raise ValueError('D1 transfer requires all five separate source components')
    process(plan,output/'daily')
    return export(output/'daily/manifest.json',cfg['membership'],output/'transfer')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--plan',type=Path);g.add_argument('--bindings',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run(a.plan or a.bindings,a.output,bindings=a.bindings is not None)
