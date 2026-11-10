"""Compare first-stage diagnostic outputs with historical Frank CSVs, read-only.

Rows must have the same order and unique IDs. Blank is not zero. Decimal values
compare exactly, without rounding tolerance. A match is table equivalence, not
full source provenance or qualification of the nine-stage chain.
"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal, InvalidOperation
from itertools import zip_longest
import json
from pathlib import Path
import sys
import pipeline_v03 as p


def compare(reference, candidate, expected):
    changed = {}; examples = []; count = 0; seen = set()
    with reference.open(newline='', encoding='utf-8-sig') as a, candidate.open(newline='', encoding='utf-8-sig') as b:
        ra, rb = csv.DictReader(a), csv.DictReader(b)
        fields = ra.fieldnames
        if not fields or fields != rb.fieldnames or len(fields) != len(set(fields)):
            raise ValueError('CSV headers differ or are duplicated')
        key = 'SVAT/HRU' if 'SVAT/HRU' in fields else 'SVAT'
        for left, right in zip_longest(ra, rb):
            if left is None or right is None:
                raise ValueError('CSV row counts differ')
            if None in left or None in right or any(x is None for x in [*left.values(), *right.values()]):
                raise ValueError('Malformed CSV row')
            ident = int(left[key])
            if int(right[key]) != ident or ident in seen:
                raise ValueError('CSV order/ID differs or a duplicate ID is present')
            seen.add(ident); count += 1
            for col in fields:
                x, y = left[col], right[col]
                if x == y:
                    continue
                equal = False
                if x != '' and y != '':
                    try:
                        xx, yy = Decimal(x), Decimal(y)
                        equal = xx.is_finite() and yy.is_finite() and xx == yy
                    except InvalidOperation:
                        pass
                if not equal:
                    changed[col] = changed.get(col, 0) + 1
                    if len(examples) < 20:
                        examples.append({'SVAT': ident, 'column': col, 'reference': x, 'candidate': y})
    if count != expected:
        raise ValueError('Expected %d rows, found %d' % (expected, count))
    return {'rows': count, 'equal_values': not changed, 'changed_cells_by_column': changed,
            'examples': examples, 'reference_sha256': p.sha(reference), 'candidate_sha256': p.sha(candidate),
            'byte_identical': p.sha(reference) == p.sha(candidate)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, default=p.CONFIG)
    args = ap.parse_args(argv)
    ctx = p.load_context(args.config)
    candidate_dir = ctx['output'] / 'results/msw_basic'
    if not p.inside(candidate_dir, ctx['output']):
        raise ValueError('Candidate path escapes the isolated output root')
    receipt = json.loads((candidate_dir / 'RECEIPT_V03.json').read_text(encoding='utf-8'))
    results = {}
    # Existing historical tables are read, never adopted as new-stage inputs.
    for name in p.ARTIFACTS['msw_basic']:
        ref = ctx['source'] / 'frank_export' / name
        candidate = candidate_dir / name
        if p.sha(candidate) != receipt['outputs'][name]['sha256']:
            raise ValueError('Candidate changed since its completed diagnostic run')
        results[name] = compare(ref, candidate, ctx['config']['expected_svats'])
    equal = all(x['equal_values'] for x in results.values())
    report = {'status': 'FIRST_STAGE_VALUES_EQUAL' if equal else 'FIRST_STAGE_DIFFERENCES_FOUND',
              'production_enabled': False, 'source_binding_sha256': ctx['binding_sha'], 'files': results,
              'scope': 'First MetaSWAP producer only, not whole-chain acceptance',
              'historical_final_reference_expected_sha256': p.REFERENCE_SHA,
              'historical_final_reference_checked': False,
              'not_established': 'Full raw-source provenance, full physical closure, other eight producers'}
    with p.output_lock(ctx['output']):
        dest = ctx['output'] / 'COMPARE_MSW_REFERENCE_V03.json'
        p.atomic_json(dest, report)
    print(report['status'], dest)
    return 0 if equal else 2


if __name__ == '__main__':
    try: sys.exit(main())
    except Exception as exc:
        print('STOP COMPARISON:', str(exc), file=sys.stderr); sys.exit(2)
