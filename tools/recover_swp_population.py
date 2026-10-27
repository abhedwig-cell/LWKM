#!/usr/bin/env python3
"""Find and optionally bundle existing LWKM SWP output; never synthesize SWP data."""
import argparse, hashlib, json, re, zipfile
from collections import defaultdict
from pathlib import Path
PATTERN=re.compile(r'^run_(\d{1,5})$',re.I)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('roots',nargs='+',type=Path)
    ap.add_argument('--output',type=Path,default=Path('swp_recovery_report.json'))
    ap.add_argument('--zip',dest='zip_path',type=Path)
    ap.add_argument('--expected',type=int,default=10242)
    a=ap.parse_args()
    candidates=defaultdict(list)
    for root in a.roots:
        if not root.exists():continue
        for p in root.rglob('swap.swp'):
            m=PATTERN.match(p.parent.name)
            if m:
                h=int(m.group(1))
                if 1<=h<=a.expected:candidates[h].append(p)
    selected={};conflicts=[]
    for h,paths in sorted(candidates.items()):
        signatures=defaultdict(list)
        for p in paths:signatures[hashlib.sha256(p.read_bytes()).hexdigest()].append(str(p))
        if len(signatures)>1:conflicts.append({'hru':h,'sha256_paths':dict(signatures)})
        else:selected[h]=(paths[0],next(iter(signatures)))
    missing=sorted(set(range(1,a.expected+1))-set(selected))
    report={'schema_version':1,'expected':a.expected,'found_unique':len(selected),
      'missing_count':len(missing),'missing_ids':missing,'conflicts':conflicts,
      'files':[{'hru':h,'path':str(p),'sha256':d,'size':p.stat().st_size}
        for h,(p,d) in selected.items()],
      'complete':len(selected)==a.expected and not conflicts,'archive_created':False}
    if a.zip_path and report['complete']:
        a.zip_path.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(a.zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for h,(p,_) in selected.items():z.write(p,f'run_{h:05d}/swap.swp')
        report.update(archive_created=True,archive=str(a.zip_path))
        dig=hashlib.sha256()
        with a.zip_path.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):dig.update(chunk)
        report['archive_sha256']=dig.hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+chr(10),encoding='utf-8')
    print(f"SWP found={len(selected)}/{a.expected}, conflicts={len(conflicts)}, missing={len(missing)}")
    return 0 if report['complete'] else 2
if __name__=='__main__':raise SystemExit(main())
