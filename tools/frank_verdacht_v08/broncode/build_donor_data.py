#!/usr/bin/env python3
"""Bouw vastgelegde verdachte-SVAT/donor-data uit de gehashte HRU10242-bronnen.

Dit script voert geen donorselectie uit en past geen Frank-gegevens aan.
De operationele donor komt uit de bestaande membership. Verdachtheid komt
afzonderlijk uit de OR van de acht oorspronkelijke kwalificatievelden.
"""

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile


REFERENCE_COMMIT = 'e9ef2495f2cf11028a457f7e13e4b6bc17ea20f6'
EXPECTED_MEMBERSHIP = '13f4f129957e24ce6f9380dc4e72cc9bdada59620dc4a0a5464bf6e8b319f7f4'
EXPECTED_ARCHIVE = '84ae4963145176767a00c67b968ace5b817002d5292fd9cab8d3933476e509e3'
EXPECTED_INFO = '5aa4a4db2bef7e3c7f72f0925cd2a268170e0428d7225ef674f41af35fd5ce60'
INFO_MEMBER = 'csv/SVAT_INFO_HRU.CSV'
DATA_NAME = 'SVAT_DONOR_QUALIFICATION.csv.gz'
SOURCE_NAME = 'DONOR_SOURCES.json'
HEADERS = ['svat', 'HRU', 'hru_cluster_donor_svat', 'is_suspect',
           'qualification_reason_ids', 'label']
FLAGS = ('ghg_sel', 'gt1_sel', 'gt2_sel', 'gt8_sel', 'kwel_sel',
         'wegzijging_sel', 'runoff_sel', 'subinfil_sel')


def digest_stream(handle):
    result = hashlib.sha256()
    for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
        result.update(block)
    return result.hexdigest()


def digest(path):
    with Path(path).open('rb') as handle:
        return digest_stream(handle)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(membership_path, archive_path, output):
    membership_path, archive_path, output = map(Path, (membership_path, archive_path, output))
    require(digest(membership_path) == EXPECTED_MEMBERSHIP, 'Verkeerde hash van oorspronkelijke membership')
    require(digest(archive_path) == EXPECTED_ARCHIVE, 'Verkeerde hash van csv.zip')
    members = {}
    labels = Counter()
    with membership_path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle, delimiter=',')
        header = next(reader)
        require(header[:8] == ['svat_orig', 'HRU', 'NRU', 'NRUcode', 'svat_donor', 'svat_orig', 'x', 'y'],
                'Onverwachte kolommen in oorspronkelijke membership')
        label_index = header.index('label')
        for row in reader:
            require(len(row) == len(header), 'Onjuist aantal membershipvelden')
            require(row[0] == row[5], 'De twee oorspronkelijke SVAT-kolommen verschillen')
            sid, hru, donor = int(row[0]), int(row[1]), int(row[4])
            require(sid > 0 and hru > 0 and donor > 0 and sid not in members, 'Ongeldige of dubbele membership-ID')
            labels[row[label_index]] += 1
            members[sid] = {'svat': sid, 'HRU': hru, 'hru_cluster_donor_svat': donor,
                            'label': row[label_index]}

    seen = set()
    flag_counts = Counter()
    reason_combinations = Counter()
    raw_code_counts = Counter()
    flag_union_mismatches = 0
    with ZipFile(archive_path) as archive:
        with archive.open(INFO_MEMBER) as handle:
            require(digest_stream(handle) == EXPECTED_INFO, 'Verkeerde hash van ' + INFO_MEMBER)
        with archive.open(INFO_MEMBER) as raw:
            with io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as text:
                reader = csv.DictReader(text, delimiter=',')
                header = reader.fieldnames or []
                require(len(header) == len(set(header)), 'Dubbele kolomnaam in SVAT_INFO_HRU')
                require(set(('svat', 'isverdacht(1010000)') + FLAGS) <= set(header), 'Kwalificatievelden ontbreken')
                for row in reader:
                    require(None not in row and all(value is not None for value in row.values()),
                            'Onjuist aantal SVAT_INFO_HRU-velden')
                    sid = int(row['svat'])
                    require(sid in members and sid not in seen, 'SVAT_INFO_HRU en membership verschillen of bevatten dubbele IDs')
                    seen.add(sid)
                    values = {field: int(row[field].strip()) for field in FLAGS}
                    require(all(value in (0, 1) for value in values.values()), 'Onverwachte kwalificatieflagwaarde')
                    reasons = [field for field in FLAGS if values[field] > 0]
                    flag_counts.update(reasons)
                    reason_string = '|'.join(reasons)
                    reason_combinations[reason_string] += 1
                    code = int(row['isverdacht(1010000)'].strip())
                    raw_code_counts[str(code)] += 1
                    flag_union_mismatches += bool(reasons) != (code != 0)
                    members[sid].update({'is_suspect': int(bool(reasons)),
                                         'qualification_reason_ids': reason_string})
    require(seen == set(members), 'Niet alle membership-SVATs hebben oorspronkelijke kwalificatievelden')
    require(flag_union_mismatches == 0, 'OR van acht flags verschilt van oorspronkelijke isverdacht-code')

    for sid, record in members.items():
        donor = record['hru_cluster_donor_svat']
        require(donor in members, 'Operationele donor ontbreekt voor SVAT ' + str(sid))
        source = members[donor]
        require(source['HRU'] == record['HRU'], 'Donor zit in een andere HRU bij SVAT ' + str(sid))
        require(source['hru_cluster_donor_svat'] == donor, 'Donor is niet zelfdonor bij SVAT ' + str(sid))
        require(not source['is_suspect'], 'Donor is zelf verdacht bij SVAT ' + str(sid))

    suspect = sum(row['is_suspect'] for row in members.values())
    nonself = sum(sid != row['hru_cluster_donor_svat'] for sid, row in members.items())
    suspect_nonself = sum(bool(row['is_suspect']) and sid != row['hru_cluster_donor_svat']
                          for sid, row in members.items())
    checks = {
        'membership_rows': len(members),
        'unique_hrus': len({row['HRU'] for row in members.values()}),
        'suspect_svats': suspect,
        'nonsuspect_svats': len(members) - suspect,
        'nonself_donors': nonself,
        'suspect_nonself_svats': suspect_nonself,
        'nonsuspect_nonself_svats': nonself - suspect_nonself,
        'self_donors': len(members) - nonself,
        'qualification_flag_counts': {field: flag_counts[field] for field in FLAGS},
        'reason_combinations': dict(sorted(reason_combinations.items())),
        'source_isverdacht_code_counts': dict(sorted(raw_code_counts.items())),
        'source_label_counts': dict(sorted(labels.items())),
        'flag_union_vs_original_isverdacht_mismatches': flag_union_mismatches,
        'all_donors_exist': True,
        'all_donors_in_same_hru': True,
        'all_donors_are_self_donors': True,
        'all_donors_are_not_suspect': True,
    }
    expected = {'membership_rows': 427656, 'unique_hrus': 10242, 'suspect_svats': 20934,
                'nonself_donors': 57880, 'nonsuspect_nonself_svats': 36946,
                'suspect_nonself_svats': 20934}
    for key, value in expected.items():
        require(checks[key] == value, 'Productiebron wijkt af voor {}: {}'.format(key, checks[key]))

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='donor_data_build_', dir=str(output)) as temporary:
        staging = Path(temporary)
        data_path = staging / DATA_NAME
        with data_path.open('wb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                    writer = csv.DictWriter(text, HEADERS, delimiter=',', lineterminator='\n')
                    writer.writeheader()
                    writer.writerows(members[sid] for sid in sorted(members))
        metadata = {
            'schema_version': 1,
            'profile': 'LWKM_HRU10242_ORIGINAL_QUALIFICATION_AND_OPERATIONAL_DONORS',
            'repository': 'abhedwig-cell/LWKM',
            'reference_commit': REFERENCE_COMMIT,
            'authority_paths': [
                'docs/production/WORK_B_20261019.md',
                'docs/lhm-hru-swap/SUSPECT-SVAT-DONOR-RECONCILIATION-2026-09-30.md',
                'tools/export_hru_interfaces.py',
                'config/source/work-b-source-register-20261019.json',
            ],
            'headers': HEADERS,
            'qualification_flags': list(FLAGS),
            'semantics': {
                'is_suspect': 'OR of the eight original qualification flags > 0; not donor != self.',
                'qualification_reason_ids': 'Original positive qualification field names in the fixed qualification_flags order, joined by |.',
                'hru_cluster_donor_svat': 'Existing operational donor from reference membership svat_donor; not legacy_pre_hru_donor_svat and not the HRU representative.',
                'membership': 'Original target SVAT identity and HRU are retained.',
                'scope': 'Binding only; this builder replaces no Frank values and invents no new criteria.',
                'legacy_snapshot_status': 'Source identities reconstructed and regression-qualified; this package does not claim new model-production qualification.',
            },
            'inputs': {
                'reference_membership': {'filename': membership_path.name, 'sha256': EXPECTED_MEMBERSHIP},
                'source_archive': {'filename': archive_path.name, 'sha256': EXPECTED_ARCHIVE},
                'original_qualification': {'archive_member': INFO_MEMBER, 'sha256': EXPECTED_INFO},
            },
            'outputs': {DATA_NAME: {'sha256': digest(data_path), 'size_bytes': data_path.stat().st_size}},
            'builder': {'filename': Path(__file__).name, 'sha256': digest(Path(__file__))},
            'checks': checks,
        }
        metadata_path = staging / SOURCE_NAME
        # Expliciete LF houdt de JSON-identiteit op Windows gelijk aan Linux.
        with metadata_path.open('w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        # Bronnen blijven tijdens het bouwen dezelfde versie.
        require(digest(membership_path) == EXPECTED_MEMBERSHIP, 'Membership gewijzigd tijdens bouwen')
        require(digest(archive_path) == EXPECTED_ARCHIVE, 'csv.zip gewijzigd tijdens bouwen')
        for name in (DATA_NAME, SOURCE_NAME):
            target = output / name
            if target.exists():
                require(digest(target) == digest(staging / name), 'Bestaand bouwresultaat wijkt af: ' + str(target))
        for name in (DATA_NAME, SOURCE_NAME):
            target = output / name
            if not target.exists():
                (staging / name).rename(target)
    return {'output': str(output), 'outputs': metadata['outputs'], 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--membership', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.membership, args.archive, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
