"""Bind documented merged daily locations; never rerun reconstruction.

A supplied hash-bound processing contract carries membership, support and source
semantics. This command selects only existing merged products, not native runs.
"""
import argparse,json
from pathlib import Path
from tools.run_dra_protected_population import atomic_json

ROOT=r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow'

def make(contract,output,root=ROOT):
    base=json.loads(contract.read_text())
    if base['start']<'1970-01-01' or base['end']>'2022-12-31':raise ValueError('outside owner-designated 1970-2022 coverage')
    sources={}
    from pathlib import PureWindowsPath
    native=PureWindowsPath(root) if ':\\' in root else Path(root)
    for role in ['flf','frf','fff','ghb','wel']:
        sources[role]=dict(directory=str(native/('bdg'+role)),pattern='bdg'+role+'_{date}*_l1.*',positive_multiplier=1,
            spatial_operation={'frf':'SAVED_CURRENT_MINUS_PREVIOUS_COLUMN','fff':'SAVED_CURRENT_MINUS_PREVIOUS_ROW'}.get(role,'CELL_NET'),
            provenance='RECONSTRUCTED_OPERATIONAL',semantics_evidence='docs/production/WORK_A_FIVE_COMPONENT_AUTHORITY_20261019.md')
    atomic_json(output,dict(processing_contract=base,sources=sources,controls=[dict(path=base[k]['path']) for k in ['signs_evidence','units_evidence','time_evidence','package_coverage_evidence']]))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--root',default=ROOT)
    a=p.parse_args();make(a.contract,a.output,a.root)
