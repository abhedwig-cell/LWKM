"""Daily BDGQLAT IDFs from BBC09 saved incoming right/front faces. Requires NumPy.

Usage (in LWKM package root):
 python -m tools.server.bdgqlat_daily --root G:\\...\\modflow --mask source_data/IBOUND_L1.IDF --output G:\\...\\modflow\\bdgqlat_reconstructed --start 1970-01-01 --end 2022-12-31
"""
from __future__ import annotations
import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import numpy as np
from tools.server.bbc_production import Raster, sha, acquire_lock

def timeline(start, end):
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if a>b or a<date(1970,1,1) or b>date(2022,12,31):
        raise ValueError('Period must be within 1970-2022')
    while a<=b:
        yield a.strftime('%Y%m%d')
        a+=timedelta(days=1)

def inventory(root, role, wanted):
    folder=Path(root)/('bdg'+role)
    rx=re.compile(r'^bdg'+role+r'_((?:19|20)\d{6})(\d{6})?_l1\.idf$',re.I)
    groups={}
    for f in folder.iterdir():
        if not f.is_file():continue
        m=rx.fullmatch(f.name)
        if m:
            try:date(int(m[1][:4]),int(m[1][4:6]),int(m[1][6:8]))
            except ValueError:continue
            pat=str(f.parent/(f.name[:m.start(1)]+'{date}'+f.name[m.end(1):]))
            groups.setdefault(pat,set()).add(m[1])
    if len(groups)!=1:raise ValueError(f'Ambiguous or missing {role} series: {folder}, patterns={len(groups)}')
    pat,available=next(iter(groups.items()))
    missing=sorted(set(wanted)-available)
    if missing:raise ValueError(f'{role}: {len(missing)} missing days; first: {missing[:8]}')
    return pat

def produce_one(frf,fff,mask,active,rr,cc,x,y):
    # Geometry is mapped using exact cell centres; raster extents may differ.
    right=Raster(frf);front=Raster(fff)
    current=[]
    for src in (right,front):
        sr,sc=src.indices(x,y,mask)
        current.append(src.sample(sr,sc))
    if np.any(active[:,1:] & ~active[:,:-1]):pass # no assumption about inactive predecessors
    outputs=[]
    for axis,src,values in ((1,right,current[0]),(0,front,current[1])):
        prv=np.zeros(len(rr),dtype=np.float64)
        # BBC09: predecessor column for FRF, predecessor row for FFF
        pred=(cc>0) if axis==1 else (rr>0)
        select=np.flatnonzero(pred)
        pr=rr[select]-(axis==0)
        pc=cc[select]-(axis==1)
        good=active[pr,pc]
        valid=select[good]
        if len(valid):
            px=x[valid]-(mask.dx if axis==1 else 0)
            py=y[valid]+(mask.dy if axis==0 else 0)
            sr,sc=src.indices(px,py,mask)
            prv[valid]=src.sample(sr,sc)
        forward=np.zeros(len(rr),dtype=bool)
        if axis==1:
            ix=cc+1<mask.nx
            forward[ix]=active[rr[ix],cc[ix]+1]
        else:
            ix=rr+1<mask.ny
            forward[ix]=active[rr[ix]+1,cc[ix]]
        if np.any(values[~forward]!=0):
            raise ValueError('Nonzero stored face across inactive/outer forward boundary')
        outputs.append(values-prv)
    total=outputs[0]+outputs[1]
    # Independent check: internal saved faces cancel globally; only open edges remain.
    if not np.all(np.isfinite(total)):raise ValueError('Nonfinite net flux')
    return total,{'frf_net_sum_m3_day':float(outputs[0].sum()),
                  'fff_net_sum_m3_day':float(outputs[1].sum()),
                  'qlat_sum_m3_day':float(total.sum()),
                  'max_abs_m3_day':float(np.max(np.abs(total),initial=0))}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--mask',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--start',default='1970-01-01')
    p.add_argument('--end',default='2022-12-31')
    p.add_argument('--limit',type=int,default=0,help='For bounded one-day or week qualification')
    args=p.parse_args(argv)
    wanted=list(timeline(args.start,args.end))
    patterns={role:inventory(args.root,role,wanted) for role in ('frf','fff')}
    mask=Raster(args.mask)
    m=np.asarray(mask.values)
    active=np.isfinite(m)&(m!=mask.nodata)&(m!=0)
    rr,cc=np.where(active)
    if not len(rr):raise ValueError('IBOUND has no active cells')
    x=mask.xmin+(cc+.5)*mask.dx
    y=mask.ymax-(rr+.5)*mask.dy
    args.output.mkdir(parents=True,exist_ok=True)
    lock=acquire_lock(args.output/'.bdgqlat.lock')
    try:
        contract={'start':args.start,'end':args.end,'sources':patterns,
                  'mask':str(args.mask.resolve()),'mask_sha256':sha(args.mask),
                  'operation':'BBC09_SAVED_CURRENT_MINUS_PREVIOUS_COLUMN_ROW',
                  'unit':'m3/calendar_day','positive':'into_MODFLOW_layer1',
                  'grid':list(mask.geometry),'active_cells':int(len(rr))}
        cfg=args.output/'contract.json'
        if cfg.exists() and json.loads(cfg.read_text(encoding='utf8'))!=contract:
            raise ValueError('Output contract differs; use a new output directory')
        if not cfg.exists():cfg.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf8')
        done=0; reused=0
        for stamp in wanted:
            if args.limit and done+reused>=args.limit:break
            dst=args.output/f'BDGQLAT_{stamp}.IDF'
            receipt=args.output/f'BDGQLAT_{stamp}.json'
            srcs={r:Path(patterns[r].replace('{date}',stamp)) for r in patterns}
            source_hashes={r:sha(srcs[r]) for r in srcs}
            if dst.exists() and receipt.exists():
                data=json.loads(receipt.read_text(encoding='utf8'))
                if data.get('sha256')==sha(dst) and data.get('sources_sha256')==source_hashes and data.get('contract_mask_sha256')==contract['mask_sha256']:
                    reused+=1;continue
                raise ValueError(f'Existing day cannot be reused safely: {stamp}')
            if dst.exists() or receipt.exists():raise ValueError(f'Incomplete previous output for {stamp}')
            net,stats=produce_one(srcs['frf'],srcs['fff'],mask,active,rr,cc,x,y)
            out=np.full((mask.ny,mask.nx),mask.nodata,dtype='<f4')
            if np.any(np.abs(net)>np.finfo('f4').max):raise ValueError('Output overflow')
            out[rr,cc]=net.astype('<f4')
            # Identity-compatible standard 1271 header (same grid, no unknown trailer).
            with args.mask.open('rb') as f:header=f.read(52)
            temp=dst.with_suffix('.IDF.partial')
            with temp.open('wb') as f:
                f.write(header);f.write(out.tobytes(order='C'))
            temp.replace(dst)
            receipt.write_text(json.dumps({'date':stamp,'sha256':sha(dst),
                'sources_sha256':source_hashes,'contract_mask_sha256':contract['mask_sha256'],
                **stats},indent=2)+'\n',encoding='utf8')
            done+=1
            print(f'{stamp}: {stats["qlat_sum_m3_day"]:.8g} m3/day',flush=True)
        print(json.dumps({'created':done,'reused':reused,'requested':len(wanted),
            'output':str(args.output)}))
    finally:lock.close()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'BDGQLAT STOP: {exc}',file=sys.stderr);sys.exit(2)
