"""BBC stage of Work E. BBC09 uses the verified corrected saved-face producer convention."""
import argparse,json,subprocess,sys
from pathlib import Path
from tools.server.bbc_production import discover,process,write_json,sha

ROOT=r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',default=ROOT,type=Path)
    p.add_argument('--members',default='source_data/svat_hru_xy.csv.gz',type=Path)
    p.add_argument('--output',default='work_e_bbc09',type=Path)
    p.add_argument('--start',default='1970-01-01');p.add_argument('--end',default='2022-12-31')
    p.add_argument('--expected-hrus',default=10242,type=int)
    p.add_argument('--profile',choices=['corrected-saved-faces-20261016','work-a-saved-faces'],default='corrected-saved-faces-20261016')
    p.add_argument('--activity-mask',default='source_data/IBOUND_L1.IDF',type=Path)
    p.add_argument('--config',type=Path,help='Use an already explicit five-component configuration')
    p.add_argument('--d1-plan',type=Path,help='After BBC, execute an existing fully bound D1 plan')
    a=p.parse_args()
    try:
        # Probe the actual interpreter before processing, without installing anything.
        probe=subprocess.run([sys.executable,'-m','tools.server.bbc_production','--probe'],check=True,capture_output=True,text=True)
        print(probe.stdout,flush=True)
        if a.config: config=a.config
        else:
            config=a.output.parent/(a.output.name+'-sources.json')
            inventory=discover(a.root,a.start,a.end)
            write_json(a.output.parent/(a.output.name+'-inventory.json'),inventory)
            sources={role:{k:spec[k] for k in ['pattern','spatial_operation','positive_multiplier']}
                     for role,spec in inventory.items()}
            if a.profile in ('corrected-saved-faces-20261016','work-a-saved-faces'):
                sources['frf']['spatial_operation']='SAVED_CURRENT_MINUS_PREVIOUS_COLUMN'
                sources['fff']['spatial_operation']='SAVED_CURRENT_MINUS_PREVIOUS_ROW'
            obj=dict(start=a.start,end=a.end,members=str(a.members.resolve()),expected_hrus=a.expected_hrus,
                     units='m3/calendar_day',positive='into_layer1',sources=sources,
                     source_semantics_profile=a.profile,
                     activity_mask=dict(path=str(a.activity_mask.resolve()),sha256=sha(a.activity_mask)),
                     profile_authority='LWKM_MF_L1_Horizontal.cs corrected 2026-10-16 + Work A saved-face net convention')
            if config.exists() and json.loads(config.read_text()) != obj:
                raise ValueError('source configuration changed: choose a new output')
            write_json(config,obj)
        report=process(config,a.output)
        print(json.dumps({k:report[k] for k in ['status','days','hrus','reused_days']}))
        if a.d1_plan:
            # D1 consumes transfer/transfer.json through its existing hash-bound plan.
            subprocess.run([sys.executable,'-m','tools.work_d1','--plan',str(a.d1_plan),
                            '--output',str(a.output.parent/'work_e_d1')],check=True)
        return 0
    except Exception as e:
        print('WORK E STOP: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
