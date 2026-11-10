"""Bind explicit run-local source paths. Read-only sources; no production runner.

The selected static reference run is not the aggregation period. Owner decisions
on shared static inputs and executable/source identity are retained, not reopened.
Standard library only; Python 3.8+ (including the confirmed Deltaforge Python).
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import tempfile

SOURCE_DECISION = 'LWKM-LHM-SOURCE-20261110-01'
REFERENCE_SHA = '7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df'
BINDING_FOLDER = 'LWKM_Frank_RunBinding_v01'
ALLOWED_INPUTS = {'area_svat.inp', 'mod2svat.inp', 'scap_svat.inp',
                  'dldra_svat.inp', 'dqsat_svat.inp', 'idf_svat.inp'}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def relative_file(root: Path, value: str) -> Path:
    """No absolute paths, traversal, drives or junction escapes in relative fields."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Relative file path must be a nonempty string')
    parts = value.replace('\\', '/').split('/')
    if (PureWindowsPath(value).drive or value.startswith(('/', '\\'))
            or any(p in ('', '.', '..') or ':' in p for p in parts)):
        raise ValueError('Invalid relative file path: ' + value)
    result = root.joinpath(*parts)
    if not inside(result, root):
        raise ValueError('Path escapes its source root: ' + value)
    return result


def file_record(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError('Source file not found: ' + str(path))
    before = path.stat()
    sha = digest(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Source changed while fingerprinting: ' + str(path))
    return {'path': str(path.resolve()), 'bytes': after.st_size, 'sha256': sha}


def build_binding(config_path: Path) -> tuple:
    """Return a proposed manifest and safe target; never write to source folders."""
    config_path = config_path.resolve()
    config_bytes = config_path.read_bytes()
    c = json.loads(config_bytes.decode('utf-8-sig'))
    if not isinstance(c, dict):
        raise ValueError('Configuration must be a JSON object')
    if c.get('schema_version') != 1 or c.get('source_profile') != 'run_local':
        raise ValueError('Expected schema_version=1 and source_profile=run_local')
    root_value = c.get('runs_root', '')
    if not isinstance(root_value, str) or not root_value.strip():
        raise ValueError('runs_root must be an explicit absolute path')
    runs = Path(root_value)
    if not runs.is_absolute() or not runs.is_dir():
        raise ValueError('runs_root is not an available absolute directory: ' + str(runs))
    runs = runs.resolve()
    run = c.get('static_reference_run', '')
    if not isinstance(run, str) or not re.fullmatch(r'run_\d{4}_\d{4}(?:_[A-Za-z0-9_-]+)?', run):
        raise ValueError('Invalid explicit static_reference_run')
    # Deliberately no recursive discovery, global fallback or assumed /inp suffix.
    metaswap = runs / run / 'metaswap'
    authority = runs / 'LWKM_run_resultaten_totaal'
    if (not metaswap.is_dir() or not inside(runs / run, runs)
            or not inside(metaswap, runs / run)):
        raise ValueError('Run-local metaswap directory unavailable or redirected: ' + str(metaswap))
    if not authority.is_dir() or not inside(authority, runs):
        raise ValueError('Authorized LHM output root unavailable or redirected: ' + str(authority))
    definitions = c.get('static_files')
    if not isinstance(definitions, dict) or 'area_svat.inp' not in definitions:
        raise ValueError('static_files must explicitly include area_svat.inp')
    records, missing = {}, []
    for name, item in definitions.items():
        if name not in ALLOWED_INPUTS or not isinstance(item, dict):
            raise ValueError('Unsupported static input definition: ' + str(name))
        required = item.get('required', False)
        if not isinstance(required, bool):
            raise ValueError('required must be boolean for ' + name)
        if name == 'area_svat.inp' and not required:
            raise ValueError('area_svat.inp must remain required')
        path = relative_file(metaswap, item.get('path', ''))
        if path.name.lower() != name:
            raise ValueError('Logical filename does not match explicit path: ' + name)
        if not path.is_file():
            if required:
                raise FileNotFoundError('Required run-local file missing: ' + str(path))
            missing.append({'logical_file': name, 'path': str(path), 'status': 'NOT_PRESENT_AT_EXPLICIT_PATH'})
            continue
        records[name] = file_record(path)
    # Carry the existing INI inventory as DECLARED context. Do not infer which of
    # several variants was active, or relabel directory presence as execution proof.
    inventory = {'status': 'NOT_SUPPLIED', 'run_contexts': []}
    inventory_rel = c.get('ini_inventory')
    if inventory_rel:
        source = relative_file(runs, inventory_rel)
        inventory = {'status': 'NOT_AVAILABLE', 'path': str(source), 'run_contexts': []}
        if source.is_file():
            inventory_bytes = source.read_bytes()
            data = json.loads(inventory_bytes.decode('utf-8-sig'))
            if not isinstance(data, dict):
                raise ValueError('INI inventory must be a JSON object')
            controls = data.get('ini_files')
            if not isinstance(controls, list):
                raise ValueError('INI inventory must contain an ini_files list')
            inventory = {'status': 'DECLARED_CONTEXT_ONLY', 'path': str(source.resolve()),
                         'sha256': hashlib.sha256(inventory_bytes).hexdigest(),
                         'run_contexts': controls}
    target_root = runs / 'LWKM_tools' / BINDING_FOLDER
    target = target_root / 'run_source_binding.json'
    if (not inside(runs / 'LWKM_tools', runs)
            or not inside(target_root, runs / 'LWKM_tools')):
        raise ValueError('Binding destination escapes its dedicated directory')
    if any(inside(target_root, protected) for protected in (metaswap, authority)):
        raise ValueError('Binding destination overlaps protected source data')
    # A pre-existing unrecognized file is never silently replaced.
    if target.is_symlink():
        raise ValueError('Binding target may not be a symlink')
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf-8'))
        if previous.get('kind') != 'LWKM_RUN_SOURCE_BINDING':
            raise ValueError('Refusing to replace an unrelated existing file: ' + str(target))
    report = {
        'schema_version': 1, 'kind': 'LWKM_RUN_SOURCE_BINDING',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'SOURCE_BINDING_ONLY', 'production_enabled': False,
        'source_profile': 'run_local', 'static_reference_run': run,
        'metaswap_input_root': str(metaswap.resolve()),
        'output_authority_root': str(authority.resolve()),
        'static_input_identity': 'OWNER_ESTABLISHED_IDENTICAL_BETWEEN_RUNS',
        'cross_run_hash_comparison': 'OPTIONAL_QA_NOT_REQUIRED_AND_NOT_PERFORMED',
        'source_executable_authority': SOURCE_DECISION,
        'static_files': records, 'optional_files_not_present': missing,
        'declared_run_context': inventory,
        'historical_reference': {
            'filename': 'FRANK_SVAT_BASIS_ONGECORRIGEERD_1991_2020.csv',
            'expected_sha256': REFERENCE_SHA,
            'status': 'PROTECTED_NOT_READ_OR_REUSED_BY_THIS_TOOL'},
        'provenance': {
            'config_path': str(config_path),
            'config_sha256': hashlib.sha256(config_bytes).hexdigest(),
            'binding_code_sha256': digest(Path(__file__))},
        'not_established_by_this_tool': [
            'Producer-specific completeness and numerical equivalence',
            'Which INI variant and restart chain were executed for each run',
            'Qualification of existing or newly calculated SVAT/HRU output'],
        'source_file_mutations': 0, 'producers_executed': 0,
    }
    return report, target


def write_binding(config_path: Path) -> Path:
    report, target = build_binding(config_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.binding_', suffix='.partial', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        target = write_binding(args.config)
    except (OSError, ValueError, TypeError) as exc:
        print('STOP: ' + str(exc), file=sys.stderr)
        return 2
    print('SOURCE_BINDING_ONLY: ' + str(target))
    print('No producer executed; production_enabled=false.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
