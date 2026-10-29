"""Package tested Work E source with hash-bound existing membership for NHI.

Copies Python modules only; reuses existing native programs in their original
packages. Bundled NumPy is not assumed or installed on the NHI machine.
"""
import argparse,gzip,hashlib,json,shutil,zipfile
from pathlib import Path


def build(repo,members,output,activity_mask=None):
    repo,output=Path(repo),Path(output)
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    for p in (repo/'tools').rglob('*.py'):
        target=output/p.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    shutil.copyfile(repo/'tools/server/start_work_e.cmd',output/'start_work_e.cmd')
    dest=output/'source_data/svat_hru_xy.csv.gz';dest.parent.mkdir()
    with open(members,'rb') as src,open(dest,'wb') as dst:
        with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
    if activity_mask:
        shutil.copyfile(activity_mask,output/'source_data/IBOUND_L1.IDF')
    shutil.copyfile(repo/'docs/production/WORK_E_BBC09_20261029.md',output/'README.md')
    rows=[dict(path=p.relative_to(output).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
          for p in sorted(output.rglob('*')) if p.is_file()]
    (output/'bundle-manifest.json').write_text(json.dumps(dict(schema_version=1,
        status='REAL_GEOMETRY_TESTED_NOT_NATIONAL_PRODUCTION_VALIDATED',files=rows),indent=2)+'\n')
    archive=output.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(output.parent))
    return dict(path=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['repo','members','output']:p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--activity-mask',type=Path)
    a=p.parse_args();print(json.dumps(build(a.repo,a.members,a.output,a.activity_mask)))
