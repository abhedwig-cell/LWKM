"""Verify a compact MetaSWAP transfer without copying national raster files."""
import argparse
import json
from pathlib import Path
import pandas as pd
from tools.assemble_swap_package import sha256
from tools.production_transfer import relative
from tools.run_dra_protected_population import atomic_json

def verify(directory):
    done=dict(line.split('=',1) for line in (directory/'COMPLETE.txt').read_text().splitlines())
    manifest=directory/'SHA256SUMS.txt'
    if done.get('sha256_manifest')!=sha256(manifest):raise ValueError('compact completion hash mismatch')
    entries={}
    for line in manifest.read_text().splitlines():
        digest,name=line.split('  ',1)
        if name in entries:raise ValueError('duplicate compact asset')
        if sha256(relative(directory,name))!=digest:raise ValueError('compact SHA256 mismatch: '+name)
        entries[name]=digest
    expected={'annual_hru.csv','seasonal_population.csv','decadal_population.csv','source_hashes.csv','decadal_qa.csv','acceptance.txt','producer_identity.txt'}
    if set(entries)!=expected:raise ValueError('incomplete compact contract')
    status=dict(line.split('=',1) for line in (directory/'acceptance.txt').read_text().splitlines())
    if status.get('production_admitted')!='false' or status.get('status')!='STRUCTURALLY_VERIFIED_CANDIDATE':raise ValueError('unsupported compact status')
    qa=pd.read_csv(directory/'decadal_qa.csv')
    if len(qa)!=int(status['decades']):raise ValueError('compact decade count mismatch')
    if not (qa.complete_hrus+qa.incomplete_hrus).eq(int(status['hru_count'])).all():raise ValueError('compact HRU counts')
    return dict(status='COMPACT_TRANSFER_VERIFIED',production_admitted=False,decades=len(qa),
                source_rehash_verified=status['source_rehash_verified']=='1',
                incomplete_hru_decades=int(qa.incomplete_hrus.sum()),max_abs_residual_mm=float(qa.max_abs_residual_mm.max()),
                hashes=entries,scientific_status='PENDING_REAL_DATA_INTERPRETATION')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',required=True,type=Path);p.add_argument('--report',required=True,type=Path)
    a=p.parse_args();r=verify(a.directory);atomic_json(a.report,r);print(json.dumps(r,indent=2))
