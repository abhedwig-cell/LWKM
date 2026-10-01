"""Inventory supplied DRA provenance without inferring a linked executable.

ZIP timestamps are untrusted wall-clock metadata, not executable identities.
This audit never admits producers or qualifies expected numerical differences.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(path):
    path = Path(path)
    if '9830' in path.name:
        raise ValueError('Excluded historical datamodel archive')
    result = {'archive': path.name, 'sha256': sha(path.read_bytes()),
              'source_versions': [], 'average_routines': [],
              'dra_members': [], 'build_or_executable_members': []}
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            name = item.filename
            low = name.lower()
            if low.endswith('/'):
                continue
            record = {'member': name, 'zip_timestamp': list(item.date_time),
                      'bytes': item.file_size}
            if low.endswith('.dra'):
                result['dra_members'].append(dict(record, sha256=sha(archive.read(item))))
            if low.endswith(('.exe', '.vfproj', '.sln', '.mak', '.vcxproj', '.obj', '.lib')):
                result['build_or_executable_members'].append(record)
            if low.endswith(('.f90', '.for')) and ('hrulist2swap' in low or 'alterratools' in low):
                raw = archive.read(item)
                text = raw.decode('latin1')
                if 'hrulist2swap' in low:
                    history = [line.strip() for line in text.splitlines()
                               if re.search(r'v0\.\d+', line, re.I)][:20]
                    result['source_versions'].append(dict(record, sha256=sha(raw), history=history))
                # Limit to the named routine; declaration and branch-local
                # writes elsewhere must not masquerade as initialization.
                match = re.search(r'(?im)^\s*REAL\*4\s+FUNCTION\s+average\b', text)
                if match:
                    end = re.search(r'(?im)^\s*END\s*$', text[match.end():])
                    if not end:
                        raise ValueError(f'Unterminated average routine: {name}')
                    routine = text[match.start():match.end()+end.end()]
                    active = '\n'.join(line for line in routine.splitlines()
                                       if not line.lstrip().startswith('!'))
                    branch = re.search(r'(?is)IF\s*\(nulist\s*\.GT\.\s*1\)\s*THEN(.*?)ELSEIF', active)
                    if not branch:
                        raise ValueError(f'Unrecognized average branch: {name}')
                    accumulation = re.search(r'(?im)^\s*average\s*=\s*average\s*\+', branch[1])
                    prefix = active[:active.index(branch[1])] + branch[1][:accumulation.start()] if accumulation else ''
                    initialized = bool(re.search(r'(?im)^\s*average\s*=\s*0(?:\.0*)?\s*$', prefix))
                    result['average_routines'].append(dict(record, sha256=sha(raw),
                        routine=routine, routine_sha256=sha(routine.encode('utf-8')),
                        finding='READ_BEFORE_INITIALIZATION_FOR_N_GT_1' if accumulation and not initialized else 'REQUIRES_REVIEW'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = {'status': 'PROVENANCE_AUDIT_NOT_ADMISSION',
              'timestamp_caveat': 'ZIP local timestamps are mutable, timezone-free metadata; no binary identity inferred',
              'archives': [inventory(path) for path in args.archives]}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'archives': len(result['archives']),
        'dra_members': sum(len(a['dra_members']) for a in result['archives']),
        'average_findings': sum(len(a['average_routines']) for a in result['archives'])}))


if __name__ == '__main__':
    main()
