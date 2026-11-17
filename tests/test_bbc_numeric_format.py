"""Final BBC formatting tests; no scientific SWAP model is executed."""
import contextlib
import importlib.util
import io
import json
import math
from pathlib import Path
import random
import re
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('bbc_format_subject', ROOT/'tools/server/bbc_production.py')
bbc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bbc)


def digits(token):
    """RDDECD SIGDIG rule: ignore leading zeroes, stop before exponent."""
    mantissa = re.split('[EeDd]', token)[0]
    return len(''.join(c for c in mantissa if c.isdigit()).lstrip('0'))


def fixture(directory):
    import numpy as np
    directory.mkdir(parents=True, exist_ok=True)
    members = directory/'members.csv'
    members.write_text('svat_id,hru_id,x,y\n1,1,125,125\n2,9,375,125\n')
    sources = {}
    for j, role in enumerate(bbc.ROLES):
        sources[role] = dict(pattern=str(directory/(role+'_{date}.idf')),
                             spatial_operation='CELL_NET', positive_multiplier=1)
        for d in range(1, 4):
            values = np.array([-(d+j)*2.1234567, (d+j)*3.7654321], dtype='<f4')
            header = struct.pack('<3i7f4B2f',1271,2,1,0,500,0,250,
                                 float(values.min()),float(values.max()),-9999,0,0,0,0,250,250)
            (directory/(role+f'_1970010{d}.idf')).write_bytes(header+values.tobytes())
    cfg = dict(start='1970-01-01',end='1970-01-03',members=str(members),expected_hrus=2,
               units='m3/calendar_day',positive='into_layer1',sources=sources)
    path = directory/'config.json';path.write_text(json.dumps(cfg))
    return path


class NumericFormat(unittest.TestCase):
    def test_reported_value(self):
        self.assertEqual(bbc.format_bbc_real(-0.026986001601585975), '-0.026986001601586')

    def test_real_even_for_integer(self):
        for value in [-100.0,-1.0,0.0,1.0,100.0]:
            token=bbc.format_bbc_real(value)
            self.assertTrue('.' in token or 'e' in token.lower())
            self.assertEqual(float(token),value)

    def test_signed_zero_preserved(self):
        self.assertEqual(bbc.format_bbc_real(-0.0),'-0.')
        self.assertEqual(math.copysign(1,float(bbc.format_bbc_real(-0.0))),-1)

    def test_small_nonzero_not_clipped(self):
        for x in [1e-20, -1e-20, 9.876543210123456e-30]:
            text=bbc.format_bbc_real(x)
            self.assertNotEqual(float(text),0)
            self.assertLessEqual(digits(text),15)
            self.assertLessEqual(abs(float(text)-x),6e-15*abs(x))

    def test_fifteen_digit_boundary(self):
        for x in [0.0123456789012345,0.012345678901234567,99.99999999999999]:
            self.assertLessEqual(digits(bbc.format_bbc_real(x)),15)

    def test_nonfinite_refused(self):
        for x in [float('nan'),float('inf'),float('-inf')]:
            with self.assertRaisesRegex(ValueError,'nonfinite'):
                bbc.format_bbc_real(x)

    def test_ten_thousand_numbers(self):
        rng=random.Random(20261117)
        for _ in range(10000):
            x=rng.uniform(-1,1)*10**rng.uniform(-30,2)
            text=bbc.format_bbc_real(x)
            self.assertLessEqual(digits(text),15)
            self.assertLessEqual(abs(float(text)-x),6e-15*abs(x))
            self.assertEqual(math.copysign(1,float(text)),math.copysign(1,x))

    def test_original_ten_day_fixture(self):
        from decimal import Decimal
        lines=(ROOT/'tests/fixtures/bbc_precision/hru1_first10.bbc').read_text().splitlines()
        records=[x.split() for x in lines if re.match(r'^\d{4}-\d{2}-\d{2} ',x)]
        self.assertEqual(len(records),10)
        self.assertTrue(any(digits(x[1])>15 for x in records))
        for day, token in records:
            out=bbc.format_bbc_real(float(token))
            self.assertLessEqual(digits(out),15)
            self.assertLessEqual(abs(Decimal(out)-Decimal(token)),Decimal('5e-17'))


class ProducerIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.config=fixture(self.base/'sources')
        self.out=self.base/'new-output'

    def run_producer(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return bbc.process(self.config,self.out)

    def test_written_bbc_and_transfer_precision_separate(self):
        report=self.run_producer()
        self.assertEqual(report['producer_version'],'BBC09_FORMAT15')
        self.assertEqual(report['bbc_float_format'],'.15g')
        self.assertEqual(report['hrus'],2)
        for path in (self.out/'bbc').glob('*.bbc'):
            records=[x.split() for x in path.read_text().splitlines() if re.match(r'^\d{4}-',x)]
            self.assertEqual(len(records),3)
            for _,token in records:self.assertLessEqual(digits(token),15)
        # The full-precision interchange stream is not normalized for TTUTIL.
        import csv
        with (self.out/'transfer/1970-01-01.csv').open(newline='') as f:
            records=list(csv.DictReader(f))
        self.assertTrue(any(digits(r['q_ext_mm_d'])>15 for r in records))

    def test_resume_same_code_reuses_bbc(self):
        self.run_producer();report=self.run_producer()
        self.assertTrue(report['bbc_reused'])
        self.assertEqual(report['reused_days'],3)

    def test_old_identity_not_accepted(self):
        self.run_producer();identity=self.out/'identity.json'
        old=json.loads(identity.read_text());old['code_sha256']='0'*64
        identity.write_text(json.dumps(old))
        with self.assertRaisesRegex(ValueError,'choose a new output directory'):
            self.run_producer()

    def test_no_source_mutation(self):
        before={p.name:p.read_bytes() for p in self.config.parent.iterdir()}
        self.run_producer()
        after={p.name:p.read_bytes() for p in self.config.parent.iterdir()}
        self.assertEqual(before,after)


if __name__=='__main__':unittest.main()
