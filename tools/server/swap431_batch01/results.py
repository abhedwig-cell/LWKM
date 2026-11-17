"""Strict native SWAP431 daily CSV checks and bounded period summaries.

Native names/units retained. Initial-state row is checked, not summed.
No reconstructed water balance, GxG or invented scientific tolerance.
See OUTPUT_CONTRACT.md for the inspected source basis and limits.
"""
from __future__ import annotations
import csv
from datetime import date, timedelta
import math
from pathlib import Path
import re
from common import file_sha, atomic_json

COLUMNS = 'DATE RAIN IRRIG RUNOFF EIC EPD EPOT EACT TPOT TACT TREDDRY TREDWET DRN SSDI BOT GWL PD_VOL IC_VOL WTOT DSTOR BALDEV'.split()
FLUX = 'RAIN IRRIG RUNOFF EIC EPD EPOT EACT TPOT TACT TREDDRY TREDWET DRN SSDI BOT'.split()
STATES = 'GWL PD_VOL IC_VOL WTOT'.split()
# DSTOR is the signed storage change over the output interval, not storage.
SUMS = FLUX + ['DSTOR']


def update(bucket, values):
    bucket['n'] += 1
    for k, v in values.items():
        s = bucket['values'].setdefault(k, dict(total=0.,compensation=0.,minimum=v,maximum=v,last=v,squares=0.,abs_total=0.))
        # Kahan sum: keep long-period diagnostics stable without changing raw data.
        y = v-s['compensation']; t = s['total']+y
        s['compensation'] = (t-s['total'])-y; s['total'] = t
        s['minimum'] = min(s['minimum'],v); s['maximum'] = max(s['maximum'],v)
        s['last'] = v; s['squares'] += v*v; s['abs_total'] += abs(v)


def finish(bucket):
    n = bucket['n']; out = {'days':n}
    for k in SUMS:
        out[k+'_sum_cm'] = bucket['values'][k]['total']
    for k in STATES:
        s = bucket['values'][k]
        out.update({k+'_mean_cm':s['total']/n,k+'_min_cm':s['minimum'],
                    k+'_max_cm':s['maximum'],k+'_last_cm':s['last']})
    s = bucket['values']['BALDEV']
    out.update(BALDEV_sum_cm=s['total'],BALDEV_abs_sum_cm=s['abs_total'],
        BALDEV_max_abs_cm=max(abs(s['minimum']),abs(s['maximum'])),
        BALDEV_rms_cm=math.sqrt(s['squares']/n))
    return out


def write_table(path, rows):
    path = Path(path)
    with path.open('w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def inspect_csv(path, start, end, summary_dir=None):
    path = Path(path); start = date.fromisoformat(str(start)); end = date.fromisoformat(str(end))
    if not path.is_file() or path.stat().st_size == 0 or end < start:
        raise ValueError('MISSING_RESULT_OR_INVALID_PERIOD')
    first = start-timedelta(days=1); expected = first; rows=0; numeric=0
    units = None; version = False; annual = {}; decadal = {}; all_days={'n':0,'values':{}}
    before = file_sha(path)
    with path.open(encoding='utf-8-sig', newline='') as f:
        def data_lines():
            nonlocal units,version
            for line in f:
                s=line.strip()
                if not s: continue
                if s.startswith(('*','!')):
                    if 'Model version:' in s and re.search(r'\bSwap\s+4\.3\.1\b',s,re.I): version=True
                    if s.lstrip('*! ').startswith('(yyyy-mm-dd)'):
                        units=[x.strip() for x in s.lstrip('*! ').split(',')]
                    continue
                yield line
        reader=csv.reader(data_lines()); header=next(reader,None)
        if header is None or [x.strip().upper() for x in header] != COLUMNS:
            raise ValueError('CSV_HEADER_NOT_BOUND_SERVER06_CONTRACT')
        if not version or units != ['(yyyy-mm-dd)']+['(cm)']*(len(COLUMNS)-1):
            raise ValueError('CSV_VERSION_OR_NATIVE_UNITS_NOT_CONFIRMED')
        for row in reader:
            if len(row)!=len(COLUMNS): raise ValueError('CSV_COLUMN_COUNT')
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',row[0].strip()): raise ValueError('CSV_INVALID_DATE')
            actual=date.fromisoformat(row[0].strip())
            if actual!=expected or actual>end: raise ValueError('CSV_DATE_GAP_DUPLICATE_OR_EXTRA: expected %s got %s'%(expected,actual))
            try: values={k:float(raw.strip().replace('D','E').replace('d','e')) for k,raw in zip(COLUMNS[1:],row[1:])}
            except ValueError as exc: raise ValueError('CSV_NONNUMERIC') from exc
            if not all(math.isfinite(x) for x in values.values()): raise ValueError('CSV_NONFINITE')
            numeric+=len(values);rows+=1; expected+=timedelta(days=1)
            if actual<start: continue
            yy=actual.year; dd=(actual.year,actual.month,1 if actual.day<=10 else 2 if actual.day<=20 else 3)
            for bucket in (annual.setdefault(yy,{'n':0,'values':{}}),
                           decadal.setdefault(dd,{'n':0,'values':{}}),all_days): update(bucket,values)
    if expected-timedelta(days=1)!=end or all_days['n']!=(end-start).days+1:
        raise ValueError('CSV_DID_NOT_REACH_REQUIRED_END')
    if file_sha(path)!=before: raise ValueError('OUTPUT_CHANGED_DURING_CHECK')
    summary=dict(rows=rows,numeric_values_checked=numeric,first_date=str(first),last_date=str(end),
        simulation_start=str(start),simulation_end=str(end),sha256=before,bytes=path.stat().st_size,
        native_units='cm',columns=COLUMNS,initial_row_excluded_from_aggregates=True,
        scientific_balance_tolerance=None,scientific_admission=False,
        comparison_period=None,spinup_exclusion_applied=False,statistics=finish(all_days))
    if summary_dir is not None:
        dest=Path(summary_dir);dest.mkdir(parents=True,exist_ok=True)
        write_table(dest/'YEAR.csv',[dict(year=k,**finish(v)) for k,v in sorted(annual.items())])
        write_table(dest/'DECADE.csv',[dict(year=k[0],month=k[1],decade=k[2],**finish(v)) for k,v in sorted(decadal.items())])
        atomic_json(dest/'NUMERICAL_SUMMARY.json',summary)
    return summary


def inspect_logs(work):
    work=Path(work); normal=False; fatal=0; warnings=0; examples=[]; hashes={}
    for name in ('runtime.log','swap.log','swap.err'):
        p=work/name
        if not p.is_file(): continue
        hashes[name]=file_sha(p)
        with p.open(encoding='utf-8',errors='replace') as f:
            for line in f:
                if name=='runtime.log' and 'Swap normal completion!' in line: normal=True
                s=line.strip()
                if re.search(r'Fatal execution error|^ERROR\s+in\b|forrtl:\s*severe',s,re.I):
                    fatal+=1
                    if len(examples)<12:examples.append(name+': '+s[:400])
                if re.search(r'\bwarning\b',s,re.I): warnings+=1
    return dict(normal_completion=normal,fatal_messages=fatal,warning_lines=warnings,
                fatal_examples=examples,log_sha256=hashes)
