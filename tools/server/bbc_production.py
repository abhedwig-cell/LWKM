"""BBC09: bounded, restartable BBC production from existing five daily IDF products.

Requires numpy only; --probe runs before importing it. No flux reconstruction,
interpolation, spatial resampling, zero filling or source-semantic inference.
Config explicitly records the spatial operation of each existing product.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, timedelta
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROLES = ('flf', 'frf', 'fff', 'ghb', 'wel')
OPERATIONS = {'CELL_NET', 'SAVED_CURRENT_MINUS_PREVIOUS_COLUMN', 'SAVED_CURRENT_MINUS_PREVIOUS_ROW'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()


def atomic(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.partial')
    tmp.write_bytes(data); tmp.replace(path)


def write_json(path, obj):
    atomic(path, (json.dumps(obj, sort_keys=True, indent=2) + '\n').encode())


def days(start, end):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    if a > b or a < date(1970, 1, 1) or b > date(2022, 12, 31):
        raise ValueError('BBC period must be within 1970-2022')
    while a <= b:
        yield a.isoformat(); a += timedelta(days=1)


class Raster:
    """Observed 1271 regular single precision IDF, including provenance footer."""
    def __init__(self, path):
        import numpy as np
        self.path = Path(path)
        with self.path.open('rb') as f: header = f.read(52)
        if len(header) != 52: raise ValueError('short IDF header: ' + str(path))
        magic, self.nx, self.ny = struct.unpack('<3i', header[:12])
        if magic != 1271: raise ValueError('unqualified IDF variant: ' + str(magic))
        (self.xmin, self.xmax, self.ymin, self.ymax, _, _, self.nodata) = struct.unpack('<7f', header[12:40])
        equi, topbot, _, _ = header[40:44]
        self.dx, self.dy = struct.unpack('<2f', header[44:52])
        if equi or topbot or min(self.nx, self.ny, self.dx, self.dy) <= 0:
            raise ValueError('unsupported/invalid IDF geometry: ' + str(path))
        if not all(__import__('math').isfinite(v) for v in self.geometry):
            raise ValueError('nonfinite geometry')
        if abs((self.xmax-self.xmin)/self.dx-self.nx) > 1e-6 or abs((self.ymax-self.ymin)/self.dy-self.ny) > 1e-6:
            raise ValueError('IDF extent/dimension inconsistency')
        size = 52 + 4*self.nx*self.ny
        actual = self.path.stat().st_size
        if actual < size: raise ValueError('truncated IDF: ' + str(path))
        if actual > size:
            with self.path.open('rb') as f: f.seek(size); trailer = f.read()
            if len(trailer) < 8: raise ValueError('short metadata footer')
            n, words = struct.unpack('<2i', trailer[:8])
            if n != 1 or words < 0 or len(trailer) != 8 + 4*words or any(b not in (0,9,10,13) and not 32 <= b <= 126 for b in trailer[8:]):
                raise ValueError('unknown IDF trailer')
        self.values = np.memmap(self.path, dtype='<f4', mode='r', offset=52, shape=(self.ny,self.nx))

    @property
    def geometry(self): return (self.nx,self.ny,self.xmin,self.xmax,self.ymin,self.ymax,self.dx,self.dy)

    def indices(self, x, y, reference=None):
        import numpy as np
        if reference:
            if abs(self.dx-reference.dx) > 1e-7 or abs(self.dy-reference.dy) > 1e-7:
                raise ValueError('CELL_SIZE_MISMATCH: ' + str(self.path))
            shifts = ((self.xmin-reference.xmin)/self.dx, (self.ymax-reference.ymax)/self.dy)
            if any(abs(s-round(s)) > 1e-6 for s in shifts):
                raise ValueError('GRID_ALIGNMENT_MISMATCH: ' + str(self.path))
        cf, rf = (x-self.xmin)/self.dx, (self.ymax-y)/self.dy
        # Membership coordinates are cell centres. Never silently snap arbitrary points.
        if np.any(abs(cf-np.floor(cf)-.5) > 1e-6) or np.any(abs(rf-np.floor(rf)-.5) > 1e-6):
            raise ValueError('membership is not at cell centres')
        col, row = np.floor(cf).astype('int64'), np.floor(rf).astype('int64')
        if np.any((row<0)|(col<0)|(row>=self.ny)|(col>=self.nx)):
            raise ValueError('GRID_COVERAGE_MISSING: ' + str(self.path))
        return row, col

    def sample(self, row, col):
        import numpy as np
        values = np.asarray(self.values[row,col], dtype='float64')
        if np.any(~np.isfinite(values)|(values==self.nodata)):
            bad=np.flatnonzero(~np.isfinite(values)|(values==self.nodata))[:5]
            raise ValueError('missing source values: '+str(self.path)+' sample_row_col='+str([(int(row[i]),int(col[i])) for i in bad]))
        return values


def members(path, reference, expected):
    import numpy as np
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    ids = [r['svat_id'] for r in rows]
    if len(set(ids)) != len(ids): raise ValueError('duplicate SVAT identity')
    x = np.array([float(r['x']) for r in rows]); y = np.array([float(r['y']) for r in rows])
    h = np.array([int(r['hru_id']) for r in rows])
    if np.any(h<=0): raise ValueError('invalid HRU identity')
    rr, cc = reference.indices(x,y)
    # Deduplicate physical cells, rejecting any cross-HRU ownership conflict.
    keys = rr*reference.nx+cc
    order = np.argsort(keys, kind='stable'); k, hh = keys[order], h[order]
    if np.any((k[1:]==k[:-1]) & (hh[1:]!=hh[:-1])):
        raise ValueError('physical MODFLOW cell belongs to multiple HRUs')
    keep = order[np.r_[True,k[1:]!=k[:-1]]]
    x,y,h,rr,cc = x[keep],y[keep],h[keep],rr[keep],cc[keep]
    domain, inv = np.unique(h, return_inverse=True)
    if len(domain) != expected: raise ValueError('HRU population count mismatch')
    area = np.bincount(inv)*reference.dx*reference.dy
    return dict(x=x,y=y,h=h,row=rr,col=cc,domain=domain,inv=inv,area=area,svats=len(ids))


def discover(root, start, end):
    """BBC07H source selection policy, without assuming a particular clock suffix."""
    result = {}; wanted = {d.replace('-','') for d in days(start,end)}
    for role in ROLES:
        directory = Path(root)/('bdg'+role)
        if role == 'flf': directory /= 'diepe_slootkwel_gecorrigeerd'
        groups = {}
        expression = re.compile(r'^bdg'+role+r'_((?:19|20)\d{6})(\d{6})?_l1\.idf$',re.I)
        for path in sorted(directory.glob('*')):
            if not path.is_file(): continue
            match = expression.fullmatch(path.name)
            if not match: continue
            stamp = match[1]
            try: date(int(stamp[:4]),int(stamp[4:6]),int(stamp[6:8]))
            except ValueError: continue
            pattern = str(path.parent/(path.name[:match.start(1)]+'{date}'+path.name[match.end(1):]))
            groups.setdefault(pattern,set()).add(stamp)
        if len(groups) != 1: raise ValueError('ambiguous/missing authoritative series: '+str(directory))
        pattern, available = next(iter(groups.items()))
        missing = sorted(wanted-available)
        if missing: raise ValueError(role+' missing days '+','.join(missing[:20]))
        result[role] = dict(pattern=pattern, spatial_operation='CELL_NET', positive_multiplier=1,
                            available_total=len(available),available_in_period=len(wanted))
    return result


def face_net(raster, mask, m, reference, role, multiplier):
    """Stored incoming right/front face minus the opposite stored face.

    The corrected producer emits NoData at inactive cells, but zero at an
    active cell's face without an active neighbour. Only the bound IBOUND
    authorizes skipping that nonexistent opposite face, never NoData alone.
    """
    import numpy as np
    rr,cc=raster.indices(m['x'],m['y'],reference)
    current=raster.sample(rr,cc)*multiplier
    mr,mc=mask.indices(m['x'],m['y'],reference)
    activity=mask.sample(mr,mc)
    if np.any(activity==0):raise ValueError('BBC membership contains inactive model cells')
    inside=mc>0 if role=='frf' else mr>0
    selected=np.flatnonzero(inside)
    px=m['x'][inside]-(reference.dx if role=='frf' else 0)
    py=m['y'][inside]+(reference.dy if role=='fff' else 0)
    pr,pc=mask.indices(px,py,reference)
    neighbours=mask.sample(pr,pc)
    active=neighbours!=0
    previous=np.zeros(len(current),dtype='float64')
    # Do not read source NoData for an IBOUND=0 cell: the shared face is absent.
    sr,sc=raster.indices(px[active],py[active],reference)
    previous[selected[active]]=raster.sample(sr,sc)*multiplier
    # Closed right/front faces must be explicitly zero in the corrected source.
    forward_inside=mc+1<mask.nx if role=='frf' else mr+1<mask.ny
    closed=~forward_inside
    j=np.flatnonzero(forward_inside)
    fr,fc=mask.indices(m['x'][j]+(reference.dx if role=='frf' else 0),
                      m['y'][j]-(reference.dy if role=='fff' else 0),reference)
    closed[j]=mask.sample(fr,fc)==0
    if np.any(current[closed]!=0):raise ValueError('nonzero flux across a closed model face')
    values=current-previous
    # Independent HRU boundary sum: shared internal faces cancel exactly.
    owner=np.full((mask.ny,mask.nx),-1,dtype='int64');owner[mr,mc]=m['h']
    right_owner=np.full(len(mr),-1,dtype='int64')
    right_owner[j]=owner[mr[j]+(role=='fff'),mc[j]+(role=='frf')]
    left_owner=np.full(len(mr),-1,dtype='int64')
    left_owner[inside]=owner[mr[inside]-(role=='fff'),mc[inside]-(role=='frf')]
    boundary=np.where(right_owner!=m['h'],current,0)-np.where(left_owner!=m['h'],previous,0)
    n=len(m['domain'])
    sums=np.bincount(m['inv'],weights=values,minlength=n)
    edges=np.bincount(m['inv'],weights=boundary,minlength=n)
    error=float(abs(sums-edges).max())
    if error>1e-9*max(1,float(abs(values).sum())):raise ValueError('HRU lateral boundary cancellation failure')
    return values,dict(inactive_previous_faces=int((~active).sum()),
        outer_previous_faces=int((~inside).sum()),closed_forward_faces=int(closed.sum()),
        max_hru_boundary_difference_m3=error)


def acquire_lock(path):
    """OS-held lock: released automatically on termination, including Windows."""
    f=Path(path).open('a+b')
    try:
        f.seek(0,2)
        if f.tell()==0:f.write(b'0');f.flush()
        f.seek(0)
        if sys.platform=='win32':
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        return f
    except OSError as e:
        f.close();raise RuntimeError('another BBC producer owns this output directory') from e


def process(config, output):
    import numpy as np
    cfg = json.loads(Path(config).read_text(encoding='utf-8-sig'))
    timeline = list(days(cfg['start'],cfg['end']))
    if cfg.get('units') != 'm3/calendar_day' or cfg.get('positive') != 'into_layer1':
        raise ValueError('explicit source units/sign convention required')
    if cfg.get('source_semantics_profile')=='bbc07h-cell-net':
        raise ValueError('BBC08 CELL_NET profile is invalid for the identified saved-face sources; use BBC09')
    if set(cfg['sources']) != set(ROLES): raise ValueError('exactly five sources required')
    for role, spec in cfg['sources'].items():
        op = spec['spatial_operation']
        if op not in OPERATIONS or spec['positive_multiplier'] not in (-1,1):
            raise ValueError('invalid component operation/sign')
        if op != 'CELL_NET' and (role,op) not in (('frf','SAVED_CURRENT_MINUS_PREVIOUS_COLUMN'),('fff','SAVED_CURRENT_MINUS_PREVIOUS_ROW')):
            raise ValueError('operation incompatible with component')
    def source_path(role, day):
        return Path(cfg['sources'][role]['pattern'].replace('{date}',day.replace('-','')))
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    # A separate process must never share mutable production checkpoints.
    lock = output/'production.lock'
    handle=acquire_lock(lock)
    try:
        write_json(output/'run-status.json',dict(status='RUNNING',production_admitted=False))
        prior=json.loads((output/'manifest.json').read_text()) if (output/'manifest.json').exists() else {}
        (output/'manifest.json').unlink(missing_ok=True)
        (output/'transfer'/'transfer.json').unlink(missing_ok=True)
        reference = Raster(source_path('flf',timeline[0]))
        m = members(cfg['members'],reference,int(cfg['expected_hrus']))
        report=_process(cfg,config,output,timeline,m,reference,source_path,prior)
        write_json(output/'run-status.json',dict(status=report['status'],production_admitted=False,manifest_sha256=sha(output/'manifest.json')))
        return report
    except Exception as e:
        write_json(output/'run-status.json',dict(status='FAILED',error=str(e),production_admitted=False))
        raise
    finally: handle.close()


def _process(cfg,config,output,timeline,m,reference,source_path,prior):
    import numpy as np
    success = output/'manifest.json'; success.unlink(missing_ok=True)
    static = dict(config_sha256=sha(config),members_sha256=sha(cfg['members']),code_sha256=sha(__file__))
    needs_mask=any(s['spatial_operation']!='CELL_NET' for s in cfg['sources'].values())
    mask=None
    if needs_mask:
        binding=cfg.get('activity_mask',{})
        if not binding.get('path') or sha(binding['path'])!=binding.get('sha256'):
            raise ValueError('saved face processing requires hash-bound IBOUND')
        mask=Raster(binding['path']);static['activity_mask_sha256']=binding['sha256']
    old = output/'identity.json'
    if old.exists() and json.loads(old.read_text()) != static:
        raise ValueError('changed configuration/membership/code: choose a new output directory')
    write_json(old,static)
    mapping = 'cell_id,hru_id,row,col,area_m2\n' + ''.join(
        f'{r*reference.nx+c+1},{h},{r+1},{c+1},{reference.dx*reference.dy:.17g}\n'
        for r,c,h in zip(m['row'],m['col'],m['h']))
    atomic(output/'mapping.csv',mapping.encode())
    population='hru_id\n'+''.join(str(h)+'\n' for h in m['domain'])
    atomic(output/'population.csv',population.encode())
    records=[]; transfers=[]; reused=0
    for day in timeline:
        paths = {role:source_path(role,day) for role in ROLES}
        hashes = {role:dict(path=str(p),sha256=sha(p)) for role,p in paths.items()}
        cache = output/'daily'/(day+'.json'); values_path = cache.with_suffix('.npy')
        previous = json.loads(cache.read_text()) if cache.exists() else {}
        if previous.get('sources') == hashes and values_path.exists() and sha(values_path)==previous.get('values_sha256'):
            rec=previous; reused+=1
        else:
            sums=[]; geometry={}; source_totals={}; source_abs={}
            for role,path in paths.items():
                raster=Raster(path); rr,cc=raster.indices(m['x'],m['y'],reference)
                op=cfg['sources'][role]['spatial_operation']
                if op != 'CELL_NET':
                    v,face_audit=face_net(raster,mask,m,reference,role,cfg['sources'][role]['positive_multiplier'])
                else:
                    v=raster.sample(rr,cc)*cfg['sources'][role]['positive_multiplier'];face_audit=None
                sums.append(np.bincount(m['inv'],weights=v,minlength=len(m['domain'])))
                source_totals[role]=float(__import__('math').fsum(v)); source_abs[role]=float(np.abs(v).sum())
                geometry[role]=dict(geometry=raster.geometry,selected_cells=len(v),total_raster_cells=raster.nx*raster.ny,face_audit=face_audit)
                del raster
            if any(sha(paths[role]) != hashes[role]['sha256'] for role in ROLES):
                raise ValueError('source changed during processing: '+day)
            components=np.stack(sums,axis=1); q=components.sum(axis=1)
            for j,role in enumerate(ROLES):
                if abs(float(components[:,j].sum())-source_totals[role])>1e-10*max(1,source_abs[role]):
                    raise ValueError('volume conservation failure '+day+' '+role)
            cm=100*q/m['area']
            if not np.isfinite(cm).all() or np.any(abs(cm)>100): raise ValueError('QBOT2 outside SWAP range: '+day)
            values_path.parent.mkdir(parents=True,exist_ok=True)
            tmp=values_path.with_suffix('.partial')
            with tmp.open('wb') as f: np.save(f,components,allow_pickle=False)
            tmp.replace(values_path)
            rec=dict(date=day,sources=hashes,geometry=geometry,component_m3=source_totals,
                     values_sha256=sha(values_path),max_abs_cm_d=float(abs(cm).max()))
            write_json(cache,rec)
        # Exact existing D1 BBC shard contract, no second manual conversion.
        components=np.load(values_path,allow_pickle=False)
        if components.shape != (len(m['domain']),5):raise ValueError('invalid checkpoint shape')
        mm=1000*components/m['area'][:,None]
        header=['hru_id','date','area_m2']+[r+'_mm_d' for r in ROLES]+['q_ext_mm_d']
        lines=[','.join(header)]
        for i,h in enumerate(m['domain']):
            vals=[str(h),day,format(m['area'][i],'.17g')]+[format(v,'.17g') for v in mm[i]]+[format(mm[i].sum(),'.17g')]
            lines.append(','.join(vals))
        shard=output/'transfer'/(day+'.csv'); atomic(shard,('\n'.join(lines)+'\n').encode())
        transfers.append(dict(date=day,path=shard.name,sha256=sha(shard)))
        records.append(rec)
        print(day+' '+('REUSED' if rec is previous else 'PROCESSED'),flush=True)
    if needs_mask and sha(cfg['activity_mask']['path'])!=static['activity_mask_sha256']:
        raise ValueError('IBOUND changed during processing')
    # Transpose in bounded batches; keep at most 64 HRU output handles open.
    artifacts=[]
    reuse_bbc=(reused==len(timeline) and prior.get('identity')==static
        and [r['date'] for r in prior.get('daily',[])]==timeline
        and len(prior.get('bbc',[]))==len(m['domain'])
        and all(Path(a['path']).is_file() and sha(a['path'])==a['sha256'] for a in prior.get('bbc',[])))
    if reuse_bbc:artifacts=prior['bbc']
    for lo in ([] if reuse_bbc else range(0,len(m['domain']),64)):
        hi=min(lo+64,len(m['domain'])); writers=[]; targets=[]
        try:
            for h in m['domain'][lo:hi]:
                p=output/'bbc'/f'HRU_{h:05d}.bbc';p.parent.mkdir(exist_ok=True)
                targets.append(p); f=p.with_suffix('.partial').open('w',encoding='ascii',newline='\n');writers.append(f)
                f.write('! LWKM_OWNER_DAILY_MEAN_NODES_20261020\nSWBOTB=2\nSW2=2\nDATE2 QBOT2\n')
            for day in timeline:
                data=np.load(output/'daily'/(day+'.npy'),allow_pickle=False,mmap_mode='r')
                cm=100*data[lo:hi].sum(axis=1)/m['area'][lo:hi]
                for f,v in zip(writers,cm):
                    token=format(v,'.17g')
                    if '.' not in token and 'e' not in token.lower():token+='.'
                    f.write(day+' '+token+'\n')
            for f in writers:f.write('* End of table\n');f.close()
            for p in targets:
                p.with_suffix('.partial').replace(p)
                artifacts.append(dict(hru_id=int(p.stem.split('_')[1]),path=str(p),sha256=sha(p)))
        finally:
            for f in writers:f.close()
    report=dict(schema_version=1,producer_version='BBC09',spatial_operations={r:s['spatial_operation'] for r,s in cfg['sources'].items()},status='BBC_SOURCE_CANDIDATE_NOT_SWAP_VALIDATED',production_admitted=False,
        identity=static,start=timeline[0],end=timeline[-1],days=len(timeline),reused_days=reused,
        svats=m['svats'],physical_cells=len(m['h']),hrus=len(m['domain']),
        full_cell_area_m2=reference.dx*reference.dy,area_m2=float(m['area'].sum()),bbc_reused=bool(reuse_bbc),
        mapping_sha256=sha(output/'mapping.csv'),daily=records,bbc=artifacts,
        timing='owner accepted daily nodes; SWAP interpolation may change daily integrated volumes')
    write_json(success,report)
    atomic(output/'transfer'/'source-manifest.json',success.read_bytes())
    write_json(output/'transfer'/'transfer.json',dict(schema_version=1,product_kind='BBC',
        dataset_id='BBC09_NET_FIVE_COMPONENT_DAILY',population_sha256=sha(output/'population.csv'),
        source_manifest_sha256=sha(success),source_manifest_path='source-manifest.json',
        producer_sha256=sha(__file__),units='mm/day_positive_into_L1',start=timeline[0],end=timeline[-1],
        hru_ids=[int(h) for h in m['domain']],status='RESEARCH_CANDIDATE',files=transfers))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe',action='store_true');p.add_argument('--config',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.probe:
        try:
            import numpy
            print(json.dumps(dict(python=sys.version,executable=sys.executable,numpy=numpy.__version__)))
            return 0
        except ImportError as e: print(str(e),file=sys.stderr);return 2
    if not a.config or not a.output:p.error('--config and --output required')
    try:
        r=process(a.config,a.output)
        print(json.dumps({k:r[k] for k in ('status','days','reused_days','physical_cells','hrus')}));return 0
    except Exception as e:
        print('BBC ERROR: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
