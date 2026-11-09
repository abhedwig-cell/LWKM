"""Read-only, fail-visible LHM run-definition inventory for Frank's LHM433 baseline.

No file named in an INI is automatically treated as the historic executed input.
Outputs are evidence inventories, not a verified reconstruction of execution.
Python 3.8+ standard library only, Windows paths preserved.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys

LINE = re.compile(r'^\s*([^#;][^=]*?)\s*=\s*(.*?)\s*(?:[#;].*)?$')
SECTION = re.compile(r'^\s*(\[{1,4})([^\]]+)(\]{1,4})\s*$')
INTERPOLATION = re.compile(r'%\(([^)]+)\)s')
PERIOD = re.compile(r'(19|20)\d\d[_-](19|20)\d\d')

def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def parse_ini(path: Path) -> dict:
    raw = path.read_text(encoding='utf-8-sig', errors='replace').splitlines()
    sections = [''] * 5
    declarations = []
    aliases = {}
    for lineno, line in enumerate(raw, 1):
        match = SECTION.match(line)
        if match:
            level = len(match.group(1))
            sections[level] = match.group(2).strip()
            for index in range(level + 1, len(sections)):
                sections[index] = ''
            continue
        if not line.strip() or line.lstrip().startswith(('#', ';')):
            continue
        match = LINE.match(line)
        if not match:
            continue
        key, value = match.group(1).strip(), match.group(2).strip()
        declarations.append({'line': lineno, 'section': '/'.join(s for s in sections if s),
                             'key': key, 'raw': value})
        aliases[key] = value

    def resolve(value):
        visited = set()
        for _ in range(32):
            m = INTERPOLATION.search(value)
            if not m or m.group(1) not in aliases or m.group(1) in visited:
                break
            visited.add(m.group(1))
            value = value[:m.start()] + aliases[m.group(1)] + value[m.end():]
        return value

    paths = []
    for d in declarations:
        value = resolve(d['raw']).strip(' "\'')
        d['resolved'] = value
        if re.match(r'^[A-Za-z]:\\', value) or value.startswith('\\\\') or '\\' in value:
            paths.append({'line': d['line'], 'section': d['section'], 'key': d['key'],
                          'declared': d['raw'], 'resolved': value,
                          'status': 'DECLARED_ONLY_NOT_HISTORICALLY_VERIFIED'})
    return {'path': str(path), 'sha256': checksum(path), 'bytes': path.stat().st_size,
            'period_hint': PERIOD.search(path.name).group() if PERIOD.search(path.name) else None,
            'declarations': declarations, 'path_candidates': paths}

def inventory(roots, glob_pattern):
    files = {}
    for root in roots:
        p = Path(root)
        if p.is_file() and p.suffix.lower() == '.ini':
            files[str(p.resolve()).lower()] = p
        elif p.is_dir():
            for f in p.rglob(glob_pattern):
                if f.is_file() and f.suffix.lower() == '.ini':
                    files[str(f.resolve()).lower()] = f
    return [files[k] for k in sorted(files)]

def produce(roots, pattern, out, output_root):
    found = inventory(roots, pattern)
    controls = [parse_ini(p) for p in found]
    result = {
      'schema_version': 1, 'model': 'LHM 4.3.3',
      'status': 'INPUT_CONFIG_AUTHORITY_PARTIAL' if found else 'BLOCKED_NO_INI_FOUND',
      'source_authority': 'project-owner supplied control_run INI; current path identity unproven',
      'output_authority_root': str(output_root),
      'output_authority': 'Deltares-collected LWKM_run_resultaten_totaal',
      'source_discovery': {'roots': [str(x) for x in roots], 'pattern': pattern},
      'ini_count': len(found), 'ini_files': controls,
      'unverified': ['exact executed INI hashes not bound to LHM output',
                     'period restart chain not proven', 'referenced original input file hashes not bound'],
      'source_file_mutations': 0
    }
    out.mkdir(parents=True, exist_ok=True)
    temp = out / 'lhm_run_definition.json.partial'
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(out / 'lhm_run_definition.json')
    with (out / 'lhm_ini_references.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['ini','line','section','key','declared','resolved','status'])
        writer.writeheader()
        for c in controls:
            for entry in c['path_candidates']:
                writer.writerow({'ini': c['path'], **entry})
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ini-root', action='append', required=True)
    parser.add_argument('--pattern', default='control_run_*.ini')
    parser.add_argument('--out', required=True)
    parser.add_argument('--output-root', required=True)
    a = parser.parse_args(argv)
    status = produce(a.ini_root, a.pattern, Path(a.out), a.output_root)
    print('LHM definition:', status['status'], 'INI count:', status['ini_count'])
    return 0 if status['ini_count'] else 2

if __name__ == '__main__':
    sys.exit(main())
