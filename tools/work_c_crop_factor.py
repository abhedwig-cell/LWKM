"""Source-bound constant crop-factor projection for the three grass ETref cases.

The supplied 3.0.0 grass template contains CF=1 at every DNR node. A constant
function is invariant under the day-number/development-stage coordinate. Only
this mathematically unambiguous case is accepted; no tulip factors are inferred.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
from tools.swp_full_oracle import parse_named_table
from tools.assemble_swap_package import assemble,sha256
from tools.package_preflight import validate
from tools.execute_swap_candidate import execute


def project(crop,source):
    rows=parse_named_table(source,'DNR CH CF')
    if len(rows)<2:raise ValueError('missing source CF table')
    factor=float(rows[0][2])
    if not 0<=factor<=2 or any(float(row[2])!=factor for row in rows):
        raise ValueError('nonconstant/out-of-range CF requires independently qualified axis mapping')
    if re.search(r'(?m)^\s*(CFTB|CF)\b',crop):raise ValueError('crop already contains factors')
    out,n=re.subn(r'(?m)^(\s*SWCF\s*=)\s*2\b',r'\g<1> 1',crop)
    if n!=1:raise ValueError('expected one SWCF=2')
    out+=f'\n* Source-bound constant CF projection; see provenance.json\nCFTB =\n0.0 {factor:.8f}\n2.0 {factor:.8f}\n* End of table\n'
    return out,{'source_header':'DNR CH CF','constant_cf':factor,
                'axis_rule':'CONSTANT_FUNCTION_INVARIANT_UNDER_DNR_TO_DVS',
                'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('packages','factor-source','output','executable','library'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    base=json.loads(a.packages.read_text());results=[]
    for hid in (7909,7910,7911):
        row=next(r for r in base['runs'] if r['run_id']==hid)
        src=Path(row['package']);stage=a.output/'inputs'/str(hid);shutil.copytree(src,stage)
        crop=stage/'gras_beweiding.crp';out,audit=project(crop.read_text(),a.factor_source.read_text());crop.write_text(out)
        swp=stage/'swap.swp';s=swp.read_text();s=re.sub(r'(?m)^(\s*SWETR\s*=)\s*0\b',r'\g<1> 1',s);s=re.sub(r'(?m)^(\s*SWDIVIDE\s*=)\s*1\b',r'\g<1> 0',s);swp.write_text(s)
        preflight=validate(stage)
        assets={n:{'path':str(stage/n),'sha256':sha256(stage/n),
                   'qualification_id':'SOURCED_CF_RESEARCH_VARIANT_NOT_PRODUCTION'} for n in preflight['files']}
        manifest=assemble(hid,assets,a.output/'packages',profile_id='WORK_C_SOURCED_GRASS_CF_V1',
            code_commit='sha256:'+sha256(Path(__file__)),file_keys=('METFIL',),required_assets=preflight['files'])
        target=a.output/'packages'/f'run_{hid:05d}'
        audit.update(source_file=str(a.factor_source),source_sha256=sha256(a.factor_source),
                     parent_package_manifest_sha256=sha256(src/'manifest.json'))
        (target/'provenance.json').write_text(json.dumps(audit,indent=2)+'\n')
        result=execute(a.executable,target,a.output/'executions'/str(hid),library_path=a.library,
                       expected_start=preflight['start'],expected_end=preflight['end'])
        results.append({'run_id':hid,'source_projection':audit,'manifest':manifest,'execution':result})
    (a.output/'summary.json').write_text(json.dumps({'results':results,'production_admitted':False},indent=2)+'\n')
    print(json.dumps({'execution_pass':sum(r['execution']['status']=='EXECUTION_PASS' for r in results)}))
