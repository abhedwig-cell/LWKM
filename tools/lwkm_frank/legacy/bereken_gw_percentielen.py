"""GW5/GW95 from the 720 14th/28th layer-1 MODFLOW heads, 1991-2020.

Percentiles are defined on DEPTHS (cm below land surface): GW5=P5,
GW95=P95. Thus GW5 is shallow and GW95 is deep; GHG<=GG<=GLG
approximately, but not necessarily GHG==GW5 or GLG==GW95.

This program reuses the existing GxG SVAT table for coordinates and land
surface. It does NOT re-parse fixed-width area_svat.inp, and it leaves the
previous GxG export unchanged.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, os, pathlib, shutil, sys, time
import numpy as np
from wb10_reader import raster, sample_xy

ROOT=pathlib.Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
OUTBASE=ROOT/'LWKM_run_resultaten_totaal'
HEADS=OUTBASE/'modflow'/'head'
GXG=OUTBASE/'frank_export_heads'/'FRANK_LHM_SVAT_GXG_GG_1991_2020.csv'
OUTPUT=OUTBASE/'frank_export_heads'/'percentielen_v01'


def dates():
    return [dt.date(y,m,d) for y in range(1991,2021) for m in range(1,13) for d in (14,28)]


def index_heads(folder):
    import re
    pat=re.compile(r'head_((?:19|20)\d{6})(?:000000)?_l1\.idf$',re.I)
    found={}
    if not folder.is_dir():raise FileNotFoundError(f'Head-directory ontbreekt: {folder}')
    for p in folder.iterdir():
        if not p.is_file():continue
        m=pat.fullmatch(p.name)
        if not m:continue
        day=m[1]
        if day in found:raise ValueError(f'Dubbel headbestand: {day}: {found[day]}, {p}')
        found[day]=p
    return found


def read_base(path):
    if not path.is_file():raise FileNotFoundError(f'Bestaande GxG-CSV ontbreekt: {path}')
    cols={'SVAT','X_RD','Y_RD','maaiveld_mNAP','GHG_cm_mv','GLG_cm_mv','GG_cm_mv'}
    ids=[]; xs=[]; ys=[]; glks=[]
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        missing=cols-set(reader.fieldnames or [])
        if missing:raise ValueError(f'GxG-CSV mist kolommen: {sorted(missing)}')
        for row in reader:
            ids.append(int(row['SVAT']));xs.append(float(row['X_RD']))
            ys.append(float(row['Y_RD']));glks.append(float(row['maaiveld_mNAP']))
    if len(ids)!=645582:raise ValueError(f'Verwacht 645582 SVATs, gevonden {len(ids)}')
    if len(set(ids))!=len(ids):raise ValueError('Dubbele SVAT-ID in GxG-CSV')
    for a in [xs,ys,glks]:
        if not np.isfinite(a).all():raise ValueError('Niet-eindige X/Y/maaiveld in GxG-CSV')
    return np.asarray(ids,dtype=np.int64),np.asarray(xs),np.asarray(ys),np.asarray(glks)


def quantile_5_95(matrix,block=8192):
    """Exact NumPy linear percentiles with 720 samples, per SVAT, blockwise.

    Return NaNs if any of the 720 samples for a SVAT is invalid.
    """
    m,n=matrix.shape
    if m!=720:raise ValueError(f'Verwacht 720 standen, ontvangen {m}')
    p5=np.full(n,np.nan,dtype=np.float64)
    p95=np.full(n,np.nan,dtype=np.float64)
    a=0.05*(m-1);b=0.95*(m-1)
    lo5,lo95=int(np.floor(a)),int(np.floor(b))
    hi5,hi95=lo5+1,lo95+1
    for s in range(0,n,block):
        e=min(s+block,n)
        z=np.array(matrix[:,s:e],dtype=np.float32,copy=True)
        complete=np.isfinite(z).all(axis=0)
        z[:,~complete]=np.inf
        z.partition((lo5,hi5,lo95,hi95),axis=0)
        x5=z[lo5].astype('f8')*(hi5-a)+z[hi5].astype('f8')*(a-lo5)
        x95=z[lo95].astype('f8')*(hi95-b)+z[hi95].astype('f8')*(b-lo95)
        x5[~complete]=np.nan;x95[~complete]=np.nan
        p5[s:e]=x5;p95[s:e]=x95
    return p5,p95


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for v in iter(lambda:f.read(1024*1024),b''):h.update(v)
    return h.hexdigest()


def write_output(base,output,ids,p5,p95):
    out=output/'FRANK_LHM_SVAT_GXG_GG_GW5_GW95_1991_2020.csv'
    tmp=pathlib.Path(str(out)+'.partial')
    with base.open(newline='',encoding='utf-8-sig') as f, tmp.open('w',newline='',encoding='utf-8') as o:
        reader=csv.DictReader(f)
        fields=list(reader.fieldnames or [])
        for name in ('GW5','GW95'):
            if name in fields:raise ValueError(f'Invoer bevat al {name}')
        writer=csv.DictWriter(o,fieldnames=fields+['GW5','GW95'])
        writer.writeheader()
        for i,row in enumerate(reader):
            if i>=len(ids) or int(row['SVAT'])!=ids[i]:raise ValueError('SVAT-volgorde gewijzigd tijdens uitvoeren')
            row['GW5']='' if not np.isfinite(p5[i]) else format(p5[i],'.6f')
            row['GW95']='' if not np.isfinite(p95[i]) else format(p95[i],'.6f')
            writer.writerow(row)
    tmp.replace(out)
    return out


def run(args):
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    ds=dates();index=index_heads(pathlib.Path(args.head_dir))
    missing=[d.strftime('%Y%m%d') for d in ds if d.strftime('%Y%m%d') not in index]
    report={'method':'linear interpolation (NumPy quantile method=linear)',
            'GW5':'5th percentile of groundwater DEPTH (cm below ground surface)',
            'GW95':'95th percentile of groundwater DEPTH (cm below ground surface)',
            'reference':'1991-2020, day 14 and 28 each month',
            'required_head_files':720,'available':720-len(missing),
            'missing_dates':missing[:25],'input_gxg_csv':str(args.gxg),
            'header_note':'GW5 shallow; GW95 deep; percentiles of depths, not NAP elevations'}
    report_path=out/'GW5_GW95_MANIFEST.json'
    if missing:
        report['status']='STOPPED_INCOMPLETE_HEAD_SERIES'
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        raise FileNotFoundError(f'{len(missing)} benodigde head-IDFs ontbreken. Controleer manifest: {report_path}')
    ids,x,y,glk=read_base(pathlib.Path(args.gxg));n=len(ids)
    report['n_svat']=n
    required=720*n*4
    report['temporary_matrix_bytes']=required
    if args.check_only:
        report['status']='SOURCES_OK'
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(f'OK: {n} SVATs, 720 head-IDFs. Tijdelijke werkruimte circa {required/1e9:.2f} GB.')
        return 0
    usage=shutil.disk_usage(out)
    if usage.free<required+500_000_000:
        raise OSError(f'Vrije schijfruimte te klein: {usage.free/1e9:.2f} GB; nodig >= {(required+500_000_000)/1e9:.2f} GB')
    cache=out/'GW5_GW95_WORK_720xSVAT.float32.tmp'
    if cache.exists():cache.unlink() # Never use stale/partial matrix
    a=np.memmap(cache,dtype='<f4',mode='w+',shape=(720,n))
    geo_ref=None;rc=None
    try:
        t0=time.time()
        for j,d in enumerate(ds):
            path=index[d.strftime('%Y%m%d')]
            geo,nd,values=raster(path)
            if geo_ref is None:
                geo_ref=geo;rc=sample_xy(geo,x,y)
            elif geo!=geo_ref:raise ValueError(f'Rastergeometrie wijkt af: {path}')
            h=np.asarray(values[rc],dtype=np.float64)
            ok=np.isfinite(h)&(h!=nd)&(h>-1e10)&(h<1e10)
            depth=(glk-h)*100
            depth[~ok]=np.nan
            a[j,:]=depth.astype('f4')
            if (j+1)%24==0:
                a.flush()
                print(f'Heads gelezen: {j+1}/720 ({d.year}), verstreken {int(time.time()-t0)}s',flush=True)
        a.flush()
        print('Bereken exacte P5 en P95 per SVAT...',flush=True)
        p5,p95=quantile_5_95(a,block=args.block)
        valid=np.isfinite(p5)&np.isfinite(p95)
        if np.any((p5>p95)&valid):raise ValueError('GW5 > GW95: ongeldige kwantielberekening')
        result=write_output(pathlib.Path(args.gxg),out,ids,p5,p95)
        report.update({'status':'COMPLETE','output_csv':str(result),'sha256_output':sha(result),
                       'complete_svats':int(valid.sum()),'incomplete_svats':int((~valid).sum()),
                       'head_raster_geometry':str(geo_ref)})
        report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(f'KLAAR: {result} ({valid.sum()}/{n} complete SVATs)',flush=True)
        return 0
    finally:
        del a
        if cache.exists():cache.unlink()


def cli():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gxg',type=pathlib.Path,default=GXG)
    p.add_argument('--head-dir',type=pathlib.Path,default=HEADS)
    p.add_argument('--out',type=pathlib.Path,default=OUTPUT)
    p.add_argument('--check-only',action='store_true')
    p.add_argument('--block',type=int,default=8192)
    args=p.parse_args()
    if args.block<1 or args.block>50000:p.error('--block must be between 1 and 50000')
    return run(args)

if __name__=='__main__':sys.exit(cli())
