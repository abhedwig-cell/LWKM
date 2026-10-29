"""One-time extraction of independent lookup sheets; never reads Runs.

Needs openpyxl only in the preparation environment, not on the NHI server.
"""
import argparse
from datetime import date,datetime
import gzip
import hashlib
import json
from pathlib import Path

SHEETS=('discretisatie','DZNEW','eigenschappen','Gewasrotatie','Gewasweerstand')


def main():
    import openpyxl
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('workbook',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();book=openpyxl.load_workbook(a.workbook,read_only=True,data_only=True)
    tables={}
    for name in SHEETS:
        it=iter(book[name].values);headers=next(it)
        records=[dict(zip(headers,row)) for row in it if row[0] is not None]
        if name in ('discretisatie','DZNEW'):records=[r for r in records if r['dikte_id']==1700]
        for r in records:
            for key,v in r.items():
                if isinstance(v,(date,datetime)):r[key]=v.isoformat()[:10]
        tables[name]=records
    book.close()
    data=dict(source_sha256=hashlib.sha256(a.workbook.read_bytes()).hexdigest(),tables=tables)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(gzip.compress(json.dumps(data,separators=(',',':'),allow_nan=False).encode(),mtime=0))


if __name__=='__main__':main()
