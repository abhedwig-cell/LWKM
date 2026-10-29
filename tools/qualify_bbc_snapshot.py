"""Replay retained six-HRU real research component values through BBC08 and D1.

The IDFs are explicitly re-encodings of archived numeric research output, not
new original server grids. Historical GHB and corrected-FLF limitations remain.
"""
import argparse,csv,io,json,struct,zipfile
from pathlib import Path
import numpy as np
from tools.server.bbc_production import ROLES,process,write_json,sha
from tools.production_transfer import receive


def qualify(archive,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        m=list(csv.DictReader(io.StringIO(z.read('membership.csv').decode())))
        c=list(csv.DictReader(io.StringIO(z.read('daily/2020-07-01-cells.csv').decode())))
        expected=list(csv.DictReader(io.StringIO(z.read('daily/2020-07-01-hrus.csv').decode())))
        header=z.read('selected-membership-support.idf')[:52]
    _,nx,ny,*other=struct.unpack('<3i10f',header)
    xmin,xmax,ymin,ymax,_,_,nodata,_,dx,dy=other
    path=output/'members.csv'
    path.write_text('svat_id,hru_id,x,y\n'+''.join(f"{r['cell_id']},{r['hru_id']},{xmin+(int(r['col'])+.5)*dx},{ymax-(int(r['row'])+.5)*dy}\n" for r in m))
    lookup={r['cell_id']:r for r in c};sources={}
    for role in ROLES:
        a=np.full((ny,nx),nodata,dtype='<f4')
        for r in m:a[int(r['row']),int(r['col'])]=float(lookup[r['cell_id']][role])
        dest=output/(role+'_20200701.idf');dest.write_bytes(header+a.tobytes())
        sources[role]=dict(pattern=str(dest.resolve()),spatial_operation='CELL_NET',positive_multiplier=1)
    config=output/'config.json'
    write_json(config,dict(start='2020-07-01',end='2020-07-01',members=str(path.resolve()),expected_hrus=len(expected),
        units='m3/calendar_day',positive='into_layer1',sources=sources,
        provenance='REENCODED_RETAINED_REAL_RESEARCH_VALUES_NOT_ORIGINAL_SERVER_IDFS'))
    first=process(config,output/'producer');again=process(config,output/'producer')
    actual={r['hru_id']:r for r in csv.DictReader((output/'producer/transfer/2020-07-01.csv').open())}
    maxerr=max(abs(float(actual[r['hru_id']]['q_ext_mm_d'])-float(r['q_ext_mm_d'])) for r in expected)
    if maxerr>1e-7:raise AssertionError('real snapshot replay error')
    received=receive(output/'producer/transfer/transfer.json',output/'producer/transfer',output/'received')
    report=dict(status='REAL_NUMERIC_SNAPSHOT_REPLAY_NOT_MODERN_SOURCE_ADMISSION',production_admitted=False,
        archive_sha256=sha(archive),hrus=first['hrus'],physical_cells=first['physical_cells'],
        max_q_ext_difference_mm_d=maxerr,reused_days=again['reused_days'],consumer_errors=received['errors'],
        limitations=['Source values re-encoded as float32 IDF for this software regression',
          'Cached historical research GHB, not current operational GHB',
          'No corrected operational FLF or MET qualification',
          'One day, six HRUs, no time extrapolation'],
        code_sha256=sha(__file__))
    write_json(output/'summary.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(qualify(a.archive,a.output),indent=2))
