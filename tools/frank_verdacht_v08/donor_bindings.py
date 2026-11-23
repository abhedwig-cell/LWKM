"""Lees de vastgelegde verdachtheid en operationele SVAT-donorkoppeling.

Verdachtheid volgt uitsluitend uit de oorspronkelijke kwalificatievelden.
Een operationele donor die van de eigen SVAT verschilt is op zichzelf geen
reden om een SVAT als verdacht aan te merken.
"""

from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path


DATA_NAME = 'SVAT_DONOR_QUALIFICATION.csv.gz'
SOURCE_NAME = 'DONOR_SOURCES.json'
HEADERS = ['svat', 'HRU', 'hru_cluster_donor_svat', 'is_suspect',
           'qualification_reason_ids', 'label']
QUALIFICATION_FLAGS = ('ghg_sel', 'gt1_sel', 'gt2_sel', 'gt8_sel', 'kwel_sel',
                       'wegzijging_sel', 'runoff_sel', 'subinfil_sel')
CHECK_FIELDS = ('membership_rows', 'unique_hrus', 'suspect_svats',
                'nonsuspect_svats', 'nonself_donors', 'suspect_nonself_svats',
                'nonsuspect_nonself_svats', 'self_donors')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _positive_integer(value, label):
    if isinstance(value, bool):
        raise ValueError('Ongeldige positieve integer voor ' + label)
    text = str(value).strip()
    if not text.isdigit() or int(text) <= 0:
        raise ValueError('Ongeldige positieve integer voor {}: {!r}'.format(label, value))
    return int(text)


def _nonnegative_integer(value, label):
    if isinstance(value, bool):
        raise ValueError('Ongeldig controletotaal voor ' + label)
    text = str(value).strip()
    if not text.isdigit():
        raise ValueError('Ongeldig controletotaal voor {}: {!r}'.format(label, value))
    return int(text)


def _check_reasons(text, is_suspect, sid):
    reasons = text.split('|') if text else []
    if len(reasons) != len(set(reasons)):
        raise ValueError('Dubbele kwalificatiereden bij SVAT ' + str(sid))
    if any(reason not in QUALIFICATION_FLAGS for reason in reasons):
        raise ValueError('Onbekende kwalificatiereden bij SVAT ' + str(sid))
    canonical = [reason for reason in QUALIFICATION_FLAGS if reason in reasons]
    if reasons != canonical:
        raise ValueError('Kwalificatieredenen niet in vaste bronvolgorde bij SVAT ' + str(sid))
    if bool(reasons) != is_suspect:
        raise ValueError('Verdacht-indicator en kwalificatieredenen verschillen bij SVAT ' + str(sid))
    return reasons


def load_bindings(directory, membership):
    """Geef ``(bindings, metadata)`` terug voor exact de meegegeven membership.

    ``membership`` heeft integer SVAT-IDs als sleutels en HRU-IDs als waarden.
    ``bindings[sid]`` bevat ``svat``, ``HRU`` en ``donor`` als integer,
    ``is_suspect`` als bool en ``reasons`` en ``label`` als string.

    Alle aantallen worden aan het bijbehorende manifest getoetst. Er zijn geen
    vaste productieaantallen in deze loader, zodat kleine zelfstandige fixtures
    dezelfde controles doorlopen. Donoren moeten wel altijd bestaan, in dezelfde
    HRU zitten, zichzelf als operationele donor hebben en niet verdacht zijn.
    """
    directory = Path(directory)
    source_path = directory / SOURCE_NAME
    data_path = directory / DATA_NAME
    with source_path.open('r', encoding='utf-8') as handle:
        metadata = json.load(handle)
    if metadata.get('schema_version') != 1:
        raise ValueError('Niet-ondersteunde versie van ' + SOURCE_NAME)
    if metadata.get('headers') != HEADERS:
        raise ValueError('Donorbronmanifest heeft een ander kolomschema')
    if metadata.get('qualification_flags') != list(QUALIFICATION_FLAGS):
        raise ValueError('Donorbronmanifest heeft andere kwalificatievelden')
    try:
        expected_digest = metadata['outputs'][DATA_NAME]['sha256']
        expected_size = metadata['outputs'][DATA_NAME]['size_bytes']
        expected_counts = metadata['checks']
    except (KeyError, TypeError):
        raise ValueError('Onvolledig donorbronmanifest: ' + str(source_path))
    if not isinstance(expected_digest, str) or len(expected_digest) != 64:
        raise ValueError('Ongeldige SHA256 in donorbronmanifest')
    if data_path.stat().st_size != _nonnegative_integer(expected_size, DATA_NAME + ' bytes'):
        raise ValueError('Bestandsgrootte van de donorkoppeling wijkt af: ' + str(data_path))
    if sha256(data_path) != expected_digest:
        raise ValueError('SHA256 van de donorkoppeling wijkt af: ' + str(data_path))
    if not membership:
        raise ValueError('Lege SVAT-HRU-membership')
    for sid, hru in membership.items():
        # Een string-sleutel mag een ontbrekende integer-key niet verhullen.
        if isinstance(sid, bool) or _positive_integer(sid, 'membership SVAT') != sid:
            raise ValueError('Membership vereist integer SVAT-sleutels')
        _positive_integer(hru, 'membership HRU')

    bindings = {}
    label_pool = {}
    reason_pool = {}
    reason_counts = Counter()
    with gzip.open(str(data_path), 'rt', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter=',')
        if reader.fieldnames != HEADERS:
            raise ValueError('Onjuist kolomschema of scheidingsteken in donorkoppeling')
        for lineno, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Onjuist aantal velden in donorkoppeling op regel ' + str(lineno))
            sid = _positive_integer(row['svat'], 'donorkoppeling SVAT')
            hru = _positive_integer(row['HRU'], 'donorkoppeling HRU')
            donor = _positive_integer(row['hru_cluster_donor_svat'], 'operationele donor')
            if sid in bindings:
                raise ValueError('Dubbele SVAT in donorkoppeling: ' + str(sid))
            if sid not in membership:
                raise ValueError('SVAT uit donorkoppeling ontbreekt in membership: ' + str(sid))
            if hru != _positive_integer(membership[sid], 'membership HRU'):
                raise ValueError('HRU van donorkoppeling wijkt af van membership bij SVAT ' + str(sid))
            if row['is_suspect'] not in ('0', '1'):
                raise ValueError('Verdacht-indicator moet 0 of 1 zijn bij SVAT ' + str(sid))
            is_suspect = row['is_suspect'] == '1'
            reasons = row['qualification_reason_ids']
            reason_counts.update(_check_reasons(reasons, is_suspect, sid))
            label = row['label']
            if not label.strip():
                raise ValueError('Oorspronkelijk membershiplabel ontbreekt bij SVAT ' + str(sid))
            label = label_pool.setdefault(label, label)
            reasons = reason_pool.setdefault(reasons, reasons)
            bindings[sid] = {'svat': sid, 'HRU': hru, 'donor': donor,
                             'is_suspect': is_suspect, 'reasons': reasons, 'label': label}
    if len(bindings) != len(membership):
        missing = [int(sid) for sid in membership if sid not in bindings][:10]
        raise ValueError('Donorkoppeling mist SVATs uit membership, bijvoorbeeld ' + str(missing))

    for sid, record in bindings.items():
        donor = record['donor']
        if donor not in bindings:
            raise ValueError('Operationele donor {} ontbreekt voor SVAT {}'.format(donor, sid))
        source = bindings[donor]
        if source['HRU'] != record['HRU']:
            raise ValueError('Operationele donor zit in een andere HRU bij SVAT ' + str(sid))
        if source['donor'] != donor:
            raise ValueError('Operationele donor is geen zelfdonor bij SVAT ' + str(sid))
        if source['is_suspect']:
            raise ValueError('Operationele donor is zelf verdacht bij SVAT ' + str(sid))
        record['donor'] = source['svat']

    nonself = sum(sid != record['donor'] for sid, record in bindings.items())
    suspect = sum(record['is_suspect'] for record in bindings.values())
    suspect_nonself = sum(record['is_suspect'] and sid != record['donor']
                          for sid, record in bindings.items())
    observed = {
        'membership_rows': len(bindings),
        'unique_hrus': len({record['HRU'] for record in bindings.values()}),
        'suspect_svats': suspect,
        'nonsuspect_svats': len(bindings) - suspect,
        'nonself_donors': nonself,
        'suspect_nonself_svats': suspect_nonself,
        'nonsuspect_nonself_svats': nonself - suspect_nonself,
        'self_donors': len(bindings) - nonself,
    }
    for field in CHECK_FIELDS:
        if field not in expected_counts:
            raise ValueError('Donorbronmanifest mist controletotaal: ' + field)
        if observed[field] != _nonnegative_integer(expected_counts[field], field):
            raise ValueError('Controletotaal {} wijkt af: {} versus {}'.format(
                field, observed[field], expected_counts[field]))
    expected_reasons = expected_counts.get('qualification_flag_counts')
    if not isinstance(expected_reasons, dict) or set(expected_reasons) != set(QUALIFICATION_FLAGS):
        raise ValueError('Donorbronmanifest mist aantallen per kwalificatieveld')
    for field in QUALIFICATION_FLAGS:
        if reason_counts[field] != _nonnegative_integer(expected_reasons[field], field):
            raise ValueError('Aantal kwalificatieredenen wijkt af voor ' + field)
    if sha256(data_path) != expected_digest:
        raise ValueError('Donorkoppeling is tijdens het lezen gewijzigd')
    return bindings, metadata
