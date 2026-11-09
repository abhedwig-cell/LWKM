"""Regression gate for the immutable Frank original-SVAT reference.

Not a hydrological qualification. Verifies the manifest contract and optionally
rehashes actual output/source bytes on the NHI server. Standard library only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

REFERENCE_SHA = '7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df'
SOURCES = ('metaswap', 'signed', 'gxg', 'mf', 'et', 'static', 'gebied', 'qmodf')

def checksum(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def verify(manifest, hash_files=False):
    errors = []
    if manifest.get('expected_svats') != 645582 or manifest.get('count') != 645582:
        errors.append('SVAT population differs from 645582')
    if manifest.get('period') != '1991-2020':
        errors.append('Period differs from 1991-2020')
    if manifest.get('missing_gebied') != 88581:
        errors.append('Accepted missing ECHO-gebied count changed')
    if manifest.get('outputs', {}).get('table_sha256', '').lower() != REFERENCE_SHA:
        errors.append('Not the frozen original-SVAT reference table hash')
    if set(manifest.get('sources', {})) != set(SOURCES):
        errors.append('Unexpected source list (must be 8 named sources)')
    if manifest.get('formulas', {}).get('GG') != '(GHG+GLG)/2':
        errors.append('GG formula contract changed')
    if 'NO QMODF' not in manifest.get('formulas', {}).get('OVERALL', ''):
        errors.append('Overall must not include QModF as independent external flux')
    if 'NO MODFLOW STO/BND' not in manifest.get('formulas', {}).get('OVERALL', ''):
        errors.append('Overall must exclude unavailable MODFLOW STO/BND')
    if hash_files:
        paths = [('table', manifest.get('outputs', {}).get('table'),
                  manifest.get('outputs', {}).get('table_sha256'))]
        paths += [(key, rec.get('path'), rec.get('sha256'))
                  for key, rec in manifest.get('sources', {}).items()]
        for name, path, expected in paths:
            try:
                if not path or checksum(path).lower() != str(expected).lower():
                    errors.append('SHA mismatch: ' + name)
            except OSError as exc:
                errors.append('Cannot rehash ' + name + ': ' + str(exc))
    return errors

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--hash-files', action='store_true',
                   help='Expensive: read entire 30-year source CSVs and endtable')
    a = p.parse_args(argv)
    report = json.loads(a.manifest.read_text(encoding='utf-8-sig'))
    errors = verify(report, hash_files=a.hash_files)
    if errors:
        for error in errors:
            print('FAIL:', error, file=sys.stderr)
        return 2
    print('PASS: manifest contract and baseline fingerprint',
          '(actual source bytes rehashed)' if a.hash_files else '(manifest only)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
