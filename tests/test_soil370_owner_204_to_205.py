"""Owner decision 2026-11-20: soil370 204 always becomes 205."""
import csv
import gzip
import json
import unittest
from pathlib import Path
from tools.swp_run_parameters import canonical_bodem370, SOIL370_REPLACEMENTS
from tools.swp_direct_render import Catalog

ROOT=Path(__file__).resolve().parents[1]

class Soil370Owner204To205(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'config/swp/soil_classification_and_profile.csv').open(newline='') as f:
            cls.soils={int(r['bodem370']):r for r in csv.DictReader(f)}
        with gzip.open(ROOT/'config/swp/lookup_catalog.json.gz','rt') as f:
            cls.catalog=json.load(f)

    def test_general_rule(self):
        self.assertEqual(SOIL370_REPLACEMENTS,{204:205})
        self.assertEqual(canonical_bodem370(204,self.soils),205)
        self.assertEqual(canonical_bodem370('204',self.soils),205)
        self.assertEqual(canonical_bodem370(205,self.soils),205)
        self.assertEqual(canonical_bodem370(140,self.soils),140)

    def test_compatible_classification_required(self):
        altered={k:dict(v) for k,v in self.soils.items()}
        altered[205]['grondsoort2']='999'
        with self.assertRaisesRegex(ValueError,'grondsoort2'):
            canonical_bodem370(204,altered)
        del altered[205]
        with self.assertRaisesRegex(ValueError,'missing replacement'):
            canonical_bodem370(204,altered)

    def test_real_205_profile(self):
        props=sorted((r for r in self.catalog['tables']['eigenschappen'] if int(r['bodem_id'])==205),
                     key=lambda r:int(r['ISOILLAY']))
        self.assertEqual([r['sfu'] for r in props],['B05','O05','O05'])
        sublayers=sorted((r for r in self.catalog['tables']['discretisatie']
                          if int(r['bodem_id'])==205 and int(r['dikte_id'])==1700),
                         key=lambda r:int(r['ISUBLAY']))
        self.assertEqual(float(sublayers[0]['HSUBLAY']),5.0)
        self.assertEqual(int(sublayers[0]['ISOILLAY']),1)
        only_o05=[r['sfu'] for r in self.catalog['tables']['eigenschappen'] if int(r['bodem_id'])==204]
        self.assertEqual(only_o05,['O05'])

    def test_old_204_parameters_are_rejected(self):
        catalog=Catalog(ROOT/'config/swp/lookup_catalog.json.gz')
        with self.assertRaisesRegex(ValueError,'SOIL204_FORBIDDEN'):
            catalog.context({'bodem_id':'204'})

if __name__=='__main__':
    unittest.main()
