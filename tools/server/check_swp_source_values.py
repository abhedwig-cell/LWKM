"""Read confirmed server sources at existing locations; report raw values/geometry.

This is a data check, not SWP production or automatic unit conversion.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import zipfile


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def grid(path):
    import numpy as np
    if path.suffix.lower()=='.idf':
        from tools.idf_reader import read_idf
        g=read_idf(path)
        return g.values,dict(ncols=g.ncol,nrows=g.nrow,xmin=g.xmin,ymin=g.ymin,dx=g.dx,dy=g.dy,nodata=g.nodata)
    with path.open() as f:header=dict(f.readline().lower().split() for _ in range(6))
    dx=dy=float(header['cellsize'])
    xmin=float(header['xllcorner']) if 'xllcorner' in header else float(header['xllcenter'])-dx/2
    ymin=float(header['yllcorner']) if 'yllcorner' in header else float(header['yllcenter'])-dy/2
    a=np.loadtxt(path,skiprows=6,ndmin=2)
    if a.shape!=(int(header['nrows']),int(header['ncols'])):raise ValueError('ASCII shape mismatch')
    return a,dict(ncols=a.shape[1],nrows=a.shape[0],xmin=xmin,ymin=ymin,dx=dx,dy=dy,nodata=float(header['nodata_value']))


def sample(values,g,xy):
    import numpy as np
    col=np.floor((xy[:,0]-g['xmin'])/g['dx']).astype(int)
    row=np.floor((g['ymin']+g['nrows']*g['dy']-xy[:,1])/g['dy']).astype(int)
    inside=(col>=0)&(col<g['ncols'])&(row>=0)&(row<g['nrows'])
    centered=np.isclose(xy[:,0],g['xmin']+(col+.5)*g['dx'],rtol=0,atol=1e-5)&np.isclose(xy[:,1],g['ymin']+(g['nrows']-row-.5)*g['dy'],rtol=0,atol=1e-5)
    result=np.full(len(xy),np.nan)
    valid=inside&centered
    result[valid]=values[row[valid],col[valid]]
    nodata=result==g['nodata'];result[nodata]=np.nan
    summary=dict(points=len(xy),outside=int((~inside).sum()),off_center=int((inside&~centered).sum()),
                 nodata_or_nonfinite=int((inside&centered&~np.isfinite(result)).sum()),finite=int(np.isfinite(result).sum()))
    v=result[np.isfinite(result)]
    if len(v):summary['raw_values']=dict(min=float(v.min()),max=float(v.max()),p05=float(np.quantile(v,.05)),median=float(np.median(v)),p95=float(np.quantile(v,.95)))
    return result,summary


def main():
    import numpy as np
    root=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,default=root/'config/swp/server_locations_20261029.json')
    p.add_argument('--members',type=Path,default=root/'source_data/membership.csv.gz')
    p.add_argument('--output',type=Path,default=Path('swp_broncontrole'))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    with gzip.open(a.members,'rt') as f:members=list(csv.DictReader(f))
    if len({r['svat'] for r in members})!=len(members):raise ValueError('duplicate SVATs in membership')
    xy=np.array([(float(m['x']),float(m['y'])) for m in members])
    expected_area=np.array([float(m['svat_area_m2']) for m in members])
    sources=json.loads(a.sources.read_text())['sources'];results={};arrays={}
    for role,spec in sources.items():
        path=Path(spec['path']);print(f'LEES {role}: {path}',flush=True)
        try:
            before=path.stat()
            if path.suffix.lower() not in ('.asc','.idf'):
                with path.open('rb') as f:preview=f.read(4096).decode('utf-8-sig',errors='replace')
                results[role]=dict(status='TEXT_PREVIEW_ONLY',path=str(path),bytes=before.st_size,first_4096_bytes_text=preview)
                continue
            values,geometry=grid(path);raw,summary=sample(values,geometry,xy)
            digest=sha(path);after=path.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('source changed during check')
            results[role]=dict(status='RAW_GRID_CHECKED_UNITS_UNVERIFIED',path=str(path),bytes=before.st_size,sha256=digest,geometry=geometry,samples=summary)
            if role in ('glk','head'):arrays[role]=raw
            if role=='area':
                mask=np.isfinite(raw)&(expected_area>0)
                ratio=raw[mask]/expected_area[mask]
                results[role]['comparison_with_qualified_svat_area']=dict(points=int(mask.sum()),min_ratio=float(ratio.min()) if len(ratio) else None,max_ratio=float(ratio.max()) if len(ratio) else None)
        except (OSError,ValueError,KeyError) as exc:results[role]=dict(status='ERROR',path=str(path),error=str(exc))
    diagnostics={}
    if 'glk' in arrays and 'head' in arrays:
        for label,scale in [('NO_SURFACE_CONVERSION',1),('SURFACE_CM_TO_M_HYPOTHESIS',.01)]:
            depth=arrays['glk']*scale-arrays['head'];v=depth[np.isfinite(depth)]
            diagnostics[label]=dict(points=len(v),min=float(v.min()) if len(v) else None,median=float(np.median(v)) if len(v) else None,max=float(v.max()) if len(v) else None)
    errors=sum(r['status']=='ERROR' for r in results.values())
    report=dict(status='SOURCE_VALUE_CHECK_NOT_PRODUCTION_QUALIFIED',numpy=np.__version__,members=len(members),hrus=len({m['HRU'] for m in members}),errors=errors,
                source_binding_sha256=sha(a.sources),membership_sha256=sha(a.members),sources=results,
                groundwater_depth_unit_hypotheses=diagnostics,limitations=['No units chosen or conversions applied.','No HRU identity recomputed.','No models executed.'])
    (a.output/'source_values.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    archive=a.output.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:z.write(a.output/'source_values.json','source_values.json')
    print(f'GEREED: {archive}; fouten: {errors}')
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
