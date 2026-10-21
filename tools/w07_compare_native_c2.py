"""Compare NHI native DRA output to C2 baseline, with explicit exceptions.

Never declare exact parity based only on syntactic presence. Baseline filenames are
<HRU>.dra. The native run may legitimately approximate the 29 old blockers,
which must be audited separately rather than called baseline mismatches.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path

KEY=re.compile(r'^\s*(DRARES|INFRES|SWALLO|L|ZBOTDR|SWDTYP)(\d+)\s*=\s*(\S+)',re.I)
HEADER=re.compile(r'^\s*NRLEVS\s*=\s*(\d+)',re.I)

def read(path):
    data=path.read_bytes()
    values={};levels=None
    for line in data.decode('utf-8-sig').splitlines():
        m=HEADER.match(line)
        if m: levels=int(m.group(1))
        m=KEY.match(line)
        if m:
            if (m.group(1).upper(),int(m.group(2))) in values:
                raise ValueError('duplicate key in '+str(path))
            values[(m.group(1).upper(),int(m.group(2)))]=float(m.group(3))
    if levels is None or not 1<=levels<=5: raise ValueError('invalid NRLEVS '+str(path))
    required={(name,i) for name in ('DRARES','INFRES','SWALLO','L','ZBOTDR','SWDTYP') for i in range(1,levels+1)}
    if set(values)!=required:raise ValueError('missing/extra DRA level parameters '+str(path))
    return data,levels,values

def compare(native,baseline,report,expected=10242,atol=1e-7):
    reference={int(p.stem):p for p in baseline.glob('*.dra') if p.stem.isdigit()}
    candidate={int(p.stem):p for p in native.glob('*.dra') if p.stem.isdigit()}
    ids=sorted(set(reference)|set(candidate))
    rows=[]
    for h in ids:
        rec=dict(hru=h,has_native=h in candidate,has_c2=h in reference,status='UNKNOWN')
        try:
            if h not in candidate:
                rec['status']='MISSING_NATIVE'
            elif h not in reference:
                read(candidate[h]);rec['status']='NEW_CANDIDATE_NO_C2_BASELINE'
            else:
                a,na,va=read(candidate[h]);b,nb,vb=read(reference[h])
                if a==b:rec['status']='BYTE_IDENTICAL'
                elif na!=nb or set(va)!=set(vb):
                    rec['status']='STRUCTURE_DIFFERENCE'
                else:
                    diff=max(abs(va[k]-vb[k]) for k in va)
                    rec['maximum_parameter_absolute_difference']=diff
                    rec['status']='NUMERIC_EQUAL_TEXT_DIFFERENT' if diff<=atol else 'HYDRAULIC_PARAMETER_DIFFERENCE'
                rec['native_sha256']=hashlib.sha256(a).hexdigest()
                rec['c2_sha256']=hashlib.sha256(b).hexdigest()
        except (ValueError,UnicodeError) as e:
            rec.update(status='INVALID_DRA',error=str(e))
        rows.append(rec)
    histogram={}
    for x in rows:histogram[x['status']]=histogram.get(x['status'],0)+1
    result=dict(schema_version=1,expected_population=expected,native_count=len(candidate),
        c2_count=len(reference),represented_population=len(candidate),
        qualification='NOT_ADMITTED',counts=histogram,rows=rows)
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--native',required=True,type=Path)
    ap.add_argument('--c2',required=True,type=Path)
    ap.add_argument('--report',required=True,type=Path)
    a=ap.parse_args()
    result=compare(a.native,a.c2,a.report)
    print(json.dumps({k:result[k] for k in ('native_count','c2_count','counts')}))
    return 0 if result['native_count']==10242 and result['counts'].get('INVALID_DRA',0)==0 else 1
if __name__=='__main__':raise SystemExit(main())
