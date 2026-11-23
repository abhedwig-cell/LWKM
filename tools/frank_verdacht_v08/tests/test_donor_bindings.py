import csv
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from collections import Counter

from donor_bindings import (DATA_NAME, SOURCE_NAME, HEADERS, QUALIFICATION_FLAGS,
                            load_bindings, sha256)


def record(svat, hru, donor, suspect=False, reasons='', label='valid'):
    return {'svat': str(svat), 'HRU': str(hru),
            'hru_cluster_donor_svat': str(donor),
            'is_suspect': '1' if suspect else '0',
            'qualification_reason_ids': reasons, 'label': label}


class TestDonorBindings(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='frank_donor_binding_test_')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.membership = {1: 10, 2: 10, 3: 10, 4: 20, 5: 20}
        self.records = [
            record(1, 10, 1),
            record(2, 10, 1, True, 'ghg_sel|kwel_sel', 'Toegevoegd'),
            record(3, 10, 1, False, '', 'Toegevoegd'),
            record(4, 20, 4),
            record(5, 20, 4, True, 'gt2_sel', 'Toegevoegd'),
        ]

    def write_fixture(self, records=None, headers=None):
        rows = self.records if records is None else records
        headers = HEADERS if headers is None else headers
        data = self.directory / DATA_NAME
        with data.open('wb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                    writer = csv.DictWriter(text, headers, delimiter=',', lineterminator='\n')
                    writer.writeheader()
                    writer.writerows(rows)
        suspect = sum(row['is_suspect'] == '1' for row in rows)
        nonself = sum(row['svat'] != row['hru_cluster_donor_svat'] for row in rows)
        suspect_nonself = sum(row['is_suspect'] == '1' and row['svat'] != row['hru_cluster_donor_svat']
                              for row in rows)
        reasons = Counter(reason for row in rows for reason in row['qualification_reason_ids'].split('|') if reason)
        metadata = {
            'schema_version': 1,
            'headers': HEADERS,
            'qualification_flags': list(QUALIFICATION_FLAGS),
            'outputs': {DATA_NAME: {'sha256': sha256(data), 'size_bytes': data.stat().st_size}},
            'checks': {
                'membership_rows': len(rows),
                'unique_hrus': len({row['HRU'] for row in rows}),
                'suspect_svats': suspect,
                'nonsuspect_svats': len(rows) - suspect,
                'nonself_donors': nonself,
                'suspect_nonself_svats': suspect_nonself,
                'nonsuspect_nonself_svats': nonself - suspect_nonself,
                'self_donors': len(rows) - nonself,
                'qualification_flag_counts': {flag: reasons[flag] for flag in QUALIFICATION_FLAGS},
            },
        }
        self.write_metadata(metadata)
        return metadata

    def write_metadata(self, metadata):
        (self.directory / SOURCE_NAME).write_text(json.dumps(metadata), encoding='utf-8')

    def test_loads_types_and_does_not_equate_nonself_with_suspect(self):
        expected_metadata = self.write_fixture()
        bindings, metadata = load_bindings(self.directory, self.membership)
        self.assertEqual(set(bindings), set(self.membership))
        self.assertEqual(metadata, expected_metadata)
        self.assertEqual(bindings[2], {'svat': 2, 'HRU': 10, 'donor': 1,
                                      'is_suspect': True, 'reasons': 'ghg_sel|kwel_sel',
                                      'label': 'Toegevoegd'})
        self.assertEqual(bindings[3]['donor'], 1)
        self.assertIs(bindings[3]['is_suspect'], False)
        self.assertEqual(metadata['checks']['suspect_svats'], 2)
        self.assertEqual(metadata['checks']['nonsuspect_nonself_svats'], 1)

    def test_hash_change_is_rejected_before_reading_compressed_data(self):
        self.write_fixture()
        path = self.directory / DATA_NAME
        data = bytearray(path.read_bytes())
        data[-5] ^= 1
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            load_bindings(self.directory, self.membership)

    def test_missing_and_extra_membership_ids_are_rejected(self):
        self.write_fixture(self.records[:-1])
        with self.assertRaisesRegex(ValueError, 'mist SVATs'):
            load_bindings(self.directory, self.membership)
        self.write_fixture()
        membership = dict(self.membership)
        del membership[5]
        with self.assertRaisesRegex(ValueError, 'ontbreekt in membership'):
            load_bindings(self.directory, membership)

    def test_duplicate_target_id_is_rejected(self):
        self.write_fixture(self.records + [dict(self.records[0])])
        with self.assertRaisesRegex(ValueError, 'Dubbele SVAT'):
            load_bindings(self.directory, self.membership)

    def test_hru_assignment_must_match_membership(self):
        self.write_fixture()
        membership = dict(self.membership)
        membership[2] = 20
        with self.assertRaisesRegex(ValueError, 'HRU van donorkoppeling'):
            load_bindings(self.directory, membership)

    def test_donor_must_exist_in_selected_population(self):
        self.records[1]['hru_cluster_donor_svat'] = '99'
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, 'donor 99 ontbreekt'):
            load_bindings(self.directory, self.membership)

    def test_donor_must_be_in_same_hru(self):
        self.records[1]['hru_cluster_donor_svat'] = '4'
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, 'andere HRU'):
            load_bindings(self.directory, self.membership)

    def test_chained_donor_is_rejected(self):
        self.records[2]['hru_cluster_donor_svat'] = '2'
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, 'geen zelfdonor'):
            load_bindings(self.directory, self.membership)

    def test_suspect_source_donor_is_rejected(self):
        self.records[0].update({'is_suspect': '1', 'qualification_reason_ids': 'kwel_sel'})
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, 'zelf verdacht'):
            load_bindings(self.directory, self.membership)

    def test_reason_flags_must_be_known_ordered_and_match_suspicion(self):
        for suspect, reasons, message in [
            ('1', '', 'Verdacht-indicator'),
            ('0', 'ghg_sel', 'Verdacht-indicator'),
            ('1', 'donor_differs', 'Onbekende kwalificatiereden'),
            ('1', 'kwel_sel|ghg_sel', 'vaste bronvolgorde'),
            ('1', 'ghg_sel|ghg_sel', 'Dubbele kwalificatiereden'),
        ]:
            with self.subTest(suspect=suspect, reasons=reasons):
                rows = [dict(row) for row in self.records]
                rows[1].update({'is_suspect': suspect, 'qualification_reason_ids': reasons})
                self.write_fixture(rows)
                with self.assertRaisesRegex(ValueError, message):
                    load_bindings(self.directory, self.membership)

    def test_indicator_and_target_ids_must_have_exact_types(self):
        for key, value, message in [
            ('is_suspect', '2', '0 of 1'),
            ('svat', '2.0', 'positieve integer'),
            ('hru_cluster_donor_svat', '0', 'positieve integer'),
        ]:
            with self.subTest(key=key, value=value):
                rows = [dict(row) for row in self.records]
                rows[1][key] = value
                self.write_fixture(rows)
                with self.assertRaisesRegex(ValueError, message):
                    load_bindings(self.directory, self.membership)

    def test_manifest_counts_and_reason_counts_are_checked(self):
        metadata = self.write_fixture()
        metadata['checks']['suspect_svats'] = 3
        self.write_metadata(metadata)
        with self.assertRaisesRegex(ValueError, 'Controletotaal suspect_svats'):
            load_bindings(self.directory, self.membership)
        metadata = self.write_fixture()
        metadata['checks']['qualification_flag_counts']['ghg_sel'] = 99
        self.write_metadata(metadata)
        with self.assertRaisesRegex(ValueError, 'kwalificatieredenen wijkt af'):
            load_bindings(self.directory, self.membership)

    def test_exact_schema_and_qualification_fields_are_required(self):
        self.write_fixture(headers=list(reversed(HEADERS)))
        with self.assertRaisesRegex(ValueError, 'kolomschema'):
            load_bindings(self.directory, self.membership)
        metadata = self.write_fixture()
        metadata['qualification_flags'] = ['donor_differs']
        self.write_metadata(metadata)
        with self.assertRaisesRegex(ValueError, 'andere kwalificatievelden'):
            load_bindings(self.directory, self.membership)


if __name__ == '__main__':
    unittest.main()
