"""Run the compiled primary producer; no mocked serializer or SWAP process.
Usage: python test_hum_contract.py DIRECT_EXE [LEGACY_CSV_EXE]
"""
from pathlib import Path
import csv
import json
import math
import subprocess
import sys
import tempfile
import unittest

EXE = Path(sys.argv.pop(1)).resolve()
LEGACY = Path(sys.argv.pop(1)).resolve() if len(sys.argv)>1 else None
VARS = ('RD1','EV24','TN','TX','Q','HUM','WIND','WET_RAW')
VALUES = (2.,1.,3.,6.,100.,.724,11.595999,.5)

class PrimaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='met08 test ')
        self.root = Path(self.tmp.name)
        self.days = ['19700101','19700102']
        self.nc, self.nr = 3, 1
        self.links = [(1,0,1.,1.)]
        self.cfg = dict(weights='weights.csv',template='RD1_19700101.asc',
                        output_met='out',start_year='1970',end_year='1970',
                        start_date='19700101',end_date='19700102',
                        quantity_HUM='actual_vapour_pressure',unit_HUM='kPa')
        for k,v in zip(VARS,VALUES):
            self.cfg['path_'+k] = 'UG/UG_{date}.asc' if k=='HUM' else k+'_{date}.asc'
            self.cfg['scale_'+k] = '1'
            self.grid(k,[v]*3)
        # An existing FG source must never be silently used as humidity.
        for day in self.days: (self.root/('FG_'+day+'.asc')).write_text('NOT HUM')
    def tearDown(self):
        self.tmp.cleanup()
    def grid(self,key,values):
        for day in self.days:
            p=self.root/self.cfg['path_'+key].replace('{date}',day)
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('ncols %s\nnrows %s\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n%s\n'
                         %(self.nc,self.nr,' '.join(map(str,values))))
    def call(self,extra='',legacy=False):
        (self.root/'weights.csv').write_text('hru_id,grid_id,area_m2,weight\n'+
            ''.join('%s,%s,%s,%s\n'%x for x in self.links))
        c=dict(self.cfg)
        if legacy: c['output']=c.pop('output_met')
        (self.root/'config.ini').write_text(''.join(k+'='+v+'\n' for k,v in c.items())+extra)
        return subprocess.run([str(LEGACY if legacy else EXE),str(self.root/'config.ini')],
                              cwd=self.root,capture_output=True,text=True,timeout=60)
    def okay(self):
        r=self.call();self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        return (self.root/'out/HRU_00001.met').read_bytes()
    def reject(self,contains=None):
        r=self.call();self.assertNotEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertFalse((self.root/'out').exists())
        if contains:self.assertIn(contains,r.stderr)
    def test_values_and_distinct_wind(self):
        b=self.okay();self.assertEqual(b.splitlines()[1],
             b"'1' 1 1 1970 100.000000 3.000000 6.000000 0.724000 11.595999 2.000000 1.000000 0.500000")
        self.assertIn('producer_version=MET08_PRIMARY_UG_HUM', (self.root/'out/MANIFEST.txt').read_text())
    def test_old_config_rejected_before_output(self):
        self.cfg['path_FG']=self.cfg.pop('path_HUM');self.cfg['scale_FG']=self.cfg.pop('scale_HUM')
        self.reject('LEGACY_FG_HUM_REJECTED');self.assertFalse((self.root/'out.partial').exists())
    def test_both_old_and_new_rejected(self):
        self.cfg['path_FG']='FG_{date}.asc';self.reject('LEGACY_FG_HUM_REJECTED')
    def test_old_scale_alone_rejected(self):
        self.cfg['scale_FG']='1';self.reject('LEGACY_FG_HUM_REJECTED')
    def test_wrong_quantity(self):
        self.cfg['quantity_HUM']='relative_humidity';self.reject('ACTUAL_VAPOUR')
    def test_wrong_unit(self):
        self.cfg['unit_HUM']='percent';self.reject('ACTUAL_VAPOUR')
    def test_missing_quantity(self):
        del self.cfg['quantity_HUM'];self.reject('HUM_CONFIG_MISSING')
    def test_missing_path(self):
        del self.cfg['path_HUM'];self.reject('HUM_CONFIG_MISSING')
    def test_missing_scale(self):
        del self.cfg['scale_HUM'];self.reject('HUM_CONFIG_MISSING')
    def test_conversion_rejected(self):
        self.cfg['scale_HUM']='0.1';self.reject('SCALE_ONE')
    def test_scale_trailing_junk_rejected(self):
        self.cfg['scale_HUM']='1garbage';self.reject('SCALE_ONE')
    def test_scale_nan_rejected(self):
        self.cfg['scale_HUM']='nan';self.reject('SCALE_ONE')
    def test_fg_named_as_hum_rejected_even_in_range(self):
        self.cfg['path_HUM']='FG/FG_{date}.asc';self.reject('IDENTIFIED_LHM_UG')
    def test_percent_file_named_as_hum_rejected(self):
        self.cfg['path_HUM']='RH/RH_{date}.asc';self.reject('IDENTIFIED_LHM_UG')
    def test_duplicate_configuration(self):
        r=self.call('unit_HUM=kPa\n');self.assertNotEqual(r.returncode,0);self.assertIn('Duplicate config key',r.stderr)
        self.assertFalse((self.root/'out.partial').exists())
    def test_negative_hum(self):
        self.grid('HUM',[-.1,.5,.5]);self.reject('HUM_OUTSIDE')
    def test_large_hum(self):
        self.grid('HUM',[10.3,.5,.5]);self.reject('HUM_OUTSIDE')
    def test_invalid_unselected_source_pixel_not_hidden(self):
        self.grid('HUM',[.5,10.3,.5]);self.reject('HUM_OUTSIDE')
    def test_nan_not_a_donor_candidate(self):
        self.grid('HUM',['nan',.5,.5]);self.reject()
    def test_inf_not_a_donor_candidate(self):
        self.grid('HUM',['inf',.5,.5]);self.reject()
    def test_all_nodata_not_zero_filled(self):
        self.grid('HUM',[-9999]*3);self.reject('HUM_ALL_NODATA')
    def test_zero_valid(self):
        self.grid('HUM',[0.]*3);self.assertIn(b'0.000000',self.okay().splitlines()[1])
    def test_ten_valid(self):
        self.grid('HUM',[10.]*3);self.assertEqual(self.okay().splitlines()[1].split()[7],b'10.000000')
    def test_nearest_tie_uses_original_lowest_index(self):
        self.links=[(1,1,1.,1.)];self.grid('HUM',[.2,-9999,.8])
        self.assertEqual(self.okay().splitlines()[1].split()[7],b'0.200000')
    def test_multiple_nodata_do_not_become_donors(self):
        self.nc=4
        for k,v in zip(VARS,VALUES):self.grid(k,[v]*4)
        self.links=[(1,2,1.,1.)];self.grid('HUM',[.2,-9999,-9999,.8])
        self.assertEqual(self.okay().splitlines()[1].split()[7],b'0.800000')
    def test_weighted_hum(self):
        self.links=[(1,0,1.,.25),(1,2,3.,.75)];self.grid('HUM',[.2,.5,.8])
        self.assertEqual(self.okay().splitlines()[1].split()[7],b'0.650000')
    def test_aggregate_bound_not_silently_clipped(self):
        self.links=[(1,0,1.,1.+5e-10)];self.grid('HUM',[10.]*3);self.reject('HUM_OUTSIDE')
    def test_wet_zero_rain_rule_unchanged(self):
        self.grid('RD1',[0.]*3);self.assertEqual(self.okay().splitlines()[1].split()[-1],b'0.000000')
    def test_wet_rain_positive_fallback_unchanged(self):
        self.grid('WET_RAW',[-9999]*3);self.assertEqual(self.okay().splitlines()[1].split()[-1],b'0.100000')
    def test_missing_ug_file_is_not_filled_from_fg(self):
        (self.root/'UG/UG_19700101.asc').unlink();self.reject('Grid missing')
    def test_existing_output_not_overwritten(self):
        self.okay();p=self.root/'out/HRU_00001.met';old=p.read_bytes();r=self.call()
        self.assertNotEqual(r.returncode,0);self.assertEqual(p.read_bytes(),old)
    def test_10242_hrus_and_sparse_release(self):
        self.links=[(i,0,1.,1.) for i in range(1,10243)];self.okay()
        self.assertEqual(len(list((self.root/'out').glob('HRU_*.met'))),10242)
        self.cfg['output_met']='sparse';self.links=[(i,0,1.,1.) for i in (101,205,9001)]
        self.cfg['release_binding_sha256']='a'*64;r=self.call();self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(sorted(p.name for p in (self.root/'sparse').glob('*.met')),
                         ['HRU_00101.met','HRU_00205.met','HRU_09001.met'])
    def test_two_real_source_samples(self):
        data=json.loads((Path(__file__).parent/'hum_source_replay.json').read_text())
        for d in data['days']:
            with self.subTest(day=d['date']):
                self.nc=len(data['rows']);self.days=[d['date']]
                self.cfg.update(template='RD1_'+d['date']+'.asc',start_date=d['date'],end_date=d['date'],output_met='out_'+d['date'])
                self.links=[(1,i,float(w['area_m2']),float(w['weight'])) for i,w in enumerate(data['rows'])]
                for k,v in zip(VARS,VALUES):self.grid(k,[v]*self.nc)
                self.grid('HUM',d['ug_values']);r=self.call();self.assertEqual(r.returncode,0,r.stderr)
                b=(self.root/self.cfg['output_met']/'HRU_00001.met').read_bytes()
                self.assertEqual(b.splitlines()[1].split()[7].decode(),d['expected_hum_token'])
                self.assertNotEqual(d['expected_hum_token'],d['old_fg_hum_token'])
    @unittest.skipIf(LEGACY is None,'legacy binary not supplied')
    def test_legacy_csv_source_also_fixed(self):
        self.links=[(i,0,1.,1.) for i in range(1,10243)];r=self.call(legacy=True)
        self.assertEqual(r.returncode,0,r.stderr)
        with (self.root/'out/met_1970.csv').open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),20484)
        self.assertTrue(all(float(x['vapour_pressure_kpa'])==.724 and float(x['wind_m_s'])==11.595999 for x in rows))
    @unittest.skipIf(LEGACY is None,'legacy binary not supplied')
    def test_legacy_old_config_stops_before_sources(self):
        self.cfg['path_FG']='FG_{date}.asc';r=self.call(legacy=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('LEGACY_FG_HUM_REJECTED',r.stderr)
        self.assertFalse((self.root/'out').exists())

if __name__=='__main__':unittest.main(verbosity=2)
