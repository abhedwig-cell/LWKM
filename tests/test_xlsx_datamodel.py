from pathlib import Path
import sqlite3
import zipfile
import unittest

from tools.xlsx_datamodel import materialize_workbook


def workbook(path, body):
    parts = {
        '[Content_Types].xml': '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        '_rels/.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Runs" sheetId="1" r:id="rId1"/></sheets></workbook>',
        'xl/_rels/workbook.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        'xl/worksheets/sheet1.xml': '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + body + '</sheetData></worksheet>',
    }
    with zipfile.ZipFile(path, 'w') as archive:
        for name, text in parts.items():
            archive.writestr(name, text)


HEADER = '<row r="1"><c r="A1" t="inlineStr"><is><t>run_id</t></is></c><c r="B1" t="inlineStr"><is><t>value</t></is></c></row>'


def test_typed_values_dates_null_and_cache(tmp_path):
    source = tmp_path / 'source.xlsx'
    workbook(source, HEADER + '<row r="2"><c r="A2"><v>1</v></c><c r="B2"><f>1.25*2</f><v>2.5</v></c></row><row r="3"><c r="A3"><v>2</v></c></row><row r="4"><c r="A4"><v>3</v></c><c r="B4" t="d"><v>2021-12-31T00:00:00</v></c></row>')
    destination = tmp_path / 'execution.sqlite'
    report = materialize_workbook(source, destination)
    with sqlite3.connect(destination) as con:
        assert con.execute('select * from Runs').fetchall() == [(1, 2.5), (2, None), (3, '2021-12-31')]
    assert report['cached_formula_cells'] == 1


INVALID_CELLS = [
    ('<c r="B2"><f>1+1</f></c>', 'Missing formula cache'),
    ('<c r="B2" t="e"><v>#REF!</v></c>', 'Excel error'),
    ('<c r="C2"><v>99</v></c>', 'Unnamed populated column'),
]

def test_rejects_incomplete_or_invalid_workbook(tmp_path, cell, reason):
    source = tmp_path / 'source.xlsx'
    workbook(source, HEADER + '<row r="2"><c r="A2"><v>1</v></c>' + cell + '</row>')
    destination = tmp_path / 'execution.sqlite'
    with unittest.TestCase().assertRaisesRegex(ValueError, reason):
        materialize_workbook(source, destination)
    assert not destination.exists()


class IngestionTests(unittest.TestCase):
    def test_types_and_cached_formulas(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            test_typed_values_dates_null_and_cache(Path(directory))

    def test_fail_closed(self):
        import tempfile
        for cell, reason in INVALID_CELLS:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                test_rejects_incomplete_or_invalid_workbook(Path(directory), cell, reason)
