"""Read actual SWP/DRA files and verify their hydraulic horizon interface."""
import argparse
import json
from pathlib import Path
from tools.swp_full_oracle import parse_full_swp
from tools.dra_semantic_oracle import parse_dra

ROOT=Path(__file__).resolve().parents[1]


def check_pair(swp,dra):
    parsed=parse_full_swp(swp.read_text());hydraulic=parsed['tables']['TABLE_SOILHYDRFUNC']
    profile=parsed['tables']['TABLE_SOILPROFILE']
    if not hydraulic or not profile:raise ValueError('missing SWP soil tables')
    layers={int(row[1]) for row in profile}
    if layers!=set(range(1,len(hydraulic)+1)):raise ValueError('SWP profile/hydraulic horizons disagree')
    values=parse_dra(dra.read_text())['global'].get('COFANI')
    coefficients=str(values).split() if values is not None else []
    if len(coefficients)!=len(hydraulic):raise ValueError(f'COFANI count {len(coefficients)} != SWP hydraulic horizons {len(hydraulic)}')
    return len(hydraulic)


def check(swp,dra,report):
    swps={p.stem:p for p in swp.glob('*.swp')};dras={p.stem:p for p in dra.glob('*.dra')}
    errors=[]
    for hid in sorted(set(swps)^set(dras)):
        errors.append(dict(HRU=hid,error='SWP or DRA missing'))
    for hid in sorted(set(swps)&set(dras)):
        try:check_pair(swps[hid],dras[hid])
        except ValueError as exc:errors.append(dict(HRU=hid,error=str(exc)))
    result=dict(status='SWP_DRA_HORIZON_MATCH' if swps and not errors else 'SWP_DRA_INTERFACE_FAILED',
                swp_files=len(swps),dra_files=len(dras),failed=len(errors),errors=errors,
                scope='ACTUAL_SERIALIZED_HORIZONS_AND_COFANI_ONLY_NOT_HYDROLOGICAL_VALIDATION')
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
    return result


def discover_dra():
    found=set()
    for parent in (ROOT.parent,ROOT.parent.parent):
        for package in parent.glob('LWKM_WorkE_DRA_Server*'):
            for candidate in (package/'dra_server_productie',package/package.name/'dra_server_productie'):
                manifest=candidate/'production_manifest.json'
                if manifest.is_file() and (candidate/'dra').is_dir():
                    data=json.loads(manifest.read_text())
                    source=candidate/'source_manifest.json'
                    policy=json.loads(source.read_text()).get('identity',{}).get('area_policy') if source.is_file() else None
                    if data.get('status')=='DRA_SOURCE_CANDIDATES_NOT_SWAP_VALIDATED' and data.get('failed')==0 and policy=='ALL_MEMBER_MODFLOW_CELL_62500_M2_NOT_AREA_SVAT':
                        found.add(candidate/'dra')

    if len(found)!=1:raise ValueError(f'expected one completed DRA output with existing full-cell support, found {len(found)}; use --dra for an explicit directory')
    return found.pop()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swp',type=Path,default=ROOT/'swp_server_productie/swp')
    parser.add_argument('--dra',type=Path)
    parser.add_argument('--report',type=Path,default=ROOT/'swp_server_productie/swp_dra_check.json')
    args=parser.parse_args()
    try:
        result=check(args.swp,args.dra or discover_dra(),args.report)
        print(json.dumps({key:value for key,value in result.items() if key!='errors'}))
        raise SystemExit(bool(result['errors']) or not result['swp_files'])
    except ValueError as error:
        print('SWP/DRA STOP: '+str(error));raise SystemExit(1)
