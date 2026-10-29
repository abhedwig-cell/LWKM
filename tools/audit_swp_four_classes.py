"""Compare four-class HRU crop candidates with historical contexts (QA only)."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
from tools.swp_hru_authority import rows, unique, number


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('hru','soil','crop','historical-contexts','output'):
        p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    soils=unique(rows(a.soil),lambda r:number(r,'bodem370'))
    crops=unique(rows(a.crop),lambda r:(number(r,'soil2_id'),number(r,'lu4')))
    hrus=unique(rows(a.hru),lambda r:number(r,'HRU','hru'))
    old={}
    with gzip.open(a.historical_contexts,'rt') as f:
        for line in f:
            c=json.loads(line)['context'];hid=int(c['run_id'])
            if hid in old:raise ValueError('duplicate historical HRU')
            old[hid]=int(c['run']['crop_id'])
    if set(old)!=set(hrus):raise ValueError('historical and candidate populations differ')
    changes=[];counts=Counter()
    for hid,h in sorted(hrus.items()):
        lu=number(h,'lu4');soil=number(h,'bodem370','bodem_repr')
        crop=number(crops[number(soils[soil],'grondsoort2'),lu],'crop_id')
        counts[lu]+=1
        if crop!=old[hid]:changes.append(dict(HRU=hid,old_crop=old[hid],candidate_crop=crop))
    result=dict(hrus=len(hrus),lu4_counts=dict(counts),candidate_crop_changes=len(changes),
                qualification='REAL_IDENTITY_AUDIT_ONLY_NO_GRID_PARAMETER_RUN',examples=changes[:20])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
