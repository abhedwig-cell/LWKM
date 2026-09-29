"""Reader for the realized Deltares IDF variant used by P12 inputs."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct
import numpy as np

@dataclass(frozen=True)
class IDF:
    values: np.ndarray
    ncol:int; nrow:int
    xmin:float; xmax:float; ymin:float; ymax:float
    dx:float; dy:float
    nodata:float

def read_idf(path:Path)->IDF:
    with path.open("rb") as f:
        header=f.read(52)
        if len(header)!=52: raise ValueError("short IDF header")
        rec,ncol,nrow,xmin,xmax,ymin,ymax,vmin,vmax,nodata,reserved,dx,dy=struct.unpack("<3i10f",header)
        expected=52+ncol*nrow*4
        if path.stat().st_size!=expected:
            raise ValueError(f"unsupported IDF layout/size: expected {expected}, got {path.stat().st_size}")
        values=np.fromfile(f,dtype="<f4",count=ncol*nrow).reshape(nrow,ncol)
    return IDF(values,ncol,nrow,xmin,xmax,ymin,ymax,dx,dy,nodata)

def row_col(grid:IDF,x:float,y:float)->tuple[int,int]:
    col=int((x-grid.xmin)//grid.dx)
    row=int((grid.ymax-y)//grid.dy)
    if not (0<=row<grid.nrow and 0<=col<grid.ncol):
        raise IndexError((x,y,row,col))
    return row,col
