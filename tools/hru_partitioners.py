"""Partitioner backends for HRU clustering."""
from __future__ import annotations
import csv,subprocess,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from tools.hru_clustering import robust_scale

class RScclustPartitioner:
    """Compatibility backend using the historical R scclust package."""
    def __init__(self,rscript="Rscript"): self.rscript=rscript
    def __call__(self,group:pd.DataFrame,min_size:int)->np.ndarray:
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); inp=td/"input.csv"; out=td/"labels.csv"; script=td/"run.R"
            x=pd.DataFrame({"GHG":robust_scale(group["GHG_LHM43"]),
                            "NettoKwel":robust_scale(group["NettoKwel_LHM43"])})
            x.to_csv(inp,index=False)
            script.write_text(r'''
args <- commandArgs(trailingOnly=TRUE)
suppressPackageStartupMessages(library(scclust))
suppressPackageStartupMessages(library(distances))
x <- read.csv(args[1])
d <- distances(x, dist_variables=c("GHG","NettoKwel"), id_variable=NULL, normalize=NULL, weights=NULL)
cl <- sc_clustering(d, size_constraint=as.integer(args[3]))
write.csv(data.frame(cluster=as.integer(cl)), args[2], row.names=FALSE)
''',encoding="utf-8")
            p=subprocess.run([self.rscript,str(script),str(inp),str(out),str(int(min_size))],
                             text=True,capture_output=True)
            if p.returncode:
                raise RuntimeError("R scclust backend failed: "+p.stderr[-2000:])
            labels=pd.read_csv(out)["cluster"].to_numpy(int)
            if len(labels)!=len(group):raise RuntimeError("R scclust returned wrong label count")
            return labels

class NativePartitionerUnavailable:
    def __call__(self,group,min_size):
        raise NotImplementedError("Native scclust-equivalent partitioner is not admitted; use RScclustPartitioner for historical compatibility.")
