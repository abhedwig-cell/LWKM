"""Replay the identified corrected producer once and verify BBC09 face assembly.

No new reconstruction method. Source archive, original head archive and actual
BBC08 server export are supplied by the caller. Does not admit historical runs.
"""
import argparse,csv,hashlib,io,json,struct,zipfile
from pathlib import Path
import numpy as np
from tools.server.bbc_production import Raster,members,face_net,sha,write_json


def raw_grid(data):
    nx,ny=struct.unpack_from('<2i',data,4)
    return np.frombuffer(data,dtype='<f4',offset=52,count=nx*ny).reshape(ny,nx),data[:52]


def qualify(producer,head_archive,mapping,control,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    z=zipfile.ZipFile(producer);ib,header=raw_grid(z.read('IBOUND_L1.IDF'));kd,_=raw_grid(z.read('kdw_L1.IDF'))
    archive=zipfile.ZipFile(head_archive)
    name=next(n for n in archive.namelist() if 'head_start__head_20200701000000_l1' in n)
    h,_=raw_grid(archive.read(name));heads=np.zeros_like(ib);heads[:,:h.shape[1]]=h
    nd=struct.unpack_from('<f',header,36)[0]
    active=np.isfinite(ib)&(ib!=nd)&(ib!=0)&(abs(ib)<1e19)
    maskpath=output/'IBOUND_L1.IDF';maskpath.write_bytes(z.read('IBOUND_L1.IDF'));mask=Raster(maskpath)
    ref=output/'reference.idf';ref.write_bytes(archive.read(next(n for n in archive.namelist() if 'bdgflf__' in n)))
    reference=Raster(ref);m=members(mapping,reference,10242)
    controlzip=zipfile.ZipFile(control);manifest=json.loads(controlzip.read('manifest.json'))
    rows=list(csv.DictReader(io.StringIO(controlzip.read('transfer\\2020-07-01.csv').decode())))
    rows=sorted(rows,key=lambda r:int(r['hru_id']))
    result={};new=[];old=[]
    for role,axis in [('frf',1),('fff',0)]:
        a=(kd[:,:-1] if axis==1 else kd[:-1,:]).astype(float)
        b=(kd[:,1:] if axis==1 else kd[1:,:]).astype(float)
        valid=(active[:,:-1]&active[:,1:]) if axis==1 else (active[:-1,:]&active[1:,:])
        conduct=np.zeros_like(a);conduct[valid]=2*a[valid]*b[valid]/(a[valid]+b[valid])
        # Match the float subtraction in the archived C# implementation.
        difference=(heads[:,1:]-heads[:,:-1]) if axis==1 else (heads[1:,:]-heads[:-1,:])
        source=np.zeros_like(ib)
        if axis==1:source[:,:-1]=(conduct*difference).astype('<f4')
        else:source[:-1,:]=(conduct*difference).astype('<f4')
        nodata=np.float32(1e20);source[~active]=nodata;good=active
        hdr=bytearray(header);struct.pack_into('<3f',hdr,28,float(source[good].min()),float(source[good].max()),float(nodata))
        path=output/(role+'.idf');path.write_bytes(hdr+source.tobytes());raster=Raster(path)
        r,c=raster.indices(m['x'],m['y'],reference)
        stored=raster.sample(r,c)
        direct=np.bincount(m['inv'],weights=stored,minlength=10242)
        actual=np.array([float(r[role+'_mm_d'])*float(r['area_m2'])/1000 for r in rows])
        difference=float(abs(direct-actual).max())
        if difference>1e-8:raise AssertionError('identified producer does not match server HRU values')
        values,audit=face_net(raster,mask,m,reference,role,1)
        # Independent whole-model divergence, with zeros only at verified inactive cells.
        whole=np.where(active,source,0.).astype(float);previous=np.zeros_like(whole)
        if axis==1:previous[:,1:]=whole[:,:-1]
        else:previous[1:,:]=whole[:-1,:]
        expected=(whole-previous)[r,c]
        if not np.array_equal(values,expected):raise AssertionError('independent cell divergence differs')
        summed=np.bincount(m['inv'],weights=values,minlength=10242)
        new.append(1000*summed/m['area']);old.append(1000*direct/m['area'])
        result[role]=dict(server_sha256=manifest['daily'][0]['sources'][role]['sha256'],
            replay_sha256=sha(path),byte_identical=sha(path)==manifest['daily'][0]['sources'][role]['sha256'],
            max_hru_saved_face_match_m3=difference,selected_saved_face_m3=float(direct.sum()),
            selected_net_m3=float(summed.sum()),independent_cell_difference_m3=float(abs(values-expected).max()),
            face_audit=audit)
    delta=new[0]+new[1]-old[0]-old[1]
    result=dict(status='BBC09_REAL_SOURCE_FACE_ASSEMBLY_CHECK',production_admitted=False,
        sources={str(p):sha(p) for p in [producer,head_archive,mapping,control]},hrus=10242,physical_cells=len(m['h']),
        components=result,max_abs_bbc08_correction_mm_d=float(abs(delta).max()),
        limitations=['one real source day, not full server period','FRF byte hash differs outside or within unobserved per-cell detail; HRU saved-face sums all match','no modern full SWAP package executed'])
    write_json(output/'summary.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['producer','head-archive','mapping','control','output']:p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();print(json.dumps(qualify(a.producer,a.head_archive,a.mapping,a.control,a.output),indent=2))
