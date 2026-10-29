"""Resolve SWP identities directly from HRU CSV; never reads Runs or SQLite.

Produces a reviewable identity manifest, not production-qualified SWP files.
RDS_cm and GWLI_cm must be independently sourced before context generation.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path


def rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if len(reader.fieldnames or []) != len(set(reader.fieldnames or [])):
            raise ValueError(f'Duplicate CSV columns: {path}')
        yield from reader


def number(row, *names):
    values = [int(row[n]) for n in names if row.get(n, '') != '']
    if not values or len(set(values)) != 1:
        raise ValueError(f'Missing or conflicting fields {names}: {values}')
    return values[0]


def unique(records, key):
    result = {}
    for row in records:
        k = key(row)
        if k in result:
            raise ValueError(f'Duplicate identity: {k}')
        result[k] = row
    return result


def resolve(hrus, svats, soils, crops):
    svats = unique(svats, lambda r: number(r, 'svat'))
    soils = unique(soils, lambda r: number(r, 'bodem370'))
    crops = unique(crops, lambda r: (number(r, 'soil2_id'), number(r, 'luse_id')))
    hrus = unique(hrus, lambda r: number(r, 'HRU', 'hru'))
    for hru, row in sorted(hrus.items()):
        representative = number(row, 'svat_repr', 'hru_representative_svat')
        soil = number(row, 'bodem370', 'bodem_repr')
        # A CSV landuse field wins; its absence requires precisely the chosen SVAT.
        if row.get('landgebruik22', '') != '':
            landuse = number(row, 'landgebruik22')
            origin = 'HRU_CSV'
        else:
            landuse = number(svats[representative], 'landgebruik22')
            origin = 'REPRESENTATIVE_SVAT'
        if not 1 <= landuse <= 22:
            raise ValueError(f'HRU {hru}: invalid landgebruik22 {landuse}')
        soil2 = number(soils[soil], 'grondsoort2')
        crop = number(crops[(soil2, landuse)], 'crop_id')
        yield dict(HRU=hru, svat_repr=representative, bodem370=soil,
                   soil2_id=soil2, landgebruik22=landuse, crop_id=crop,
                   SWETR=0 if landuse < 7 else 1,
                   landuse_source=origin,
                   physical_inputs_status='RDS_AND_GWLI_SOURCE_REQUIRED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('hru', 'svat', 'soil', 'crop', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--expected-hrus', type=int, default=10242)
    args = parser.parse_args()
    output = list(resolve(*(rows(getattr(args, n)) for n in ('hru', 'svat', 'soil', 'crop'))))
    if len(output) != args.expected_hrus:
        raise ValueError(f'Expected {args.expected_hrus} HRUs, found {len(output)}')
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / 'hru_swp_identity.csv'
    with target.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader(); writer.writerows(output)
    manifest = {'status': 'IDENTITY_RESOLVED_NOT_SWP_GENERATED', 'hrus': len(output),
                'sources': {n: {'path': str(getattr(args, n)), 'sha256': hashlib.sha256(getattr(args, n).read_bytes()).hexdigest()} for n in ('hru', 'svat', 'soil', 'crop')},
                'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'hrus': len(output)}))


if __name__ == '__main__':
    main()
