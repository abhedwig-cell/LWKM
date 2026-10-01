"""Lossless typed workbook ingestion for the existing SQLite join engine.

SQLite is a temporary execution format, not an independent authority.
Cached formula values are used only when present; empty formula caches fail.
Blank header columns are permitted only when every data cell is blank.
Dates are ISO strings, numbers keep their native numeric type, blanks are NULL.
"""
from datetime import date, datetime
import hashlib
from pathlib import Path
import sqlite3
import openpyxl


def _identifier(value):
    return '"' + value.replace('"', '""') + '"'


def materialize_workbook(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    formulas = openpyxl.load_workbook(source, read_only=True, data_only=False)
    values = openpyxl.load_workbook(source, read_only=True, data_only=True)
    report = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "sheets": {}, "cached_formula_cells": 0}
    con = sqlite3.connect(destination)
    try:
        for sheet in values:
            raw = list(sheet.iter_rows(values_only=True))
            width = max(len(row) for row in raw)
            raw = [row + (None,) * (width - len(row)) for row in raw]
            headers = raw[0]
            active = [i for i, h in enumerate(headers) if h is not None]
            names = [headers[i] for i in active]
            if any(not isinstance(h, str) or not h for h in names):
                raise ValueError(f"Invalid headers in {sheet.title}")
            if len({h.lower() for h in names}) != len(names):
                raise ValueError(f"Duplicate headers in {sheet.title}")
            rows = []
            for n, (row, frow) in enumerate(zip(raw[1:], formulas[sheet.title].iter_rows(min_row=2)), 2):
                for i, cell in enumerate(frow):
                    if i not in active and row[i] is not None:
                        raise ValueError(f"Unnamed populated column {sheet.title}:{cell.coordinate}")
                    if cell.data_type == 'e':
                        raise ValueError(f"Excel error {sheet.title}:{cell.coordinate}")
                    if cell.data_type == 'f':
                        report['cached_formula_cells'] += 1
                        if row[i] is None:
                            raise ValueError(f"Missing formula cache {sheet.title}:{cell.coordinate}")
                if all(v is None for v in row):
                    continue
                record = []
                for i in active:
                    value = row[i]
                    if isinstance(value, datetime):
                        if value.time().isoformat() != '00:00:00':
                            raise ValueError(f"Non-midnight date {sheet.title}:{n}")
                        value = value.date().isoformat()
                    elif isinstance(value, date):
                        value = value.isoformat()
                    record.append(value)
                rows.append(record)
            table = _identifier(sheet.title)
            con.execute(f"CREATE TABLE {table} ({','.join(_identifier(h) for h in names)})")
            con.executemany(f"INSERT INTO {table} VALUES ({','.join('?' for h in names)})", rows)
            reread = con.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            if reread != [tuple(r) for r in rows]:
                raise ValueError(f"Typed roundtrip failure: {sheet.title}")
            report['sheets'][sheet.title] = {"rows": len(rows), "columns": names}
        con.commit()
    except Exception:
        con.close()
        destination.unlink(missing_ok=True)
        raise
    finally:
        con.close()
        formulas.close()
        values.close()
    return report
