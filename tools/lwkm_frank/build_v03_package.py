"""Build the complete server ZIP from Git sources plus the pinned v02 data assets."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile
import pipeline_v03 as p

ARCHIVE_SHA = '86dcf02933226e78cc5eefc10d11ae6b9067f26056a507110cda48484c904598'
NAME = 'LWKM_Frank_Pipeline_v03'


def launchers():
    intro = ('@echo off\nsetlocal\n'
             'set "PYTHON=E:\\tools\\deltaforge\\deltaforge_4\\python.exe"\n'
             'if not exist "%PYTHON%" (\n'
             '  echo STOP: Deltaforge Python niet gevonden: %PYTHON%\n  exit /b 2\n)\n')
    config = '--config "%~dp0config\\production\\frank_pipeline_v03.json"'
    driver = '"%PYTHON%" -B "%~dp0tools\\lwkm_frank\\pipeline_v03.py"'
    compare = '"%PYTHON%" -B "%~dp0tools\\lwkm_frank\\compare_v03.py" ' + config + '\n'
    actions = {
        'CONTROLE_FRANK_V03.cmd': driver + ' check ' + config + ' --through msw_basic\n',
        'PLAN_FRANK_V03.cmd': driver + ' plan ' + config + ' --through all\n',
        'COMPARE_MSW_REFERENCE_V03.cmd': compare,
        'START_MSW_BASIS_V03.cmd': ('rem Alleen de eerste producent, in een afzonderlijke proefmap.\n'
                                  + driver + ' diagnostic-run ' + config + ' --through msw_basic\n'
                                  'if errorlevel 1 exit /b %ERRORLEVEL%\n' + compare),
        'TEST_FRANK_V03.cmd': '"%PYTHON%" -B -m unittest discover -s "%~dp0tests" -p "test_lwkm_frank*.py" -v\n',
    }
    return {name: (intro + body + 'set "RC=%ERRORLEVEL%"\nendlocal & exit /b %RC%\n').replace('\n', '\r\n').encode('ascii')
            for name, body in actions.items()}


def build(output, revision, v02_zip=None):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Supply the exact Git commit SHA with --revision')
    p.verify_code()
    paths = [
        'tools/lwkm_frank/pipeline_v03.py', 'tools/lwkm_frank/compare_v03.py',
        'tools/lwkm_frank/run_source_binding.py', 'tools/lwkm_frank/build_v03_package.py',
        'tests/test_lwkm_frank_pipeline_v03.py', 'tests/test_lwkm_frank_compare_v03.py',
        'tests/test_lwkm_frank_run_source_binding.py',
        'config/production/frank_original_producers_sha256_v01.json',
        'config/production/frank_pipeline_v03.json',
        'docs/production/FRANK_PIPELINE_V03_20261110.md',
        'evidence/production/frank_v03_local_qualification.json',
        'tools/lwkm_frank/data/SOURCE_ASSETS.json',
    ]
    paths += ['tools/lwkm_frank/legacy/' + n for n in [*p.PRODUCERS.values(), *p.READERS]]
    payload = {name: (p.REPO / name).read_bytes() for name in paths}
    payload['LEESMIJ.md'] = payload['docs/production/FRANK_PIPELINE_V03_20261110.md']
    payload.update(launchers())
    if v02_zip:
        if p.sha(v02_zip) != ARCHIVE_SHA:
            raise ValueError('The supplied v02 ZIP is not the recovered original archive')
        with zipfile.ZipFile(v02_zip) as z:
            if z.testzip() is not None:
                raise ValueError('Corrupt v02 archive')
            assets = {name: z.read('LWKM_Frank_Pipeline_v02_Bronbeheer/' + name) for name in p.ASSETS}
    else:
        assets = {name: (p.DATA / name).read_bytes() for name in p.ASSETS}
    for name, raw in assets.items():
        if hashlib.sha256(raw).hexdigest() != p.ASSETS[name]:
            raise ValueError('Original data asset differs: ' + name)
        payload['tools/lwkm_frank/data/' + name] = raw
    release = {'release': NAME, 'source_revision': revision,
               'source_archive_sha256': ARCHIVE_SHA,
               'production_enabled': False,
               'scope': 'Isolated diagnostic replay; real NHI comparison pending',
               'files_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(payload.items())}}
    payload['RELEASE.json'] = (json.dumps(release, indent=2) + '\n').encode('utf-8')
    output = Path(output)
    if output.exists():
        raise FileExistsError('Refusing to replace an existing release: ' + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, raw in sorted(payload.items()):
            info = zipfile.ZipInfo(NAME + '/' + name, date_time=(2026, 11, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:
            raise ValueError('Release ZIP integrity failed')
    print('GEREED:', output, 'SHA256:', p.sha(output), 'files:', len(payload))
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--revision', required=True)
    ap.add_argument('--v02-zip', type=Path)
    args = ap.parse_args()
    build(args.out, args.revision, args.v02_zip)


if __name__ == '__main__': main()
