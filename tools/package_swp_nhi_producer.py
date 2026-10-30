"""Bundle candidate NHI production with the real returned source-value report."""
import argparse
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('hru','source-report','output'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    modules=['tools/server/produce_swp_from_nhi.py','tools/server/check_swp_source_values.py','tools/swp_run_parameters.py',
             'tools/dqsat_policy.py','tools/server/dqsat_source.py','tools/check_swp_dra_compatibility.py','tools/swp_full_oracle.py','tools/dra_semantic_oracle.py','tools/swp_hru_authority.py','tools/svat_areas.py','tools/swp_direct_render.py','tools/modern_swp.py','tools/swp_renderer.py',
             'tools/swp_template_adapter.py','tools/idf_reader.py']
    prefix='LWKM_WorkE_SWP_Server05/'
    with zipfile.ZipFile(a.source_report) as report,zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
        for module in modules:z.write(ROOT/module,prefix+module)
        for name in ('tools/__init__.py','tools/server/__init__.py'):z.writestr(prefix+name,'')
        for name in ('server_locations_20261029.json','soil_classification_and_profile.csv','four_landuse_crop_candidate.csv','lookup_catalog.json.gz'):
            z.write(ROOT/'config/swp'/name,prefix+'config/swp/'+name)
        z.write(ROOT/'tests/fixtures/d1/wwl.swp',prefix+'tests/fixtures/d1/wwl.swp')
        z.write(ROOT/'docs/evidence/2026-10-19-work-b/interfaces/HRU_MEMBERSHIP.csv.gz',prefix+'source_data/membership.csv.gz')
        z.write(a.hru,prefix+'source_data/hrus.csv')
        z.writestr(prefix+'source_data/source_values.json',report.read('source_values.json'))
        z.write(ROOT/'docs/server/SWP_NHI_PRODUCTION_CANDIDATE_20261029.md',prefix+'README.md')
        z.writestr(prefix+'maak_swp.cmd','@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n"E:\\tools\\deltaforge\\deltaforge_4\\python.exe" -m tools.server.produce_swp_from_nhi %*\r\nexit /b %errorlevel%\r\n')
        z.writestr(prefix+'controleer_swp_dra.cmd','@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n"E:\\tools\\deltaforge\\deltaforge_4\\python.exe" -m tools.check_swp_dra_compatibility %*\r\nexit /b %errorlevel%\r\n')
    print(a.output)


if __name__=='__main__':main()
