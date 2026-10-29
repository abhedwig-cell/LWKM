import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tools.swp_direct_render import Catalog
from tests import test_swp_run_parameters as parameter_tests

ROOT=Path(__file__).resolve().parents[1]


class DirectTests(unittest.TestCase):
    def test_real_lookup_render_and_missing_year(self):
        fixture=parameter_tests.ParameterTests();fixture.setUp();run,_=fixture.derive()
        catalog=Catalog(ROOT/'config/swp/lookup_catalog.json.gz')
        context=catalog.context(run)
        self.assertEqual(context['RDS'],120)
        run['TEND']='2020-10-20'
        bounded=catalog.context(run)
        self.assertEqual(bounded['TABLE_CROPROTATION'][0]['CROPEND'],'2020-10-31')
        self.assertEqual(context['TABLE_CROPROTATION'][0]['CROPNAME'],"'fictief'")
        run['TEND']='2100-12-31'
        with self.assertRaisesRegex(ValueError,'missing rotation year'):catalog.context(run)

    def test_full_grid_to_swp_command_and_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder)
            def table(name, record):
                p=d/name
                with p.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=list(record));w.writeheader();w.writerow(record)
                return str(p)
            hru=table('hru.csv',dict(HRU=1,svat_repr=10,bodem370=261,lu4=3,rz_repr=120))
            members=table('members.csv',dict(svat=10,HRU=1,x=125,y=375))
            values=dict(glk=2,area=100,dqsat=8,lgn=5,bfe=261,irr_switch=1,meteo=1,bbc=2,head=1)
            for k,v in values.items():
                (d/(k+'.asc')).write_text('ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n'+f'{v} {v}\n{v} {v}\n')
            control=d/'control.inp'
            control.write_text('TimStart=20200101\nTimEnd=20201231\nMaxPondDepth=.002\ncrunoff_par=.25\ntempCbotk=12\n'+''.join(f'{k}={k}.asc\n' for k in values if k!='head'))
            command=[sys.executable,'-m','tools.swp_direct_pipeline','--control',str(control),'--base',str(d),
                     '--hru',hru,'--members',members,'--head',str(d/'head.asc'),'--output',str(d/'out'),'--expected-hrus','1']
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            swp=d/'out/swp/1.swp';text=swp.read_text()
            self.assertNotIn('{{',text)
            self.assertIn('2020',text)
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            manifest=json.loads((d/'out/swp/manifest.json').read_text())
            self.assertEqual(manifest['hrus'][0]['status'],'REUSED')
            self.assertEqual(manifest['status'],'SWP_RENDERED_NOT_SWAP_VALIDATED')
