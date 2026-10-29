"""Record confirmed server locations from the returned inventory, without copying grids."""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import zipfile

KEYS={'glk':'maaiveld_asc','area':'uopp_asc','rds':'rootzone_asc','lgn':'lgn_asc',
      'bfe':'bodem_asc','meteo':'metestat_asc','irr_switch':'beregen_asc',
      'activity':'ib_l1','pipe_cond':'drn_cond_b','pipe_level':'drn_stage_b',
      'dqsat_svat':'dqsat_svat','luse_svat':'luse_svat'}


def confirmed_locations(report):
    sources={};missing={}
    for role,key in KEYS.items():
        refs=[r for r in report['references'] if r['key'].lower()==key]
        # Retain all period/config provenance and reject conflicting physical paths.
        found={str(PureWindowsPath(x['path'])).lower():x['path'] for r in refs for x in r['locations'] if x['status']=='FILE_EXISTS'}
        if len(found)!=1:
            missing[role]=dict(reason='MISSING' if not found else 'MULTIPLE_EXISTING_PATHS',paths=sorted(found.values()))
            continue
        sources[role]=dict(path=next(iter(found.values())),key=key,units='NOT_YET_VERIFIED',
                           evidence=[dict(control=r['control'],line=r['line'],control_sha256=r['control_sha256'],provenance=r['provenance']) for r in refs])
    dynamic=[r for r in report['known_output_locations'] if r['status']=='FILE_EXISTS' and PureWindowsPath(r['path']).name.lower() in ('head_19700101_l1.idf','head_19700101000000_l1.idf')]
    if len(dynamic)==1:sources['head']=dict(path=dynamic[0]['path'],date='1970-01-01',units='m_NAP_FROM_LHM_CONVENTION_NOT_RECHECKED',evidence=dynamic)
    else:missing['head']=dict(reason='NO_UNIQUE_START_DATE_HEAD')
    return dict(status='SERVER_LOCATIONS_CONFIRMED_NOT_PHYSICAL_PARAMETER_QUALIFIED',sources=sources,unresolved=missing,
                current_server_controls=sum(x['provenance']=='CURRENT_SERVER_RUN_CONFIG' for x in report['controls']),
                required_remaining=['Verify raw grid geometry and units before applying conversions.',
                                    'Bind dqsat and bottom-boundary choice without resurrecting local BasicData grids.',
                                    'Verify representative rooting source and management mapping.'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('inventory',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    with zipfile.ZipFile(a.inventory) as z:r=json.loads(z.read('source_inventory.json'))
    result=confirmed_locations(r);result['inventory_sha256']=hashlib.sha256(a.inventory.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(sources=len(result['sources']),unresolved=result['unresolved'])))


if __name__=='__main__':main()
