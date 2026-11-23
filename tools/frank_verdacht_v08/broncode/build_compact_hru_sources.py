#!/usr/bin/env python3
"""Extract the frozen HRU10242 reference mapping; do not apply donor values."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

REF = 'b06e8d576f1ced10eece35c792165b656b0a8213'
EXPECTED_MEMBERSHIP = '13f4f129957e24ce6f9380dc4e72cc9bdada59620dc4a0a5464bf6e8b319f7f4'
EXPECTED_SCHEMA = '0ca8534216d1ab2944dcfee4c528926c7798fd967dcc58f760c88befd1c83997'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_gzip(path, headers, rows):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding='utf-8', newline='') as text:
                writer = csv.DictWriter(text, fieldnames=headers, lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)


def build(source_dir, dest):
    SOURCE = Path(source_dir)
    DEST = Path(dest)
    DEST.mkdir(parents=True, exist_ok=True)
    membership_path = SOURCE / 'export_svat_HRU_NRU_10242.csv'
    schema_path = SOURCE / 'export_HRUschema_10242.csv'
    assert digest(membership_path) == EXPECTED_MEMBERSHIP
    assert digest(schema_path) == EXPECTED_SCHEMA
    members, xy_counts, hru_counts = {}, Counter(), Counter()
    xy_hrus = defaultdict(set)
    with membership_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header[:8] == ['svat_orig', 'HRU', 'NRU', 'NRUcode', 'svat_donor', 'svat_orig', 'x', 'y']
        for row in reader:
            assert len(row) == len(header)
            assert row[0] == row[5]
            sid, hru = int(row[0]), int(row[1])
            assert sid not in members and sid > 0 and hru > 0
            x, y = float(row[6]), float(row[7])
            assert math.isfinite(x) and math.isfinite(y)
            assert (x - 125) % 250 == 0 and (y - 125) % 250 == 0
            members[sid] = {'svat': sid, 'HRU': hru, 'x': format(x, '.12g'), 'y': format(y, '.12g')}
            xy_counts[x, y] += 1
            xy_hrus[x, y].add(hru)
            hru_counts[hru] += 1
    assert len(members) == 427656 and len(hru_counts) == 10242
    assert len(xy_counts) == len(members) and max(xy_counts.values()) == 1
    src_info_hash = hashlib.sha256()
    info_member = 'csv/SVAT_INFO_HRU.CSV'
    svat_info_rows, selected_rows, selected_islwkm = 0, 0, 0
    info_ids = set()
    with ZipFile(SOURCE / 'csv.zip') as z:
        with z.open(info_member) as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                src_info_hash.update(block)
        with z.open(info_member) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            assert len(reader.fieldnames) == len(set(reader.fieldnames))
            for row in reader:
                sid = int(row['svat'])
                assert sid not in info_ids
                info_ids.add(sid)
                svat_info_rows += 1
                if sid not in members:
                    continue
                m = members[sid]
                assert float(row['xc(m)']) == float(m['x']) and float(row['yc(m)']) == float(m['y'])
                area = float(row['opp(m2)'])
                assert math.isfinite(area) and area > 0
                m['svat_area_m2'] = format(area, '.12g')
                selected_rows += 1
                selected_islwkm += int(row['islwkm(0/1)']) == 1
    assert selected_rows == len(members) and selected_islwkm == len(members)
    with schema_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        schema_headers = reader.fieldnames
        assert len(schema_headers) == len(set(schema_headers))
        schema = sorted(list(reader), key=lambda row: int(row['HRU']))
    assert len(schema) == len(hru_counts)
    assert {int(row['HRU']) for row in schema} == set(hru_counts)
    for row in schema:
        h = int(row['HRU'])
        assert int(row['N']) == hru_counts[h]
        assert int(row['svat_repr']) in members
        assert members[int(row['svat_repr'])]['HRU'] == h
    mapping_name, schema_name = 'SVAT_HRU.csv.gz', 'HRU_SCHEMA.csv.gz'
    write_gzip(DEST / mapping_name, ['svat', 'HRU', 'x', 'y', 'svat_area_m2'], (members[s] for s in sorted(members)))
    write_gzip(DEST / schema_name, schema_headers, schema)
    area_sum = math.fsum(float(row['svat_area_m2']) for row in members.values())
    audit = {
        'membership_rows': len(members), 'unique_svats': len(members),
        'unique_modflow_cell_centres': len(xy_counts), 'unique_hrus': len(hru_counts),
        'maximum_svats_per_modflow_cell': max(xy_counts.values()),
        'modflow_cells_in_multiple_hrus': sum(len(v) > 1 for v in xy_hrus.values()),
        'selected_source_islwkm_one': selected_islwkm,
        'svat_info_source_rows': svat_info_rows,
        'historical_svat_area_sum_m2': area_sum,
        'cluster_full_cell_area_sum_m2': len(members) * 62500,
        'schema_rows': len(schema), 'schema_headers': schema_headers,
        'all_schema_member_counts_match': True,
        'all_representatives_are_members_of_their_hru': True,
    }
    manifest = {
        'profile': 'HRU10242_FROZEN_REFERENCE_20261019',
        'purpose': 'Existing LWKM selection and HRU grouping for Frank export; no reclustering or donor replacement',
        'repository': 'abhedwig-cell/LWKM', 'reference_commit': REF,
        'source_semantics': {
            'selection': 'All SVAT IDs in the frozen HRU10242 membership; original target IDs and coordinates',
            'svat_area_m2': 'Historical original target area from SVAT_INFO_HRU.CSV, checked against original target XY. Actual Frank table area remains authoritative for new calculations.',
            'hru_schema': 'All original columns retained, including historical hydrology. Use for identity, representation and fixed categories only; new continuous Frank summaries come from the Frank table.',
            'unmodified_target_data': True,
            'donor_replacement_applied': False,
            'hru_reclustering_applied': False,
            'reference_hashes_match_work_b_register': True,
        },
        'inputs': {
            'reference_membership': {'filename': membership_path.name, 'sha256': EXPECTED_MEMBERSHIP,
                'library_file_id': 'libfile_fde3_f-6978c794ffe8819184714ef531b87748_c2f9319a255c8191905abbd92f0458b5',
                'file_id': 'file_000000008fdc8246b9464275d7b3479d'},
            'source_archive': {'filename': 'csv.zip', 'sha256': digest(SOURCE / 'csv.zip'),
                'library_file_id': 'libfile_fde3_f-c6070d5087a88191ae1f4e487d21bae6_c2f9319a255c8191905abbd92f0458b5',
                'file_id': 'file_0000000058548210a13df90b0b0d3354'},
            'reference_schema': {'archive_member': 'csv/export_HRUschema_10242.csv', 'sha256': EXPECTED_SCHEMA},
            'historical_area': {'archive_member': info_member, 'sha256': src_info_hash.hexdigest()},
            'work_b_reference_register': {'repository_path': 'config/source/work-b-source-register-20261019.json', 'commit': REF},
        },
        'outputs': {name: {'sha256': digest(DEST / name), 'size_bytes': (DEST / name).stat().st_size} for name in [mapping_name, schema_name]},
        'checks': audit,
    }
    # Expliciete LF maakt ook het JSON-manifest op Windows bytegelijk.
    with (DEST / 'SOURCES.json').open('w', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'destination': str(DEST), 'audit': audit, 'outputs': manifest['outputs']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True,
                        help='Map met de twee referentie-CSV-bestanden en csv.zip')
    parser.add_argument('--dest', type=Path, required=True,
                        help='Afzonderlijke uitvoermap voor de drie compacte referentiebestanden')
    args = parser.parse_args()
    build(args.source_dir, args.dest)
