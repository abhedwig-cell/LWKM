"""Persist compact complete interfaces and qualification evidence for Work B."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
from tools.hru_source_chain import sha,atomic_json


def bundle(work,qualification,interfaces,component,incremental,output):
    work,qualification,interfaces,component,incremental,output=map(Path,[work,qualification,interfaces,component,incremental,output])
    output.mkdir(parents=True,exist_ok=True)
    for p in interfaces.rglob('*'):
        if p.is_file():
            dest=output/'interfaces'/p.relative_to(interfaces);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    for directory,prefix,names in [
        (work/'W03','w03',['summary.json','stage.json','legacy-filter-differences.csv','replacement-regression.csv']),
        (work/'W04-W05','r-replay',['stage.json','R-session.txt','execution.log','CLUSTER_ROUNDS.csv','COMPLETE']),
        (qualification,'comparison',['comparison.json','hru-comparison.csv','hru-attribute-differences.csv','svat-comparison.csv.gz','incremental-controlled-change.json','incremental-unchanged.json']),
        (qualification/'W06','w06',['workbook-ingestion.json','context-summary.json','context-failures.json']),
        (component,'component',['summary.json','dependency-invalidation.json']),
        (incremental,'context-cache',['summary.json','initial.json.gz','unchanged.json.gz','changed.json.gz'])]:
        for name in names:shutil.copyfile(directory/name,output/(prefix+'-'+name))
    for name in ['DONOR_ROUND1','DONOR_ROUND2','DONOR_EXTRA','SUSPECTED_RESTORED','NRU_SCHEMA']:
        with gzip.GzipFile(filename='',fileobj=(output/(name+'.csv.gz')).open('wb'),mode='wb',mtime=0) as dst:
            dst.write((work/'W04-W05'/(name+'.csv')).read_bytes())
    for name in ['unchanged','changed']:
        for source,filename in [('execution.log','execution.log'),('id-reconciliation.json','id-reconciliation.json'),('comparison/comparison.json','comparison.json')]:
            shutil.copyfile(component/name/source,output/('component-'+name+'-'+filename))
    atomic_json(output/'code-file-hashes.json',{str(p):sha(p) for p in sorted(Path('tools').glob('*')) if p.is_file() and ('hru' in p.name or p.name=='build_svat_from_rasters.py')})
    atomic_json(output/'artifact-sha256.json',{str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='artifact-sha256.json'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['work','qualification','interfaces','component','incremental','output']:p.add_argument('--'+n,type=Path,required=True)
    bundle(**vars(p.parse_args()))
