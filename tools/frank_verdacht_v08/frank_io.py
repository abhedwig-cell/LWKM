"""Bestandsfuncties uit Frank v07.1; geen database of open bestanden bij publicatie."""
from contextlib import contextmanager
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import uuid


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('w', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(temp), str(path))
    finally:
        if temp.exists():
            temp.unlink()


@contextmanager
def read_csv(path, required=None, exact=None):
    path = Path(path)
    opener = gzip.open if path.suffix.lower() == '.gz' else open
    with opener(str(path), 'rt', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=',')
        names = reader.fieldnames or []
        if len(names) != len(set(names)):
            raise ValueError('Dubbele kolomnaam: ' + str(path))
        if exact is not None and names != list(exact):
            raise ValueError('Onjuist CSV-schema of scheidingsteken: ' + str(path) +
                             '. Verwacht de 49 v06-kolommen en een komma als scheidingsteken.')
        missing = set(required or []) - set(names)
        if missing:
            raise ValueError('Ontbrekende kolommen in ' + str(path) + ': ' + ', '.join(sorted(missing)))
        yield reader


def check_row(row, label):
    if None in row or any(v is None for v in row.values()):
        raise ValueError('Ongeldig aantal CSV-velden: ' + label)


def number(v, label):
    if v is None or not str(v).strip():
        raise ValueError('Verplichte waarde ontbreekt: ' + label)
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError('Geen getal: ' + label + ': ' + str(v))
    if not math.isfinite(x):
        raise ValueError('Niet-eindig getal: ' + label)
    return x


def integer(v, label):
    s = str(v).strip()
    if not s.isdigit() or int(s) <= 0:
        raise ValueError('Ongeldige positieve integer: ' + label + ': ' + s)
    return int(s)


def nstr(value):
    return format(float(value), '.12g')


def assert_close(a, b, label, rel=2e-7, absolute=5e-5):
    if not math.isclose(float(a), float(b), rel_tol=rel, abs_tol=absolute):
        raise ValueError('{} wijkt af: {} versus {}'.format(label, a, b))


def process_alive(pid):
    if pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = k32.OpenProcess(0x1000, False, pid)
        if handle:
            k32.CloseHandle(handle)
            return True
        return ctypes.get_last_error() == 5  # Access denied means do not break a live lock.
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


@contextmanager
def run_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    info = {'host': socket.gethostname(), 'pid': os.getpid(), 'token': token,
            'started_utc': datetime.now(timezone.utc).isoformat()}
    for attempt in range(2):
        try:
            with path.open('x', encoding='utf-8') as f:
                json.dump(info, f)
            break
        except FileExistsError:
            try:
                old = json.loads(path.read_text(encoding='utf-8'))
            except (ValueError, OSError):
                raise RuntimeError('Onleesbaar uitvoeringsslot: ' + str(path))
            if attempt == 0 and old.get('host') == info['host'] and not process_alive(int(old.get('pid', 0))):
                path.unlink()
                continue
            raise RuntimeError('Er draait al een verwerking, of een slot van een andere computer bestaat: ' + str(path))
    try:
        yield
    finally:
        if path.exists():
            current = json.loads(path.read_text(encoding='utf-8'))
            if current.get('token') == token:
                path.unlink()


def source_identity(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError('Bronbestand ontbreekt: ' + str(path))
    return {'path': str(path.resolve()), 'size_bytes': path.stat().st_size, 'sha256': sha(path)}
