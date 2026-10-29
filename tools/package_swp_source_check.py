"""Package direct physical inspection of already confirmed server sources."""
import argparse
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True);prefix='LWKM_WorkE_SWP_Broncontrole/'
    with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ('tools/server/check_swp_source_values.py','tools/idf_reader.py','config/swp/server_locations_20261029.json'):
            z.write(ROOT/name,prefix+name)
        for name in ('tools/__init__.py','tools/server/__init__.py'):z.writestr(prefix+name,'')
        z.write(ROOT/'docs/evidence/2026-10-19-work-b/interfaces/HRU_MEMBERSHIP.csv.gz',prefix+'source_data/membership.csv.gz')
        z.write(ROOT/'docs/server/SWP_CONFIRMED_SOURCES_20261029.md',prefix+'README.md')
        z.writestr(prefix+'controleer_swp_bronnen.cmd','@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n"E:\\tools\\deltaforge\\deltaforge_4\\python.exe" -m tools.server.check_swp_source_values %*\r\nexit /b %errorlevel%\r\n')
    print(a.output)


if __name__=='__main__':main()
