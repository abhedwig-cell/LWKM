"""Identity, atomic files and read-only SWP parsing for LWKM BATCH01 (stdlib)."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import uuid
from datetime import date, datetime, timezone

ROOT = Path(__file__).resolve().parent
VERSION = 'LWKM-SWAP431-BATCH01-v01'
PROFILE = 'LWKM_RECEIVED_SERVER06_DRA01_BBC09_MET06_CANDIDATE_V01'
W11_COMMIT = '276fbaf8d0571a3fe7f4c78946835fa0b0aee097'
SUCCESS = 'EXECUTION_PASS_NOT_PRODUCTION_ADMITTED'
MET07_SUCCESS = 'ALL_10242_HUM_CORRECTED_REBOUND_NOT_PRODUCTION_ADMITTED'

class IntegrityError(ValueError):
    """Shared identity or immutable-input failure: stop dispatching."""

class NotReady(ValueError):
    """Upstream correction is not a complete, bound MET07 population."""


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def object_sha(obj):
    # Same encoding as national_hum.object_sha.
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def file_sha(p):
    p = Path(p)
    if p.is_symlink() or not p.is_file():
        raise IntegrityError('NOT_REGULAR_FILE: ' + str(p))
    before = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    after = p.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise IntegrityError('FILE_CHANGED_WHILE_READING: ' + str(p))
    return h.hexdigest()


def atomic_json(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name('.' + p.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with tmp.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(str(tmp), str(p))
    finally:
        if tmp.exists():
            tmp.unlink()


def immutable_json(p, value):
    p = Path(p)
    if p.exists():
        if read_json(p) != value:
            raise IntegrityError('IMMUTABLE_BINDING_CHANGED: ' + str(p))
    else:
        atomic_json(p, value)


def within(p, parent):
    try:
        Path(p).resolve().relative_to(Path(parent).resolve()); return True
    except ValueError:
        return False


def distinct_roots(writable, protected):
    for p in writable:
        for q in protected:
            if within(p, q) or within(q, p):
                raise IntegrityError('WRITABLE_ROOT_OVERLAPS_PROTECTED: %s / %s' % (p, q))
        for q in writable:
            if p != q and (within(p, q) or within(q, p)):
                raise IntegrityError('WRITABLE_ROOTS_OVERLAP')
    if len(set(map(lambda p: str(Path(p).resolve()).casefold(), writable))) != len(writable):
        raise IntegrityError('WRITABLE_ROOTS_NOT_DISTINCT')


def basename(value):
    name = str(value).strip()
    if (not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', name) or '..' in name
        or name.endswith('.') or name.split('.')[0].upper() in
        {'CON','PRN','AUX','NUL', *('COM'+str(i) for i in range(1,10)),
         *('LPT'+str(i) for i in range(1,10))}):
        raise IntegrityError('UNSAFE_BASENAME: ' + repr(name))
    return name


def active(line):
    if line.lstrip().startswith(('*','!','#')):
        return ''
    # Remove ! comments, but preserve quoted text.
    return re.split(r"!(?=(?:[^'\"]|'[^']*'|\"[^\"]*\")*$)", line, maxsplit=1)[0].strip()


def assignments(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r'^([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$', active(line))
        if m:
            key, val = m.groups(); out.setdefault(key.upper(), []).append(val.strip().strip("'\""))
    return out


def one(a, key):
    vals = a.get(key, [])
    if len(vals) != 1:
        raise IntegrityError('EXPECTED_ONE_ASSIGNMENT: ' + key)
    return vals[0].strip()


def parse_date(value):
    val = str(value).strip().strip("'\"")
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', val):
        return date.fromisoformat(val)
    m = re.fullmatch(r'(\d{1,2})[-/]([A-Za-z]{3}|\d{1,2})[-/](\d{4})', val)
    if not m:
        raise IntegrityError('INVALID_DATE: ' + val)
    d, mo, y = m.groups()
    months = 'jan feb mar apr may jun jul aug sep oct nov dec'.split()
    return date(int(y), int(mo) if mo.isdigit() else months.index(mo.lower())+1, int(d))


def table(text, prefix, columns):
    """Known Server06 table only; absent/partial table is unknown, never invented."""
    lines = text.splitlines(); starts = []
    for i, line in enumerate(lines):
        if active(line).upper().split()[:len(prefix)] == prefix:
            starts.append(i)
    if len(starts) != 1:
        return None
    rows = []
    for line in lines[starts[0]+1:]:
        s = active(line)
        if 'end of table' in line.lower() or s.lower() in ('end_table','endtable'):
            break
        if not s:
            continue
        if '=' in s:
            break
        row = shlex.split(s)
        if len(row) != columns:
            return None
        rows.append(row)
    return rows or None


class FileLock:
    """OS lock. File may remain after a crash; a stale file alone is not a lock."""
    def __init__(self, path):
        self.path = Path(path); self.f = None
    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink(): raise IntegrityError('SYMLINK_LOCK')
        self.f = self.path.open('a+b')
        try:
            if self.f.seek(0, 2) == 0:
                self.f.write(b'0'); self.f.flush()
            self.f.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError):
            self.f.close(); self.f = None
            raise IntegrityError('LOCK_ALREADY_HELD: ' + str(self.path))
        return self
    def __exit__(self, *exc):
        if self.f is not None:
            try:
                self.f.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(self.f.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
            finally:
                self.f.close(); self.f = None


def code_identity():
    return {p.name: file_sha(p) for p in sorted(ROOT.glob('*.py'))}


def verify_package():
    p = ROOT/'PACKAGE_MANIFEST.json'
    if not p.is_file():
        raise IntegrityError('PACKAGE_MANIFEST_MISSING')
    for name, expected in read_json(p)['files'].items():
        target = ROOT/name
        if not within(target, ROOT) or file_sha(target) != expected:
            raise IntegrityError('PACKAGE_FILE_CHANGED: ' + name)
