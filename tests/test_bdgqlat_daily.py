"""Standalone unit checks using tiny synthetic IDF 1271 files."""
import tempfile
from pathlib import Path
import struct
import unittest
import numpy as np
from tools.server.bdgqlat_daily import produce_one
from tools.server.bbc_production import Raster

def idf(path, a):
    a=np.asarray(a,dtype='<f4')
    ny,nx=a.shape
    head=struct.pack('<3i7f4B2f',1271,nx,ny,0,nx,0,ny,0,0,-9999,0,0,0,0,1,1)
    Path(path).write_bytes(head+a.tobytes())

class DailyNet(unittest.TestCase):
    def test_conservation(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            idf(d/'mask.idf',[[1,1],[1,1]])
            # FRF current = right-going contribution stored at left cell;
            # FFF current = downward contribution stored at top cell.
            idf(d/'frf.idf',[[2,0],[3,0]])
            idf(d/'fff.idf',[[4,5],[0,0]])
            mask=Raster(d/'mask.idf')
            active=np.ones((2,2),dtype=bool)
            rr,cc=np.where(active)
            x=mask.xmin+(cc+.5)*mask.dx
            y=mask.ymax-(rr+.5)*mask.dy
            values,stats=produce_one(d/'frf.idf',d/'fff.idf',mask,active,rr,cc,x,y)
            np.testing.assert_allclose(values,[6,3,-1,-8])
            self.assertEqual(stats['qlat_sum_m3_day'],0)
    def test_reject_closed_forward_face(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            idf(d/'mask.idf',[[1,0]])
            idf(d/'frf.idf',[[2,-9999]])
            idf(d/'fff.idf',[[0,-9999]])
            mask=Raster(d/'mask.idf')
            active=np.array([[True,False]])
            rr,cc=np.where(active)
            x=mask.xmin+(cc+.5)*mask.dx
            y=mask.ymax-(rr+.5)*mask.dy
            with self.assertRaisesRegex(ValueError,'closed|inactive'):
                produce_one(d/'frf.idf',d/'fff.idf',mask,active,rr,cc,x,y)

if __name__=='__main__':unittest.main()
