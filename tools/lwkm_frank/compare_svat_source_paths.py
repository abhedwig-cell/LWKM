"""Read-only comparison of MetaSWAP INP and SVAT_BORDER model inputs.

A matching SHA256 proves identical bytes, not historical execution identity.
Run with Deltaforge Python 3.8+ on NHI Windows server.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

FILES=("area_svat.inp","mod2svat.inp","scap_svat.inp","dldra_svat.inp",
       "dqsat_svat.inp","idf_svat.inp","sel_svat.inp","uscl_svat.inp",
       "svat2precgrid.inp","svat2etrefgrid.inp")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda:src.read(8*1024*1024),b""):h.update(block)
    return h.hexdigest()

def inspect(root,names=FILES):
    rows=[]
    for name in names:
        a,b=root/"inp"/name,root/"svat_border"/name
        a_ok,b_ok=a.is_file(),b.is_file()
        ah=sha(a) if a_ok else ""; bh=sha(b) if b_ok else ""
        state=("BYTE_IDENTICAL" if ah and bh and ah==bh else
               "DIFFERENT_BYTES_REVIEW_REQUIRED" if ah and bh else
               "MISSING_COMPARISON")
        rows.append(dict(file=name,inp_path=str(a),inp_exists=int(a_ok),
                         inp_size=a.stat().st_size if a_ok else "",inp_sha256=ah,
                         border_path=str(b),border_exists=int(b_ok),
                         border_size=b.stat().st_size if b_ok else "",
                         border_sha256=bh,result=state))
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path(r"E:\LHM_4.3.3\Data\2_Model_Input\metaswap"))
    p.add_argument("--output",type=Path,default=Path(r"G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM_LHM_RunDef_resultaten_v01"))
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    rows=inspect(a.root)
    with (a.output/"lhm_svat_path_comparison.csv").open("w",newline="",encoding="utf8") as out:
        w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    counts={label:sum(row["result"]==label for row in rows) for label in
            ("BYTE_IDENTICAL","DIFFERENT_BYTES_REVIEW_REQUIRED","MISSING_COMPARISON")}
    (a.output/"lhm_svat_path_comparison.json").write_text(json.dumps(
        {"status":"INPUT_IDENTITY_NOT_EXECUTION_PROOF","counts":counts,"root":str(a.root)},
        indent=2),encoding="utf8")
    for row in rows:print(row["file"],row["result"])
    print("CONTROLE:",counts)
    return 1 if counts["DIFFERENT_BYTES_REVIEW_REQUIRED"] or counts["MISSING_COMPARISON"] else 0
if __name__=="__main__":raise SystemExit(main())
