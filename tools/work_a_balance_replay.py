"""Reproduce earlier balance diagnostic, retaining its zero-default limitations."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.idf_reader import read_idf
from tools.modflow_daily_rasters import mosaic,into_cell_from_faces
from tools.run_dra_protected_population import atomic_json
from tools.assemble_swap_package import sha256


def replay(root,output):
    head=read_idf(next(root.glob('*head_next_midnight*')));h=head.values.astype(float)
    active=np.isfinite(h)&(h!=head.nodata)
    def term(name):return np.nan_to_num(mosaic(sorted(root.glob(name+'*')),head),nan=0.)
    right,front=term('bdgfrf'),term('bdgfff');lat=into_cell_from_faces(right,front)
    flf,wel,sto,bnd=[term(n) for n in ['bdgflf','bdgwel','bdgsto','bdgbnd']]
    drn=sum(term('bdgdrn_sys'+str(i)) for i in range(1,4));riv=sum(term('bdgriv_sys'+str(i)) for i in range(1,5))
    def cropped(name):
        g=read_idf(root/name);c=int(round((head.xmin-g.xmin)/g.dx));r=int(round((g.ymax-head.ymax)/g.dy))
        a=g.values[r:r+head.nrow,c:c+head.ncol].astype(float);return np.where(a==g.nodata,np.nan,a)
    cond=cropped('ghb_cond_l1.idf');external=cropped('ghb_head_l1.idf')
    ghb=np.where((cond>0)&np.isfinite(external)&active,cond*(external-h),0.)
    coupling=read_idf(root/'LWKM_MetaSWAP_coupling_L1_1124x1300.idf').values
    rows=[]
    for variant,q in [('saved_sign_hypothesis',wel+drn+riv+bnd+sto+flf-lat+ghb),('standard_native_sign_hypothesis',wel+drn+riv+bnd+sto-flf+lat+ghb)]:
        for group,mask in [('outside_metaswap',active&(coupling==0)),('inside_metaswap',active&(coupling==1))]:
            a=q[mask];rows.append(dict(variant=variant,group=group,count=len(a),sum_m3_d=float(a.sum()),mae_m3_d=float(abs(a).mean()),rmse_m3_d=float(np.sqrt(np.mean(a*a))),max_abs_m3_d=float(abs(a).max())))
    report=dict(results=rows,production_admitted=False,code_sha256=sha256(Path(__file__)),input_sha256={p.name:sha256(p) for p in root.iterdir() if p.is_file()},
        caveats=['Historical zero-default package semantics replayed only for diagnostic comparison','Estimated WEL','GHB from end-midnight head, not original integrated budget','Original LIST/control-time validation still required'])
    atomic_json(output,report);print(json.dumps(report));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();replay(a.root,a.output)
