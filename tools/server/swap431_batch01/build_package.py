#!/usr/bin/env python3
"""Deterministic ZIP plus SHA256 manifest. No network or model execution."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
NAME='LWKM_SWAP431_Batch_v01'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def selected():
 return sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
  and p.name!='PACKAGE_MANIFEST.json' and p.suffix not in ('.pyc','.tmp')
  and not any(part.startswith('.') for part in p.relative_to(ROOT).parts))
def manifest():
 files={p.relative_to(ROOT).as_posix():digest(p) for p in selected()}
 (ROOT/'PACKAGE_MANIFEST.json').write_text(json.dumps({'schema_version':1,'package':NAME,'files':files},sort_keys=True,indent=2)+'\n',encoding='utf-8')
 return files

def build(out):
 out=Path(out).resolve()
 if out==ROOT or ROOT in out.parents:raise ValueError('ZIP must be outside package directory')
 manifest();out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(selected()+[ROOT/'PACKAGE_MANIFEST.json']):
   i=zipfile.ZipInfo(NAME+'/'+p.relative_to(ROOT).as_posix(),date_time=(2026,11,17,12,0,0))
   i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,p.read_bytes())
 print(str(out));print('SHA256 '+digest(out));return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--manifest-only',action='store_true');ap.add_argument('--out',type=Path,default=ROOT.parent/(NAME+'.zip'));a=ap.parse_args()
 if a.manifest_only:print('MANIFEST',len(manifest()))
 else:build(a.out)
