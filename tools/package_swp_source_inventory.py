"""Package the source-location inventory with already uploaded run controls."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def build(controls_archive,output):
    records=[]
    output.parent.mkdir(parents=True,exist_ok=True)
    prefix='LWKM_WorkE_SWP_Bronnen/'
    with zipfile.ZipFile(controls_archive) as source,zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as target:
        selected=[n for n in source.namelist() if Path(n).name.lower().startswith('control_run_') and n.lower().endswith('.ini')]
        seen=set()
        for name in sorted(selected):
            base=Path(name).name
            if base in seen:raise ValueError(f'duplicate uploaded control filename {base}')
            seen.add(base);content=source.read(name)
            target.writestr(prefix+'source_data/prior_run_controls/'+base,content)
            records.append(dict(archive_path=name,filename=base,sha256=hashlib.sha256(content).hexdigest()))
        if not records:raise ValueError('no original run controls in archive')
        manifest=dict(source_archive_sha256=hashlib.sha256(controls_archive.read_bytes()).hexdigest(),controls=records)
        target.writestr(prefix+'source_data/prior_run_controls/provenance.json',json.dumps(manifest,indent=2)+'\n')
        for name in ('tools/server/swp_source_inventory.py','tools/lhm_run_chain_provenance.py'):
            target.write(ROOT/name,prefix+name)
        for name in ('tools/__init__.py','tools/server/__init__.py'):target.writestr(prefix+name,'')
        target.write(ROOT/'tools/server/inventariseer_swp_bronnen.cmd',prefix+'inventariseer_swp_bronnen.cmd')
        target.write(ROOT/'docs/server/SWP_SOURCE_INVENTORY_20261029.md',prefix+'README.md')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--controls-archive',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();result=build(a.controls_archive,a.output)
    print(json.dumps(dict(output=str(a.output),controls=len(result['controls']))))


if __name__=='__main__':main()
