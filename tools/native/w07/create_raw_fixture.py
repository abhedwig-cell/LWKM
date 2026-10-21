"""Create a tiny original-format LHM source fixture for native W07 Windows CI."""
from pathlib import Path
import struct,json
root=Path("w07-raw-fixture")
root.mkdir(exist_ok=True)
def grid(name,value):
    header=struct.pack("<3i10f",1271,2,2,0,500,0,500,value,value,-9999,0,250,250)
    (root/name).write_bytes(header+struct.pack("<4f",*[float(value)]*4))
def asc(name,value):
    (root/name).write_text("ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n"+" ".join([str(value)]*4)+"\n")
def raw():
    (root/"members.csv").write_text("svat,hru,x,y\n1,4015,125,375\n")
    (root/"dqsat.csv").write_text("hru,representative_dqsat\n4015,10\n")
    swp=root/"swps"/"run_04015"
    swp.mkdir(parents=True,exist_ok=True)
    swp.joinpath("swap.swp").write_text("ORES OSAT ALFA NPAR KSATFIT LEXP H_ENPR KSATEXM BDENS ELAS\\n"+"0.1 0.4 0.01 1.5 10 0.5 0 10 1.3 1\\n"*4+"* End of table\\n")
    asc("ahn_f250_cm.asc",150)
    cfg={"members_csv":str(root/"members.csv"),"dqsat_csv":str(root/"dqsat.csv"),"swp_root":str(root/"swps"),
         "ground_asc":str(root/"ahn_f250_cm.asc"),"start_year":1971,"end_year":1972,"H1_stage_start":"1971-01-01","H1_stage_end":"1971-02-01"}
    for name in ("H1","P","S","T","MVG","PIPE","OLF"):
        key=name+"_cdr";grid(key+".idf",100 if name=="H1" else 50);cfg[key]=str(root/(key+".idf"))
        if name in ("P","S","T"):
            for suff,depth in (("bottom_sum",.5),("bottom_win",.6),("sum",.7),("win",.8)):
                key=name+"_"+suff;grid(key+".idf",depth);cfg[key]=str(root/(key+".idf"))
        else:
            key=name+"_bottom";grid(key+".idf",.5);cfg[key]=str(root/(key+".idf"))
        if name in ("H1","P","S","T"):
            key=name+"_inf";grid(key+".idf",.1);cfg[key]=str(root/(key+".idf"))
    months=root/"months";months.mkdir(exist_ok=True)
    grid("months/peilh_19710101.idf",.8)
    grid("months/peilh_19710201.idf",.9)
    cfg["H1_monthly_dir"]=str(months)
    (root/"raw_config.json").write_text(json.dumps(cfg,indent=2)+"\n")
raw()
