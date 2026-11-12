"""Compare the isolated MODFLOW table with the explicit historical v07 export.

Additive to v03: does not alter producers, controller, configuration or caches.
This compares the 16-flux table only, not the DRN audit or physical closure.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import re
import sys
import compare_v03 as original
import pipeline_v03 as p

STEP = 'modflow_original'
FILENAME = 'MF_SVAT_BRUTO_16_1991_2020.csv'
REPORT = 'COMPARE_MODFLOW_REFERENCE_V03.json'
REFERENCE_FOLDER = 'frank_export_modflow_bruto_v07'


def read_object(path):
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object: ' + str(path))
    return value


def contained(path, root):
    if not p.inside(path, root):
        raise ValueError('Path escapes its designated directory: ' + str(path))
    return path


def check_reference(ctx):
    """Read-only prerequisite check; never calls a producer or recalculates MSW."""
    report_path = contained(ctx['output'] / 'COMPARE_MSW_REFERENCE_V03.json', ctx['output'])
    msw = read_object(report_path)
    if (msw.get('status') != 'FIRST_STAGE_VALUES_EQUAL'
            or msw.get('production_enabled') is not False
            or msw.get('source_binding_sha256') != ctx['binding_sha']):
        raise ValueError('Missing valid first-stage comparison for this source binding')
    files = msw.get('files', {})
    if set(files) != set(p.ARTIFACTS['msw_basic']):
        raise ValueError('First-stage comparison must contain both MetaSWAP tables')
    for item in files.values():
        sha = item.get('reference_sha256', '')
        if (item.get('equal_values') is not True or item.get('byte_identical') is not True
                or item.get('rows') != ctx['config']['expected_svats']
                or item.get('changed_cells_by_column') != {}
                or not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha)
                or sha != item.get('candidate_sha256')):
            raise ValueError('First-stage comparison is not the accepted byte-identical result')
    reference = contained(ctx['source'] / REFERENCE_FOLDER / FILENAME, ctx['source'])
    if not reference.is_file():
        raise FileNotFoundError('Historical MODFLOW reference missing at explicit path: ' + str(reference))
    with reference.open(newline='', encoding='utf-8-sig') as stream:
        fields = next(csv.reader(stream), [])
    if len(fields) != len(set(fields)) or not set(p.REQUIRED[STEP]) <= set(fields):
        raise ValueError('Historical MODFLOW reference lacks required or unique columns')
    return reference, report_path


def compare_stage(ctx):
    """Keep one output lock through receipt validation, comparison and publication."""
    with p.output_lock(ctx['output']):
        reference, msw_report = check_reference(ctx)
        directory = contained(ctx['output'] / 'results' / STEP, ctx['output'])
        candidate = contained(directory / FILENAME, directory)
        receipt_path = contained(directory / 'RECEIPT_V03.json', directory)
        inputs_path = contained(directory / 'INPUTS_V03.json', directory)
        watched = [reference, candidate, receipt_path, inputs_path, msw_report]
        before = {str(path): p.file_record(path) for path in watched}
        receipt, inputs = read_object(receipt_path), read_object(inputs_path)
        if (receipt.get('status') != 'COMPUTED_STRUCTURAL_QA_ONLY'
                or receipt.get('production_enabled') is not False
                or p.object_sha(inputs) != receipt.get('identity_sha256')):
            raise ValueError('Candidate lacks a consistent completed-stage receipt')
        expected = {'step': STEP, 'binding_sha256': ctx['binding_sha'],
                    'config_sha256': ctx['config_sha'], 'controller_sha256': ctx['controller_sha'],
                    'code_sha256': ctx['code_sha']}
        if any(inputs.get(k) != v for k, v in expected.items()):
            raise ValueError('Candidate receipt belongs to different code/config/binding/step')
        output = receipt.get('outputs', {}).get(FILENAME, {})
        if (output.get('sha256') != before[str(candidate)]['sha256']
                or output.get('bytes') != before[str(candidate)]['bytes']
                or output.get('rows') != ctx['config']['expected_svats']):
            raise ValueError('Candidate changed since its completed diagnostic run')
        compared = original.compare(reference, candidate, ctx['config']['expected_svats'])
        after = {str(path): p.file_record(path) for path in watched}
        if before != after:
            raise ValueError('A compared table or receipt changed during comparison')
        result = {
            'status': 'MODFLOW_STAGE_VALUES_EQUAL' if compared['equal_values'] else 'MODFLOW_STAGE_DIFFERENCES_FOUND',
            'created_at_utc': p.dt.datetime.now(p.dt.timezone.utc).isoformat(),
            'production_enabled': False, 'source_binding_sha256': ctx['binding_sha'],
            'period': ctx['config']['period'], 'step': STEP,
            'files': {FILENAME: compared},
            'reference_path': str(reference), 'candidate_path': str(candidate),
            'receipt_sha256': before[str(receipt_path)]['sha256'],
            'inputs_sha256': before[str(inputs_path)]['sha256'],
            'preceding_msw_report_sha256': before[str(msw_report)]['sha256'],
            'comparison_code_sha256': p.sha(Path(__file__)),
            'csv_comparator_sha256': p.sha(Path(original.__file__)),
            'raw_idf_fingerprint_mode': inputs.get('raw_idf_fingerprint_mode'),
            'scope': 'MODFLOW 16-flux table equivalence only; no whole-chain acceptance',
            'historical_final_reference_checked': False,
            'drn_audit_compared': False,
            'not_established': ['DRN anomaly audit equivalence', 'Full physical water-balance closure',
                                'Other seven producer comparisons', 'Full raw-source content identity'],
        }
        p.atomic_json(ctx['output'] / REPORT, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check-reference', 'compare'))
    parser.add_argument('--config', type=Path, default=p.CONFIG)
    args = parser.parse_args(argv)
    ctx = p.load_context(args.config)
    if args.action == 'check-reference':
        reference, _ = check_reference(ctx)
        print('MODFLOW_REFERENCE_PRESENT:', reference)
        return 0
    report = compare_stage(ctx)
    print(report['status'], ctx['output'] / REPORT)
    return 0 if report['files'][FILENAME]['equal_values'] else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('STOP MODFLOW COMPARISON:', str(exc), file=sys.stderr)
        sys.exit(2)
