"""Rebuild complete server ZIP from source checkout and original supplied inputs.
Developer utility; not required to run the Windows processor on the server.
"""
import hashlib,json,shutil,sys,zipfile
from pathlib import Path
src=Path(__file__).resolve().parent
inputs,destination=map(lambda x:Path(x).resolve(),sys.argv[1:])
root=destination/'LWKM_MetaSWAP_HRU_Windows_x64_1.0.0'
root.mkdir(parents=True,exist_ok=True)
(root/'data').mkdir(exist_ok=True);(root/'source').mkdir(exist_ok=True);(root/'evidence').mkdir(exist_ok=True)
for name in ['lwkm_metaswap_hru.exe','run_metaswap_hru.cmd','sources.csv','README_NL.txt']:shutil.copy2(src/name,root/name)
for name in ['lwkm_metaswap_hru.cpp','build_cross.sh','build_windows.cmd','package_release.py']:shutil.copy2(src/name,root/'source'/name)
shutil.copytree(src/'tests',root/'source'/'tests',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for old,new in [('area_svat(2).inp','area_svat.inp'),('export_svat_HRU_NRU_10242(3).csv','svat_hru.csv')]:shutil.copy2(inputs/old,root/'data'/new)
shutil.copy2(inputs/'metaswap_inventory.csv',root/'data'/'metaswap_inventory.csv')
ev=src.parents[1]/'docs'/'evidence'/'2026-10-20-metaswap-windows'
shutil.copytree(ev,root/'evidence',dirs_exist_ok=True)
# Require exactly the tested executable before publishing a package.
r=json.loads((root/'evidence'/'test_results.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert r['binary_sha256']==sha(root/'lwkm_metaswap_hru.exe')
assert r['windows_execution']=='native Windows x64' and all(x['status']=='PASS' for x in r['tests'])
lines=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS.txt':lines.append(sha(p)+'  '+p.relative_to(root).as_posix())
(root/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
archive=destination/(root.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(root.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for line in lines:
  digest,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
print(json.dumps({'zip':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'binary_sha256':r['binary_sha256'],'verified_files':len(lines)},indent=2))
