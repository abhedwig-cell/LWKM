"""Isolated clean-run adapter for the frozen Frank MetaSWAP base producer.

Check is read-only except for the requested report. Run publishes a new directory
only after unchanged-source and output checks. No whole-chain production approval.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace

HERE = Path(__file__).resolve().parent
REGISTRY = HERE.parents[1] / 'config/production/frank_original_producers_sha256_v01.json'
ROLES = ('bdgpm', 'bdgetact', 'bdgqrun', 'bdgdecstot', 'bdgpssw', 'bdgpsgw')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inside(path, parent):
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def atomic_json(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + '.partial')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def frozen_modules():
    registry = json.loads(REGISTRY.read_text(encoding='utf-8'))['files']
    if len(registry) != 12:
        raise ValueError('Expected the complete twelve-file source register')
    sources = [HERE / 'legacy' / name for name in registry]
    for path in sources:
        if sha(path) != registry[path.name]:
            raise ValueError('Historical source differs from registered bytes: ' + path.name)
    def load(name):
        module = ModuleType(name)
        path = HERE / 'legacy' / (name + '.py')
        module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        return module
    reader = load('wb10_reader')
    previous = sys.modules.get('wb10_reader')
    sys.modules['wb10_reader'] = reader
    try:
        producer = load('build_svat_base')
    finally:
        if previous is None:
            del sys.modules['wb10_reader']
        else:
            sys.modules['wb10_reader'] = previous
    return reader, producer, sources


def prepare(config_path):
    config_path = Path(config_path).resolve()
    c = json.loads(config_path.read_text(encoding='utf-8-sig'))
    if c.get('schema_version') != 1:
        raise ValueError('Unknown configuration schema')
    first, last = c['from_year'], c['to_year']
    if type(first) is not int or type(last) is not int or not 1970 <= first <= last <= 2022:
        raise ValueError('Expected a calendar period within 1970 to 2022')
    binding_path = Path(c['binding'])
    if not binding_path.is_absolute():
        raise ValueError('The source-binding path must be absolute')
    binding_hash = sha(binding_path)
    if binding_hash != c['binding_sha256']:
        raise ValueError('Source binding differs from the explicitly selected manifest')
    b = json.loads(binding_path.read_text(encoding='utf-8-sig'))
    if (b.get('kind'), b.get('source_profile'), b.get('source_executable_authority')) != (
            'LWKM_RUN_SOURCE_BINDING', 'run_local', 'LWKM-LHM-SOURCE-20261110-01'):
        raise ValueError('Not the accepted run-local source-binding type')
    authority = Path(b['output_authority_root'])
    metaswap = Path(b['metaswap_input_root'])
    runs = authority.parent
    if not authority.is_absolute() or authority.name != 'LWKM_run_resultaten_totaal':
        raise ValueError('Unexpected authorized output root')
    expected = runs / b['static_reference_run'] / 'metaswap'
    if (not metaswap.is_absolute() or metaswap.resolve() != expected.resolve()
            or not inside(metaswap, runs) or not inside(authority, runs)):
        raise ValueError('Static source escapes the explicit reference run')
    area = Path(b['static_files']['area_svat.inp']['path'])
    if not area.is_absolute() or not inside(area, metaswap) or area.name != 'area_svat.inp':
        raise ValueError('area_svat.inp is not inside the selected run')
    if sha(area) != b['static_files']['area_svat.inp']['sha256']:
        raise ValueError('area_svat.inp differs from the accepted source binding')
    reader, producer, code_paths = frozen_modules()
    # Preserve the original parser and validations; derive only its expected count
    # from this explicit source instead of enforcing the historical 645582.
    count = 0
    with area.open(encoding='utf-8-sig', errors='replace') as stream:
        for line in stream:
            words = line.strip().replace(',', '.').split()
            if words and reader.re.fullmatch(r'\d+', words[0]):
                count += 1
    if not count:
        raise ValueError('No SVAT records in selected source')
    reader.EXPECTED_SVATS = count
    ids, areas, xs, ys = reader.read_area(area)
    root = authority / 'metaswap'
    catalog = producer.period_index(root, range(first, last + 1))
    inputs = [area]
    for year in range(first, last + 1):
        inputs.extend(producer.year_inputs(year, catalog).values())
    if not all(inside(path, authority) for path in inputs[1:]):
        raise ValueError('An IDF source escapes the authorized output directory')
    river = runs / 'LHM_uitvoer/filter/Riv_infiltratie_1991-2020_sum.asc'
    if first == 1991 and last == 2020 and river.is_file():
        if not inside(river, runs):
            raise ValueError('Historical optional infiltration grid escapes workspace')
        inputs.append(river)
    target = runs / 'LWKM_tools/LWKM_Frank_Rebuild_v03' / ('msw_basic_%s_%s' % (first, last))
    # No redirected output ancestors: keep new products in the dedicated namespace.
    chain = [target, target.parent, target.parent.parent]
    redirected = any(p.resolve() != p.absolute() for p in chain)
    if redirected or not inside(target, runs) or inside(target, authority) or inside(target, metaswap):
        raise ValueError('Unsafe or redirected output directory')
    report = {
        'status': 'MSW_BASIC_SOURCES_OK', 'whole_chain_production_enabled': False,
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'binding_sha256': binding_hash, 'period': [first, last],
        'svat_count': len(ids), 'population_policy': 'ALL_VALID_RECORDS_FROM_BOUND_AREA_FILE',
        'historical_reference_count': 645582, 'historical_count_enforced': False,
        'area_file': str(area), 'area_sha256': sha(area),
        'source_root': str(root), 'source_roles': list(ROLES),
        'decades': 36 * (last - first + 1), 'idf_files': 216 * (last - first + 1),
        'optional_infiltration_used': river in inputs,
        'target': str(target), 'target_exists': target.exists(),
        'source_content_check': 'AREA_SHA256_ONLY; IDF_CONTENT_NOT_YET_READ',
        'original_sources_verified': len(code_paths), 'producers_executed': 0,
    }
    args = SimpleNamespace(root=root, area=area, lhm_workspace=runs,
                           out=None, from_year=first, to_year=last)
    return report, producer, args, inputs + code_paths + [REGISTRY, Path(__file__), config_path, binding_path]


def run_stage(config_path):
    report, producer, args, paths = prepare(config_path)
    target = Path(report['target'])
    if target.exists():
        raise FileExistsError('Clean-run only; existing output is never reused or overwritten: ' + str(target))
    # Full hashes are computed only for the explicitly requested isolated run.
    fingerprints = {str(path): sha(path) for path in paths}
    river = args.lhm_workspace / 'LHM_uitvoer/filter/Riv_infiltratie_1991-2020_sum.asc'
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.' + target.name + '_', dir=target.parent))
    try:
        args.out = staging
        producer.execute(args)
        for path in paths:
            if sha(path) != fingerprints[str(path)]:
                raise ValueError('Dependency changed during execution: ' + str(path))
        if args.from_year == 1991 and args.to_year == 2020 and river.is_file() != report['optional_infiltration_used']:
            raise ValueError('Optional infiltration source presence changed during execution')
        producer_manifest = json.loads((staging / ('manifest_%s_%s.json' % (args.from_year, args.to_year))).read_text(encoding='utf-8'))
        report['complete_source_svats'] = producer_manifest['complete_source_svats']
        report['all_svats_complete'] = report['complete_source_svats'] == report['svat_count']
        report['numerical_qualification'] = 'NOT_ESTABLISHED_FOR_NHI_DATA'
        report.update(status='MSW_BASIC_ISOLATED_RUN_COMPLETE', producers_executed=1,
                      source_content_check='ALL_DECLARED_DEPENDENCIES_SHA256_BEFORE_AND_AFTER',
                      staging_path_at_execution=str(staging), input_and_code_sha256=fingerprints)
        report['output_sha256'] = {str(p.relative_to(staging)): sha(p)
                                  for p in sorted(staging.rglob('*')) if p.is_file()}
        atomic_json(staging / 'RUN_RECEIPT.json', report)
        if target.exists():
            raise FileExistsError('Output was created concurrently; refusing replacement')
        staging.rename(target)
        return report
    except Exception as exc:
        atomic_json(staging / 'FAILED.json', {'status': 'NOT_PUBLISHED', 'reason': str(exc),
                                            'whole_chain_production_enabled': False})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--run', action='store_true', help='Execute only msw_basic in a new isolated directory')
    a = parser.parse_args(argv)
    try:
        report = run_stage(a.config) if a.run else prepare(a.config)[0]
        atomic_json(a.report, report)
        print(report['status'], 'SVATs:', report['svat_count'], 'IDFs:', report['idf_files'])
        print('Report:', a.report)
        return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        atomic_json(a.report, {'status': 'STOPPED', 'reason': str(exc), 'whole_chain_production_enabled': False})
        print('STOP MSW_BASIC:', exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
