"""Package the direct-source DRA server producer without source relocation."""
import argparse
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MODULES=('server/produce_dra_from_nhi.py','server/check_swp_source_values.py',
         'server/dqsat_source.py','swp_hru_authority.py','dqsat_policy.py',
         'generate_dra.py','idf_reader.py','p12_swallo.py','dra_level_compression.py',
         'dra_owner_policy.py','dra_protected_compression.py',
         'w07_autofive_full_records.py','run_dra_protected_population.py')


def package(hru,output):
    output.parent.mkdir(parents=True,exist_ok=True)
    prefix='LWKM_WorkE_DRA_Server01/'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in MODULES:archive.write(ROOT/'tools'/name,prefix+'tools/'+name)
        for name in ('tools/__init__.py','tools/server/__init__.py'):archive.writestr(prefix+name,'')
        for name in ('config/dra/server_sources_20261030.json','config/swp/lookup_catalog.json.gz'):
            archive.write(ROOT/name,prefix+name)
        archive.write(hru,prefix+'source_data/hrus.csv')
        archive.write(ROOT/'docs/evidence/2026-10-19-work-b/interfaces/HRU_MEMBERSHIP.csv.gz',prefix+'source_data/membership.csv.gz')
        archive.write(ROOT/'docs/server/DRA_NHI_PRODUCTION_CANDIDATE_20261030.md',prefix+'README.md')
        archive.writestr(prefix+'maak_dra.cmd',
            '@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n'
            'set "LWKM_PYTHON=E:\\tools\\deltaforge\\deltaforge_4\\python.exe"\r\n'
            '"%LWKM_PYTHON%" -c "import sys,json,numpy; print(json.dumps(dict(python=sys.version,executable=sys.executable,numpy=numpy.__version__)))"\r\n'
            'if errorlevel 1 exit /b %errorlevel%\r\n'
            '"%LWKM_PYTHON%" -u -m tools.server.produce_dra_from_nhi %*\r\nexit /b %errorlevel%\r\n')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hru',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(package(args.hru,args.output))
