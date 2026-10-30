import copy
from pathlib import Path
import tempfile
import unittest
from tools.swp_run_parameters import derive, sample_grid, nint, FIELDS


class ParameterTests(unittest.TestCase):
    def setUp(self):
        self.hru={'HRU':'1','svat_repr':'10','bodem370':'261','lu4':'3','rz_repr':'120'}
        self.members=[dict(svat='10',x='125',y='375',col='1',row='1',lgn='5',
                           bfe='261',glk='2',head='1',area='100',dqsat='8',
                           irr_switch='1',meteo='1',bbc='2')]
        self.soil={261:dict(grondsoort2='1',soil_id='4014')}
        self.crop={(1,3):dict(crop_id='23',croporg_id='8',SWETR='0')}
        self.config=dict(climate_id='__',start='2020-01-01',end='2020-12-31',
                         MaxPondDepth=.002,crunoff_par=.25,tempCbotk=12)

    def derive(self):
        return derive(self.hru,self.members,self.soil,self.crop,self.config)

    def test_all_37_fields_and_units(self):
        row,diag=self.derive()
        self.assertEqual(set(row),set(FIELDS))
        self.assertEqual(len(FIELDS),37)
        self.assertEqual((row['RDS'],row['GWLI'],row['PONDMX']),(120,-100,.2))
        self.assertEqual(diag['root_source'],'HRU_rz_repr_cm')

    def test_hru_authority_and_equal_member_head_mean(self):
        other=copy.deepcopy(self.members[0])
        other.update(svat='11',glk='4',head='1',area='900',lgn='10')
        self.members.append(other)
        row,_=self.derive()
        self.assertEqual((row['GWLI'],row['area'],row['lu_id'],row['crop_id']),(-200,1000,5,23))

    def test_root_grid_is_explicit(self):
        del self.hru['rz_repr']
        self.members[0]['rds']='.8'
        with self.assertRaises(ValueError): self.derive()
        self.config['root_policy']='representative_grid'
        self.assertEqual(self.derive()[0]['RDS'],80)

    def test_fortran_rounding_and_groundwater_cap(self):
        self.assertEqual([nint(v) for v in [-1.5,1.5]],[-2,2])
        self.members[0]['head']='3'
        self.assertEqual(self.derive()[0]['GWLI'],0)

    def test_owner_median_does_not_select_soil_subset(self):
        self.members[0]['bfe']='99'
        self.assertEqual(self.derive()[0]['dqsat'],8)

    def test_coordinate_sampling_and_shift_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'grid.asc'
            p.write_text('ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n1 2\n3 -9999\n')
            self.assertEqual(sample_grid(p,self.members),[(1.,1,1)])
            shifted=[dict(self.members[0],x='126')]
            with self.assertRaises(ValueError):sample_grid(p,shifted)
            nodata=[dict(self.members[0],x='375',y='125')]
            with self.assertRaises(ValueError):sample_grid(p,nodata)

    def test_cli_success_and_incomplete_rerun_clears_success(self):
        import csv
        import json
        from unittest.mock import patch
        from tools.swp_run_parameters import main
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def write(name, records):
                target=root/(name+'.csv')
                with target.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
                return str(target)
            hp=write('hru',[self.hru])
            mp=write('members',[dict(self.members[0],HRU='1')])
            sp=write('soil',[dict(self.soil[261],bodem370='261')])
            cp=write('crop',[dict(self.crop[1,3],soil2_id='1',lu4='3')])
            cfg=root/'config.json';cfg.write_text(json.dumps(self.config))
            argv=['producer','--hru',hp,'--members',mp,'--soil',sp,'--crop',cp,
                  '--config',str(cfg),'--output',str(root/'out'),'--expected-hrus','1']
            with patch('sys.argv',argv):self.assertEqual(main(),0)
            self.assertTrue((root/'out/runs_candidate.csv').exists())
            bad=dict(self.hru);del bad['rz_repr'];write('hru',[bad])
            with patch('sys.argv',argv):self.assertEqual(main(),1)
            self.assertFalse((root/'out/runs_candidate.csv').exists())
            self.assertEqual(json.loads((root/'out/errors.json').read_text())[0]['HRU'],1)

    def test_all_members_even_when_representative_zero_or_soil_differs(self):
        self.members[0]['dqsat']='0'
        for svat, value in [('11','8'),('12','20')]:
            self.members.append(dict(self.members[0],svat=svat,dqsat=value,bfe='99'))
        row,diag=self.derive()
        self.assertEqual(row['dqsat'],14)
        self.assertEqual(diag['dqsat']['candidate_spacing_m'],56)
        self.assertEqual(diag['dqsat']['source_representative_dqsat'],0)
        self.assertEqual(diag['dqsat']['zero_count'],1)

    def test_old_metadata_policy_is_rejected(self):
        self.config['dqsat_policy']='representative_svat_metadata'
        with self.assertRaisesRegex(ValueError,'owner decision'):self.derive()

    def test_equal_irrigation_area_chooses_groundwater(self):
        self.members[0]['irr_switch']='2'
        self.members.append(dict(self.members[0],svat='11',irr_switch='1'))
        run,diag=self.derive()
        self.assertEqual(run['irrigation_id'],1)
        self.assertTrue(diag['irrigation_source_tied'])
        self.assertEqual(diag['irrigation_source_counts'],{1:1,2:1})

    def test_irrigation_source_uses_area_instead_of_counts(self):
        self.members[0].update(irr_switch='1',area='100')
        self.members.extend(dict(self.members[0],svat=str(i),irr_switch='2',area='20') for i in (11,12))
        run,diag=self.derive()
        self.assertEqual(run['irrigation_id'],1)
        self.assertEqual(diag['irrigation_source_areas_m2'],{1:100.,2:40.})
        self.assertFalse(diag['irrigation_source_tied'])
        self.members[1]['area']='81'
        self.assertEqual(self.derive()[0]['irrigation_id'],2)

    def test_equal_area_groundwater_even_with_fewer_svats(self):
        self.members[0].update(irr_switch='1',area='100')
        self.members.extend(dict(self.members[0],svat=str(i),irr_switch='2',area='50') for i in (11,12))
        self.assertEqual(self.derive()[0]['irrigation_id'],1)
        self.assertTrue(self.derive()[1]['irrigation_source_tied'])

    def test_no_irrigation_and_existing_activation_threshold(self):
        self.members[0]['irr_switch']='0'
        self.assertEqual(self.derive()[0]['irrigation_id'],0)
        self.members.extend(dict(self.members[0],svat=str(i),area='1') for i in (11,12))
        self.members[0]['irr_switch']='1'
        self.assertEqual(self.derive()[0]['irrigation_id'],0)

    def test_invalid_irrigation_code_fails(self):
        self.members[0]['irr_switch']='3'
        with self.assertRaisesRegex(ValueError,'unsupported irrigation'):self.derive()
