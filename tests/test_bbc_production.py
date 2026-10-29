"""Geometry, physical ownership, volume, coverage and restart regressions for BBC08."""
import csv
import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from tools.server.bbc_production import Raster, members, process, discover, days, ROLES, acquire_lock
from tools.production_transfer import receive


def grid(p,a,xmin=0,ymax=750,dx=250):
    a=np.asarray(a,dtype='<f4');ny,nx=a.shape
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(struct.pack('<3i7f4B2f',1271,nx,ny,xmin,xmin+nx*dx,ymax-ny*dx,ymax,
                             float(a.min()),float(a.max()),-9999,0,0,0,0,dx,dx)+a.tobytes())
    return p


class BBCProduction(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
    def mapping(self,rows):
        p=self.root/'members.csv'
        p.write_text('svat_id,hru_id,x,y\n'+''.join(','.join(map(str,r))+'\n' for r in rows));return p
    def fixture(self):
        m=self.mapping([(1,101,125,625),(2,101,125,625),(3,9001,375,625)])
        src={}
        for j,role in enumerate(ROLES):
            for day in ['20200101','20200102']:
                # FRF's larger extent exercises the actual BBC07G failure geometry.
                a=[[j+1,-2*(j+1),9],[3,4,5]] if role=='frf' else [[j+1,-2*(j+1)],[3,4]]
                grid(self.root/role/(day+'.idf'),a)
            src[role]=dict(pattern=str(self.root/role/'{date}.idf'),spatial_operation='CELL_NET',positive_multiplier=1)
        cfg=dict(start='2020-01-01',end='2020-01-02',members=str(m),expected_hrus=2,
                 units='m3/calendar_day',positive='into_layer1',sources=src)
        p=self.root/'config.json';p.write_text(json.dumps(cfg));return p
    def test_physical_cell_deduplication_and_sparse_ids(self):
        r=Raster(grid(self.root/'ref.idf',[[1,2]]))
        m=members(self.mapping([(1,101,125,625),(2,101,125,625),(3,9001,375,625)]),r,2)
        self.assertEqual(len(m['h']),2);self.assertEqual(m['area'].tolist(),[62500,62500])
    def test_conflicting_cell_ownership_rejected(self):
        r=Raster(grid(self.root/'ref.idf',[[1,2]]))
        with self.assertRaisesRegex(ValueError,'multiple HRUs'):
            members(self.mapping([(1,101,125,625),(2,102,125,625)]),r,2)
    def test_same_resolution_different_extent(self):
        r=Raster(grid(self.root/'ref.idf',[[1,2]]))
        g=Raster(grid(self.root/'wide.idf',[[7,8,9]],xmin=-250))
        row,col=g.indices(np.array([125]),np.array([625]),r)
        self.assertEqual(g.sample(row,col).tolist(),[8])
    def test_fractional_cell_shift_rejected(self):
        r=Raster(grid(self.root/'ref.idf',[[1,2]]))
        g=Raster(grid(self.root/'shift.idf',[[7,8,9]],xmin=.1))
        with self.assertRaisesRegex(ValueError,'ALIGNMENT'):
            g.indices(np.array([125]),np.array([625]),r)
    def test_resolution_mismatch_rejected(self):
        r=Raster(grid(self.root/'ref.idf',[[1,2]]))
        g=Raster(grid(self.root/'small.idf',[[7,8]],dx=125))
        with self.assertRaisesRegex(ValueError,'SIZE'):
            g.indices(np.array([125]),np.array([625]),r)
    def test_missing_coverage_rejected(self):
        r=Raster(grid(self.root/'ref.idf',[[1,2]]))
        with self.assertRaisesRegex(ValueError,'COVERAGE'):
            r.indices(np.array([625]),np.array([625]))
    def test_missing_value_rejected(self):
        r=Raster(grid(self.root/'ref.idf',[[-9999,2]]))
        with self.assertRaisesRegex(ValueError,'missing source'):
            r.sample(np.array([0]),np.array([0]))
    def test_complete_production_volume_resume_and_existing_consumer(self):
        cfg=self.fixture();out=self.root/'out'
        first=process(cfg,out)
        self.assertEqual((first['days'],first['physical_cells'],first['hrus']),(2,2,2))
        lines=(out/'bbc/HRU_00101.bbc').read_text().splitlines()
        q=float(lines[4].split()[1]);self.assertAlmostEqual(q*62500/100,15,places=12)
        q2=float((out/'bbc/HRU_09001.bbc').read_text().splitlines()[4].split()[1])
        self.assertAlmostEqual(q2*62500/100,-30,places=12)
        hashes=[x['sha256'] for x in first['bbc']]
        second=process(cfg,out);self.assertEqual(second['reused_days'],2);self.assertTrue(second['bbc_reused'])
        self.assertEqual(hashes,[x['sha256'] for x in second['bbc']])
        reception=receive(out/'transfer/transfer.json',out/'transfer',self.root/'received')
        self.assertEqual(reception['errors'],[])
    def test_source_change_recomputes_and_missing_day_invalidates_manifest(self):
        cfg=self.fixture();out=self.root/'out';process(cfg,out)
        grid(self.root/'ghb/20200102.idf',[[40,-40],[0,0]])
        self.assertEqual(process(cfg,out)['reused_days'],1)
        (self.root/'wel/20200102.idf').unlink()
        with self.assertRaises(FileNotFoundError):process(cfg,out)
        self.assertFalse((out/'manifest.json').exists())
        self.assertFalse((out/'transfer/transfer.json').exists())
    def test_explicit_face_operation_not_applied_twice(self):
        p=self.fixture();cfg=json.loads(p.read_text())
        cfg['sources']['frf']['spatial_operation']='SAVED_CURRENT_MINUS_PREVIOUS_COLUMN'
        p.write_text(json.dumps(cfg));out=self.root/'out';process(p,out)
        a=np.load(out/'daily/2020-01-01.npy')
        self.assertEqual(a[:,1].tolist(),[2,-6])
    def test_lock_survives_stale_file_and_rejects_concurrency(self):
        lock=self.root/'production.lock';lock.write_text('stale process id')
        first=acquire_lock(lock)
        try:
            with self.assertRaisesRegex(RuntimeError,'another BBC'):acquire_lock(lock)
        finally:first.close()
        acquire_lock(lock).close()

    def test_wel_extra_year_does_not_extend_period(self):
        for role in ROLES:
            d=self.root/('bdg'+role)
            if role=='flf':d/='diepe_slootkwel_gecorrigeerd'
            grid(d/('bdg'+role+'_20221231_l1.idf'),[[1]])
            if role=='wel':grid(d/'bdgwel_20230101_l1.idf',[[1]])
        x=discover(self.root,'2022-12-31','2022-12-31')
        self.assertEqual(x['wel']['available_total'],2)
        self.assertEqual(x['wel']['available_in_period'],1)
        self.assertEqual(len(list(days('1970-01-01','2022-12-31'))),19358)

if __name__=='__main__':unittest.main()
