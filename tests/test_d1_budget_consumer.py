import json
import os
from pathlib import Path
import subprocess
import pandas as pd
import pytest
from tests.test_daily_budget_processor import reconstructed_plan
from tools.daily_budget_entry import run
from tools.production_transfer import receive

def test_standalone_five_component_daily_export_and_restart(tmp_path):
    plan=reconstructed_plan(tmp_path);cfg=json.loads(plan.read_text());parts=cfg['intervals'][0]['components']
    parts['frf']=parts.pop('lat')
    parts['fff']=[dict(parts['flf'][0])]
    plan.write_text(json.dumps(cfg));dest=tmp_path/'output with spaces'
    if os.environ.get('LWKM_BUDGET_EXE'):
        args=[str(Path(os.environ['LWKM_BUDGET_EXE']).resolve()),'--plan',str(plan),'--output',str(dest)]
        subprocess.run(args,check=True);subprocess.run(args,check=True)
    else:run(plan,dest);run(plan,dest)
    report=json.loads((dest/'daily/manifest.json').read_text())
    assert all(v['reused'] for day in report['days'] for v in day['files'].values())
    f=pd.read_csv(dest/'transfer/2020-07-01.csv')
    assert f.frf_net_m3_d.iloc[0]==0 and f.fff_net_m3_d.iloc[0]==3.
    r=receive(dest/'transfer/transfer.json',dest/'transfer',tmp_path/'received')
    assert r['status']=='IMPORT_VERIFIED_CANDIDATE'

def test_no_four_component_transfer_disguised_as_five(tmp_path):
    plan=reconstructed_plan(tmp_path)
    with pytest.raises(ValueError,match='five separate'):run(plan,tmp_path/'out')
