"""Build a self-contained source candidate for the NHI Python environment."""
import argparse
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hru',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    sources=['swp_local_assets','swp_hru_authority','swp_run_parameters','swp_direct_render','swp_direct_pipeline',
             'modern_swp','swp_renderer','swp_template_adapter','idf_reader']
    prefix='LWKM_WorkE_SWP_Direct/'
    with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
        for stem in sources:z.write(ROOT/'tools'/f'{stem}.py',prefix+f'tools/{stem}.py')
        z.writestr(prefix+'tools/__init__.py','')
        for name in ['lookup_catalog.json.gz','soil_classification_and_profile.csv','four_landuse_crop_candidate.csv']:
            z.write(ROOT/'config/swp'/name,prefix+'config/swp/'+name)
        z.write(ROOT/'tests/fixtures/d1/wwl.swp',prefix+'tests/fixtures/d1/wwl.swp')
        z.write(a.hru,prefix+'data/hrus.csv')
        z.write(ROOT/'docs/evidence/2026-10-19-work-b/interfaces/HRU_MEMBERSHIP.csv.gz',prefix+'data/membership.csv.gz')
        z.write(ROOT/'docs/lhm-hru-swap/WORK-E-SWP-DIRECT-SERVER.md',prefix+'README.md')
        z.writestr(prefix+'start_swp_direct.cmd','@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n"E:\\tools\\deltaforge\\deltaforge_4\\python.exe" -m tools.swp_direct_pipeline %*\r\nexit /b %errorlevel%\r\n')
        for asset in sorted((ROOT/'templates').rglob('*')):
            if asset.is_file():z.write(asset,prefix+str(asset.relative_to(ROOT)))
    print(a.output)


if __name__=='__main__':main()
