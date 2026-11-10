"""Isolated diagnostic replay of the nine immutable Frank producers.

No writes to LHM source/output authority or historical Frank exports. This
controller does not grant production qualification. Raw IDF fingerprints are
explicitly metadata-only unless source_hash_mode='sha256' is configured.
"""
from __future__ import annotations
import argparse
import contextlib
import csv
import datetime as dt
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LEGACY = HERE / 'legacy'
DATA = HERE / 'data'
CONFIG = REPO / 'config/production/frank_pipeline_v03.json'
REGISTER = REPO / 'config/production/frank_original_producers_sha256_v01.json'
PRODUCERS = {
    'msw_basic': 'build_svat_base.py', 'modflow_original': 'build_modflow_svat.py',
    'gxg': 'build_gxg_gg.py', 'gw_percentielen': 'bereken_gw_percentielen.py',
    'et_componenten': 'export_msw_aanvulling.py', 'statisch_gt': 'derive_static_gt.py',
    'gebied_n': 'maak_gebied_n.py', 'qmodf': 'export_qmodf.py',
    'svat_basis': 'maak_svat_basis.py',
}
DEPENDENCIES = {
    'msw_basic': (), 'modflow_original': (), 'gxg': (), 'gw_percentielen': ('gxg',),
    'et_componenten': ('msw_basic',), 'statisch_gt': ('gxg',),
    'gebied_n': ('gw_percentielen',), 'qmodf': ('msw_basic',),
    'svat_basis': ('msw_basic', 'modflow_original', 'gw_percentielen',
                   'et_componenten', 'statisch_gt', 'gebied_n', 'qmodf'),
}
ARTIFACTS = {
    'msw_basic': ('FRANK_LHM_SVAT_BASE_1991_2020.csv', 'MSW_SOURCE_SIGNED_1991_2020.csv'),
    'modflow_original': ('MF_SVAT_BRUTO_16_1991_2020.csv',),
    'gxg': ('FRANK_LHM_SVAT_GXG_GG_1991_2020.csv',),
    'gw_percentielen': ('FRANK_LHM_SVAT_GXG_GG_GW5_GW95_1991_2020.csv',),
    'et_componenten': ('FRANK_SVAT_MSW_AANVULLING_1991_2020.csv',),
    'statisch_gt': ('FRANK_SVAT_STATISCH_GT_1991_2020.csv',),
    'gebied_n': ('FRANK_SVAT_GEBIED_N_1991_2020.csv',),
    'qmodf': ('FRANK_SVAT_QMODF_1991_2020.csv',),
    'svat_basis': ('FRANK_SVAT_BASIS_ONGECORRIGEERD_1991_2020.csv',
                   'FRANK_SVAT_BASIS_CONTROLE_1991_2020.csv'),
}
REQUIRED = {
    'msw_basic': ('SVAT', 'Opp_svat'),
    'modflow_original': ('SVAT', 'FLF_KWEL_m3', 'RIV_SYS1_ONTWATERING_m3'),
    'gxg': ('SVAT', 'GHG_cm_mv', 'GLG_cm_mv'),
    'gw_percentielen': ('SVAT', 'GW5', 'GW95'),
    'et_componenten': ('SVAT', 'Verdamping_gewas_mm_j', 'Beregening_mm_j'),
    'statisch_gt': ('SVAT', 'LU2', 'bodem370', 'Gtnr'),
    'gebied_n': ('SVAT', 'Gebied', 'N'),
    'qmodf': ('SVAT', 'QModF_signed_mm_j'),
    'svat_basis': ('SVAT/HRU', 'Gebied', 'N', 'GG', 'Fldrou1', 'Fldrin1'),
}
READERS = ('wb10_reader.py', 'wb01.py', 'wb03_balance.py')
ASSETS = {
    'landuse-mapping-realized-v1.csv': '1bba71f0c7fd8de959671815830784788a04230ea34001e574243f533158c1d0',
    'bodem370_classification_lookup.csv': '5f5a4923a72e1e46b24a3fd5798222d4d0e25b5c4b32c69833d18672e47b3ce6',
    'ECHO_toestroom_geclusterd_66gebiedenx.asc': 'e22933baa8df86551c9aa390433aa01359b7bd1fddf4ce9eb714f7c5c75532f3',
}
REFERENCE_SHA = '7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df'
SOURCE_DECISION = 'LWKM-LHM-SOURCE-20261110-01'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def object_sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True).encode('utf-8')).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.json_', suffix='.partial', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def inside(path, parent):
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def selection(target):
    if target == 'all':
        return list(PRODUCERS)
    result = []
    def visit(step):
        for dependency in DEPENDENCIES[step]:
            visit(dependency)
        if step not in result:
            result.append(step)
    visit(target)
    return result


def verify_code():
    register = json.loads(REGISTER.read_text(encoding='utf-8'))['files']
    expected = set(PRODUCERS.values()) | set(READERS)
    if set(register) != expected:
        raise ValueError('Original source register must contain exactly 12 files')
    for name, expected_sha in register.items():
        if sha(LEGACY / name) != expected_sha:
            raise ValueError('Original source changed: ' + name)
    return register


def load_context(config_file):
    config_file = Path(config_file).resolve()
    config_bytes = config_file.read_bytes()
    c = json.loads(config_bytes.decode('utf-8-sig'))
    if (c.get('schema_version') != 3 or c.get('period') != [1991, 2020]
            or c.get('expected_svats') != 645582):
        raise ValueError('v03 supports only the original 1991-2020 / 645582-SVAT profile')
    if c.get('production_enabled') is not False:
        raise ValueError('Production qualification may not be enabled by changing configuration')
    if c.get('source_hash_mode') not in ('metadata', 'sha256'):
        raise ValueError('source_hash_mode must explicitly be metadata or sha256')
    binding_file = Path(c['binding_file'])
    if not binding_file.is_absolute():
        binding_file = config_file.parent / binding_file
    binding_bytes = binding_file.read_bytes()
    binding_sha = hashlib.sha256(binding_bytes).hexdigest()
    if binding_sha != c['binding_sha256']:
        raise ValueError('Binding differs from the explicitly accepted server manifest')
    b = json.loads(binding_bytes.decode('utf-8-sig'))
    if (b.get('kind') != 'LWKM_RUN_SOURCE_BINDING' or b.get('source_profile') != 'run_local'
            or b.get('source_executable_authority') != SOURCE_DECISION
            or b.get('static_input_identity') != 'OWNER_ESTABLISHED_IDENTICAL_BETWEEN_RUNS'):
        raise ValueError('Run-source binding does not meet the recorded project decisions')
    source = Path(b['output_authority_root'])
    if not source.is_absolute() or source.name != 'LWKM_run_resultaten_totaal':
        raise ValueError('Authorized LHM output root must be explicit and absolute')
    workspace = source.parent
    run = b['static_reference_run']
    if not re.fullmatch(r'run_\d{4}_\d{4}(?:_[A-Za-z0-9_-]+)?', run):
        raise ValueError('Invalid static reference run')
    metaswap = workspace / run / 'metaswap'
    area = Path(b['static_files']['area_svat.inp']['path'])
    if Path(b['metaswap_input_root']).resolve() != metaswap.resolve() or not inside(area, metaswap):
        raise ValueError('Area source must stay inside the selected run-local metaswap directory')
    out_name = c['output_name']
    if not re.fullmatch(r'Frank_v03_[A-Za-z0-9_]+', out_name):
        raise ValueError('Invalid isolated output name')
    output = workspace / 'LWKM_rebuilds' / out_name
    if not inside(output, workspace / 'LWKM_rebuilds') or not inside(workspace / 'LWKM_rebuilds', workspace):
        raise ValueError('Redirected output directory')
    for protected in (source, metaswap, HERE):
        if inside(output, protected) or inside(protected, output):
            raise ValueError('New output overlaps protected data or software')
    mask = Path(c['ibound_l1'])
    if not mask.is_absolute():
        raise ValueError('MODFLOW mask must be an explicit absolute path')
    code = verify_code()
    return dict(config=c, config_sha=hashlib.sha256(config_bytes).hexdigest(),
                binding_sha=binding_sha, binding=b, binding_file=binding_file,
                source=source, workspace=workspace, metaswap=metaswap, area=area,
                mask=mask, output=output, code_sha=code,
                controller_sha=sha(Path(__file__)))


def module(name):
    if str(LEGACY) not in sys.path:
        sys.path.insert(0, str(LEGACY))
    loaded = importlib.import_module(name)
    if Path(loaded.__file__).resolve() != (LEGACY / (name + '.py')).resolve():
        raise ValueError('Unexpected imported producer path: ' + name)
    return loaded


def artifacts(ctx, step, directory=None):
    directory = directory or ctx['output'] / 'results' / step
    return [directory / name for name in ARTIFACTS[step]]


def command(ctx, step, out):
    area, src, work = ctx['area'], ctx['source'], ctx['workspace']
    msw, heads = src / 'metaswap', src / 'modflow/head'
    dep = lambda s, i=0: artifacts(ctx, s)[i]
    common = {
        'msw_basic': ['--root', msw, '--area', area, '--lhm-workspace', work,
                      '--out', out, '--from-year', 1991, '--to-year', 2020],
        'modflow_original': ['--root', src / 'modflow', '--area', area, '--mask', ctx['mask'],
                             '--out', out, '--from-year', 1991, '--to-year', 2020],
        'gxg': ['--head-dir', heads, '--area', area, '--out', out,
                 '--first-year', 1991, '--last-year', 2020, '--expected-svats', 645582],
        'gw_percentielen': ['--gxg', dep('gxg'), '--head-dir', heads, '--out', out],
        'et_componenten': ['--root', msw, '--area', area, '--signed-baseline', dep('msw_basic', 1),
                           '--out', out, '--start', 1991, '--end', 2020, '--check-et', dep('msw_basic')],
        'statisch_gt': ['--area', area, '--heads', dep('gxg'), '--out', out,
                        '--landuse-lookup', DATA / 'landuse-mapping-realized-v1.csv',
                        '--soil-lookup', DATA / 'bodem370_classification_lookup.csv'],
        'gebied_n': ['--gxg', dep('gw_percentielen'), '--grid', DATA / 'ECHO_toestroom_geclusterd_66gebiedenx.asc',
                     '--out', out / ARTIFACTS['gebied_n'][0], '--expect', 645582],
        'qmodf': ['--signed', dep('msw_basic', 1), '--root', msw, '--out', out],
        'svat_basis': ['--metaswap', dep('msw_basic'), '--signed', dep('msw_basic', 1),
                       '--gxg', dep('gw_percentielen'), '--mf', dep('modflow_original'),
                       '--et', dep('et_componenten'), '--static', dep('statisch_gt'),
                       '--gebied', dep('gebied_n'), '--qmodf', dep('qmodf'), '--out', out, '--expected', 645582],
    }
    return [sys.executable, '-B', '-u', str(LEGACY / PRODUCERS[step]), *map(str, common[step])]


def file_record(path, hash_content=True):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    before = path.stat()
    record = dict(path=str(path.resolve()), bytes=before.st_size, mtime_ns=before.st_mtime_ns)
    if hash_content:
        record['sha256'] = sha(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Source changed during fingerprinting: ' + str(path))
    return record


def raw_sources(ctx, step):
    src = ctx['source']
    if step == 'msw_basic':
        m = module('build_svat_base'); index = m.period_index(src / 'metaswap', range(1991, 2021))
        for year in range(1991, 2021):
            yield from m.year_inputs(year, index).values()
    elif step == 'modflow_original':
        m = module('build_modflow_svat')
        for year in range(1991, 2021):
            for stamp in m.all_days(year):
                for role in m.ROLES:
                    yield from m.source_paths(src / 'modflow', role, stamp)
    elif step in ('gxg', 'gw_percentielen'):
        m = module('build_gxg_gg' if step == 'gxg' else 'bereken_gw_percentielen')
        index = m.index_heads(src / 'modflow/head')
        dates = m.required_dates(1991, 2020) if step == 'gxg' else m.dates()
        if step == 'gxg':
            index = index[0]
        for date in dates:
            stamp = date.strftime('%Y%m%d')
            if stamp not in index:
                raise FileNotFoundError('Merged layer-1 head missing: ' + stamp)
            yield index[stamp]
    elif step == 'et_componenten':
        m = module('export_msw_aanvulling'); index = m.index_source(src / 'metaswap', range(1991, 2021))
        for d in module('wb10_reader').decades(1991, 2020):
            for role in m.VARS:
                yield index[role][d['date_end']]
    elif step == 'qmodf':
        index = module('export_qmodf').index(src / 'metaswap')
        for d in module('wb10_reader').decades(1991, 2020):
            yield index[d['date_end']]


def step_assets(step):
    if step == 'statisch_gt':
        return ('landuse-mapping-realized-v1.csv', 'bodem370_classification_lookup.csv')
    if step == 'gebied_n':
        return ('ECHO_toestroom_geclusterd_66gebiedenx.asc',)
    return ()


def snapshot(ctx, step, include_dependencies=True):
    if verify_code() != ctx['code_sha'] or sha(Path(__file__)) != ctx['controller_sha']:
        raise ValueError('Source/controller code changed during this invocation')
    regular = [file_record(ctx['area'])]
    if regular[0]['sha256'] != ctx['binding']['static_files']['area_svat.inp']['sha256']:
        raise ValueError('Run-local area_svat differs from accepted binding')
    if step == 'modflow_original':
        regular.append(file_record(ctx['mask']))
    for name in step_assets(step):
        record = file_record(DATA / name)
        if record['sha256'] != ASSETS[name]:
            raise ValueError('Bundled lookup/grid changed: ' + name)
        regular.append(record)
    optional = None
    if step == 'msw_basic':
        path = ctx['workspace'] / 'LHM_uitvoer/filter/Riv_infiltratie_1991-2020_sum.asc'
        optional = file_record(path) if path.is_file() else {'path': str(path.resolve()), 'present': False}
    deps = {}
    if include_dependencies:
        for dep in DEPENDENCIES[step]:
            receipt = ctx['output'] / 'results' / dep / 'RECEIPT_V03.json'
            deps[dep] = file_record(receipt)
            regular.extend(file_record(p) for p in artifacts(ctx, dep))
    full_sha = ctx['config']['source_hash_mode'] == 'sha256'
    raw = []
    for path in raw_sources(ctx, step):
        if not inside(path, ctx['source']):
            raise ValueError('Raw file escapes the authorized LHM output root: ' + str(path))
        raw.append(file_record(path, full_sha))
    value = dict(schema_version=3, step=step, config_sha256=ctx['config_sha'],
                 binding_sha256=ctx['binding_sha'], controller_sha256=ctx['controller_sha'],
                 code_sha256=ctx['code_sha'], runtime={'python': sys.version, 'numpy': module('wb10_reader').np.__version__},
                 regular_inputs=regular, dependencies=deps,
                 raw_idf_fingerprint_mode=ctx['config']['source_hash_mode'], raw_idfs=raw,
                 optional_historical_infiltration=optional)
    return value


def validate_csv(path, required, expected_ids):
    seen = set()
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not set(required) <= set(fields):
            raise ValueError('Missing or duplicate columns in ' + str(path))
        key = 'SVAT/HRU' if 'SVAT/HRU' in fields else 'SVAT'
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Malformed CSV row: ' + str(path))
            ident = int(row[key])
            if ident in seen or ident not in expected_ids:
                raise ValueError('Duplicate/unexpected SVAT ' + str(ident) + ' in ' + str(path))
            seen.add(ident)
    if seen != expected_ids:
        raise ValueError('Incomplete SVAT population: ' + str(path))
    return {'rows': len(seen), 'sha256': sha(path), 'bytes': path.stat().st_size}


def validate_outputs(ctx, step, directory, expected_ids):
    result = {}
    for i, path in enumerate(artifacts(ctx, step, directory)):
        required = REQUIRED[step] if i == 0 else ('SVAT',)
        result[path.name] = validate_csv(path, required, expected_ids)
    return result


@contextlib.contextmanager
def output_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / 'RUNNING.lock'
    try:
        fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        raise RuntimeError('Output locked. Check active process before manually removing: ' + str(lock))
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump({'pid': os.getpid(), 'time_utc': dt.datetime.now(dt.timezone.utc).isoformat()}, f)
        yield
    finally:
        lock.unlink()


def run_step(ctx, step, ids):
    final = ctx['output'] / 'results' / step
    work = ctx['output'] / 'work' / step
    for path in (final, work):
        if path.is_symlink() or not inside(path, ctx['output']):
            raise ValueError('Stage path escapes the isolated output root')
    before = snapshot(ctx, step)
    identity = object_sha(before)
    if final.exists():
        receipt = json.loads((final / 'RECEIPT_V03.json').read_text(encoding='utf-8'))
        actual = validate_outputs(ctx, step, final, ids)
        if receipt['identity_sha256'] != identity or actual != receipt['outputs']:
            raise ValueError('Existing result/code/config/source mismatch; choose a new output_name')
        print('HERGEBRUIK GEVERIFIEERD', step, flush=True)
        return receipt
    if work.exists():
        previous = json.loads((work / 'INPUTS_V03.json').read_text(encoding='utf-8'))
        if object_sha(previous) != identity:
            raise ValueError('Checkpoint inputs/code/config changed; choose a new output_name')
    else:
        work.mkdir(parents=True)
        atomic_json(work / 'INPUTS_V03.json', before)
    cmd = command(ctx, step, work)
    print('START DIAGNOSTISCHE HERBEREKENING', step, flush=True)
    atomic_json(work / 'COMMAND_V03.json', {'argv': cmd, 'production_enabled': False})
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with (work / 'producer.log').open('a', encoding='utf-8') as log:
        process = subprocess.Popen(cmd, cwd=work, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', env=env)
        try:
            for line in process.stdout:
                print(line, end='', flush=True); log.write(line); log.flush()
            rc = process.wait()
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()
            raise
        finally:
            process.stdout.close()
    if rc:
        raise RuntimeError('Producer failed (' + str(rc) + '); work and log preserved: ' + str(work))
    after = snapshot(ctx, step)
    if object_sha(after) != identity:
        raise ValueError('Source changed during calculation; no result published')
    outputs = validate_outputs(ctx, step, work, ids)
    receipt = dict(status='COMPUTED_STRUCTURAL_QA_ONLY', production_enabled=False,
                   identity_sha256=identity, outputs=outputs,
                   time_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   raw_idf_fingerprint_mode=ctx['config']['source_hash_mode'],
                   scientific_acceptance='PENDING_REAL_REFERENCE_COMPARISON')
    atomic_json(work / 'RECEIPT_V03.json', receipt)
    final.parent.mkdir(parents=True, exist_ok=True)
    work.rename(final)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'check', 'diagnostic-run'))
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--through', choices=(*PRODUCERS, 'all'), default='msw_basic')
    args = parser.parse_args(argv)
    ctx = load_context(args.config)
    selected = selection(args.through)
    print('Period 1991-2020. Run-local input:', ctx['area'])
    print('Isolated output:', ctx['output'])
    print('Raw IDF fingerprint:', ctx['config']['source_hash_mode'], '; production_enabled=false')
    if args.action == 'plan':
        for step in selected:
            print(step, ' '.join(command(ctx, step, ctx['output'] / 'work' / step)))
        return 0
    ids = set(map(int, module('wb10_reader').read_area(ctx['area'])[0]))
    if args.action == 'check':
        summaries = []
        for step in selected:
            snap = snapshot(ctx, step, include_dependencies=False)
            summaries.append({'step': step, 'raw_idfs': len(snap['raw_idfs']),
                              'raw_sources_identity_sha256': object_sha(snap),
                              'upstream_results_checked': False})
            print('BRONCHECK OK', step, 'SVATs', len(ids), 'IDFs', len(snap['raw_idfs']))
        with output_lock(ctx['output']):
            atomic_json(ctx['output'] / 'PREFLIGHT_V03.json',
                        {'status': 'SOURCE_PREFLIGHT_ONLY', 'production_enabled': False, 'steps': summaries})
        return 0
    with output_lock(ctx['output']):
        state = dict(status='RUNNING_DIAGNOSTIC', production_enabled=False, steps={})
        try:
            for step in selected:
                state['steps'][step] = run_step(ctx, step, ids)
                atomic_json(ctx['output'] / 'STATUS_V03.json', state)
            state['status'] = 'DIAGNOSTIC_FINISHED_NOT_PRODUCTION_QUALIFIED'
        except BaseException as exc:
            state.update(status='STOPPED', error=str(exc))
            raise
        finally:
            atomic_json(ctx['output'] / 'STATUS_V03.json', state)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('STOP FRANK V03:', str(exc), file=sys.stderr)
        sys.exit(2)
