"""Build an immutable minimal LWKM Python server bundle from the central checkout.

Only source code is shipped. National data, templates, SQLite and credentials stay on NHI.
Run locally: python -m tools.server.build_python_bundle --output PATH
"""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path

MODULES=(
"tools/__init__.py","tools/swp_context.py","tools/modern_swp.py",
"tools/swp_renderer.py","tools/swp_template_adapter.py",
"tools/swp_full_oracle.py","tools/build_modern_population.py",
"tools/hru_population_manifest.py",
"tools/dra_level_compression.py","tools/dra_protected_compression.py",
"tools/run_dra_protected_population.py",
"tools/server/check_deltaforge_compatibility.py",
)
def make(repo,output):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    copied=[]
    for relative in MODULES:
        source=Path(repo)/relative
        if not source.is_file():
            if relative=="tools/__init__.py":continue
            raise FileNotFoundError(source)
        target=output/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        copied.append({"path":relative,"sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    (output/"run_probe.cmd").write_text('@echo off\ncall "E:\\tools\\deltaforge\\deltaforge_4\\Scripts\\activate.bat" E:\\tools\\deltaforge\\deltaforge_4\ncd /d "%~dp0"\npython -m tools.server.check_deltaforge_compatibility\nexit /b %errorlevel%\n')
    manifest={"schema_version":1,"status":"RESEARCH_BUNDLE_NOT_PRODUCTION_ADMITTED",
              "code":copied,"source":"LWKM central Git checkout","input_data_included":False}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--repo",default=".");p.add_argument("--output",required=True)
    a=p.parse_args();print(json.dumps(make(a.repo,a.output),indent=2))
