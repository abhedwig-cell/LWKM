#!/usr/bin/env python3
"""Bind original SVATs to 66-area ASCII grid; preserve one record per source SVAT."""
import argparse, csv, hashlib, json, math, os, sys
from collections import Counter
from pathlib import Path
import numpy as np

def read_grid(path):
    with open(path, encoding='ascii') as f:
        h={}
        for _ in range(6):
            words=f.readline().split();
            if len(words)!=2: raise ValueError('Ongeldige ESRI ASCII header')
            h[words[0].lower()] = float(words[1])
    for k in ('ncols','nrows','xllcorner','yllcorner','cellsize','nodata_value'):
        if k not in h: raise ValueError('Rasterheader mist '+k)
    g=np.loadtxt(path,skiprows=6,dtype=np.int32)
    ncols,nrows=int(h['ncols']),int(h['nrows'])
    if g.shape!=(nrows,ncols):raise ValueError(f'Rasterdimensies {g.shape} != {(nrows,ncols)}')
    codes=set(np.unique(g))- {int(h['nodata_value'])}
    if codes!=set(range(1,67)):raise ValueError('Verwacht gebiedscodes 1 t/m 66, aangetroffen '+repr(sorted(codes)))
    return g,h

def column(fields, variants):
    standard={''.join(c.lower() for c in name if c.isalnum()):name for name in fields}
    for v in variants:
        key=''.join(c.lower() for c in v if c.isalnum())
        if key in standard:return standard[key]
    raise ValueError(f'Geen kolom gevonden voor {variants}; beschikbaar: {fields}')

def run(gxg, grid, out, expect=645582):
    raster,h=read_grid(grid)
    out.parent.mkdir(parents=True,exist_ok=True)
    x0,y0,cell=h['xllcorner'],h['yllcorner'],h['cellsize']
    ymax=y0+int(h['nrows'])*cell
    counts=Counter();seen=set();rows=0;sample=[]
    tmp=out.with_suffix(out.suffix+'.partial')
    with open(gxg,newline='',encoding='utf-8-sig') as src,open(tmp,'w',newline='',encoding='utf-8') as dst:
        reader=csv.DictReader(src)
        if not reader.fieldnames: raise ValueError('Lege input')
        s=column(reader.fieldnames,['SVAT','svat_id','svat_orig'])
        x=column(reader.fieldnames,['X_RD','x(m)','x','X','xc(m)','x_rd_m','xcoord'])
        y=column(reader.fieldnames,['Y_RD','y(m)','y','Y','yc(m)','y_rd_m','ycoord'])
        writer=csv.writer(dst);writer.writerow(['SVAT','Gebied','N'])
        for rec in reader:
            rows+=1
            id=int(rec[s]);
            if id in seen:raise ValueError(f'Dubbele SVAT {id}')
            seen.add(id)
            xx=float(rec[x]);yy=float(rec[y])
            if not math.isfinite(xx) or not math.isfinite(yy):raise ValueError(f'Ongeldige xy SVAT {id}')
            col=math.floor((xx-x0)/cell);row=math.floor((ymax-yy)/cell)
            if not (0<=row<raster.shape[0] and 0<=col<raster.shape[1]):
                area='';counts['OUTSIDE']+=1
                if len(sample)<15:sample.append({'SVAT':id,'reason':'OUTSIDE','X':xx,'Y':yy})
            else:
                val=int(raster[row,col]);
                if val==int(h['nodata_value']):
                    area='';counts['NODATA']+=1
                    if len(sample)<15:sample.append({'SVAT':id,'reason':'NODATA','X':xx,'Y':yy})
                elif not 1<=val<=66:raise ValueError(f'Geen toegelaten gebiedscode {val} voor SVAT {id}')
                else:area=val;counts[str(val)]+=1
            writer.writerow([id,area,1])
    if expect and rows!=expect:
        tmp.unlink(missing_ok=True)
        raise ValueError(f'Verwacht {expect} SVATs, gekregen {rows}')
    os.replace(tmp,out)
    report={'source_svat_csv':str(gxg),'area_raster':str(grid),'rows':rows,'unique_svat':len(seen),'valid_area_rows':sum(v for k,v in counts.items() if k.isdigit()),'nodata_rows':counts['NODATA'],'outside_rows':counts['OUTSIDE'],'per_area_svat_count':{str(i):counts[str(i)] for i in range(1,67)},'unmapped_samples':sample,'N_definition':'1 per original SVAT'}
    out.with_suffix('.manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('KLAAR:',out)
    print('SVAT:',rows,'gebied gekoppeld:',report['valid_area_rows'],'NoData:',counts['NODATA'],'buiten raster:',counts['OUTSIDE'])
    if counts['NODATA'] or counts['OUTSIDE']:
        print('LET OP: onvolledige dekking, zie manifest. Ontbrekende gebieden zijn leeg, niet 0.')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gxg',type=Path,required=True);p.add_argument('--grid',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--expect',type=int,default=645582)
    a=p.parse_args()
    try:run(a.gxg,a.grid,a.out,a.expect)
    except Exception as exc:print('STOP:',exc,file=sys.stderr);sys.exit(1)
