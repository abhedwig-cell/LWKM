"""Replay national allocation from Server04 diagnostics and exact area source.

Does not render SWP or claim SWAP irrigation management is connected.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile
from tools.svat_areas import read_area_svat
from tools.swp_hru_authority import rows
from tools.swp_run_parameters import allocate_irrigation


def audit(report, area, membership, output):
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    with zipfile.ZipFile(report) as z:
        diagnostics=json.loads(z.read('diagnostics.json'))
        area_manifest=json.loads(z.read('area_source_manifest.json'))
    if {r['sha256'] for r in area_manifest['files']}!={digest(area)}:
        raise ValueError('area_svat does not match server source hashes')
    members=list(rows(membership));values=read_area_svat(area,members)
    totals=defaultdict(float)
    for m in members:totals[int(m['HRU'])]+=values[int(m['svat'])]
    if set(totals)!={d['HRU'] for d in diagnostics}:raise ValueError('population mismatch')
    with zipfile.ZipFile(report) as z:
        manifest=json.loads(z.read('production_manifest.json'))
    if manifest['input_hashes']['membership']!=digest(membership):
        raise ValueError('membership does not match server report')
    runs=[dict(run_id=d['HRU'],area=totals[d['HRU']]) for d in diagnostics]
    summary=allocate_irrigation(runs,diagnostics)
    summary['inputs']={str(p):digest(p) for p in (report,area,membership)}
    summary['scope']='Replay of source-area diagnostics; not a new server or SWAP execution'
    output.mkdir(parents=True,exist_ok=True)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'allocation_by_hru.json').write_text(json.dumps(runs,indent=2)+'\n')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('report','area','membership','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.report,a.area,a.membership,a.output),indent=2))
