"""Reproduce BBC08 checks using supplied original FLF/FRF and bundled real members.

This consumes existing rasters only. It does not qualify complete forcing or SWAP.
"""
import argparse,csv,json
from pathlib import Path
import numpy as np
from tools.server.bbc_production import Raster,members,sha,write_json


def qualify(flf,frf,mapping,output,expected_hrus=10242):
    reference=Raster(flf);source=Raster(frf)
    m=members(mapping,reference,expected_hrus)
    rr,cc=source.indices(m['x'],m['y'],reference)
    # Compare coordinate sampling with independently translated FLF row/column indices.
    dx=int(round((reference.xmin-source.xmin)/reference.dx))
    dy=int(round((source.ymax-reference.ymax)/reference.dy))
    if not np.array_equal(rr,m['row']+dy) or not np.array_equal(cc,m['col']+dx):
        raise AssertionError('coordinate/index mismatch')
    v=np.asarray(source.values[rr,cc],dtype='float64')
    good=np.isfinite(v)&(v!=source.nodata)
    by_hru=np.bincount(m['inv'],weights=np.where(good,v,0.),minlength=len(m['domain']))
    # Missing source cells are counted, never admitted as actual zero fluxes.
    complete=np.bincount(m['inv'],weights=~good,minlength=len(m['domain']))==0
    raw_sum=float(__import__('math').fsum(v[good]));hru_sum=float(by_hru.sum())
    delta=abs(raw_sum-hru_sum)
    if delta>1e-10*max(1,float(abs(v[good]).sum())):raise AssertionError('volume mismatch')
    report=dict(status='REAL_SOURCE_GEOMETRY_CHECK_NOT_FORCING_ADMISSION',
        production_admitted=False,inputs={str(p):sha(p) for p in [flf,frf,mapping]},
        flf_geometry=reference.geometry,frf_geometry=source.geometry,
        svats=m['svats'],physical_cells=len(m['h']),hrus=len(m['domain']),
        duplicate_physical_cells=m['svats']-len(m['h']),
        full_cell_area_m2=reference.dx*reference.dy,total_area_m2=float(m['area'].sum()),
        complete_frf_hrus=int(complete.sum()),missing_frf_cells=int((~good).sum()),
        selected_frf_m3=raw_sum,grouped_frf_m3=hru_sum,volume_difference_m3=delta,
        limitations=['FRF sampled as stored; no new sign or reconstruction choice',
            'One real source day, not full five-component historical coverage',
            'Different source run identities are not asserted equivalent',
            'No corrected FLF/full GHB/MET forcing or modern end-to-end run admission'])
    write_json(output,report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ['flf','frf','mapping','output']:p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(json.dumps(qualify(a.flf,a.frf,a.mapping,a.output),indent=2))
