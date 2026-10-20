"""Receive lossless selected native HRU decades, preserving original source markers.

Integrity is separate from semantic review. No population/annual reconstruction.
"""
import argparse
import csv
import json
from pathlib import Path
import re
import shutil
import tempfile
import numpy as np
import pandas as pd
from tools.execute_swap_candidate import digest
from tools.et_calibration import RAW,PARAMETERS,decade,load_reference,select_profile,write_json
from tools.production_transfer import relative


def calendar_ends(start,end):
    a,b=pd.Timestamp(start),pd.Timestamp(end)
    if a!=decade(a)[0] or b!=decade(b)[1] or a>b:raise ValueError('whole calendar decades required')
    return [d.strftime('%Y%m%d') for d in pd.date_range(a,b) if d==decade(d)[1]]


def marker_output(path):
    lines=path.read_text().splitlines()
    values=[line[7:] for line in lines if line.startswith('output=')]
    if len(values)!=1 or not re.fullmatch('[a-f0-9]{64}',values[0]):raise ValueError('unique valid output hash required')
    return values[0]


def validate_rows(rows,ids,days):
    seen=set();incomplete=0
    for row in rows:
        hid=int(row['hru_id'])
        if str(hid)!=row['hru_id'] or hid in seen:raise ValueError('invalid/duplicate HRU')
        seen.add(hid)
        if float(row['days'])!=days:raise ValueError('wrong decade length')
        if row['complete'] not in ('0','1'):raise ValueError('invalid complete flag')
        full=True
        for name in RAW:
            cover=float(row['coverage_'+name])
            if not np.isfinite(cover) or not 0<=cover<=1:raise ValueError('coverage outside [0,1]')
            value=row[name]
            if cover==1:
                if value=='' or not np.isfinite(float(value)):raise ValueError('complete value missing/nonfinite')
            else:
                full=False
                if value!='':raise ValueError('incomplete source must not be renormalized or filled')
        if (row['complete']=='1')!=full:raise ValueError('complete flag contradicts coverage')
        if not full:incomplete+=1
    if seen!=set(ids):raise ValueError('missing/extra selected HRUs')
    return incomplete


def receive(source,destination,ids,start,end,*,data_origin):
    source,destination=Path(source),Path(destination)
    if data_origin not in ('synthetic','real_unreviewed'):raise ValueError('explicit data origin required')
    if ids!=sorted(set(ids)) or any(type(i)!=int or i<=0 for i in ids):raise ValueError('sorted unique positive HRUs required')
    if not ids:raise ValueError('empty HRUs')
    dates=calendar_ends(start,end)
    support=source/'hru_support.csv';sf=pd.read_csv(support)
    if sf.hru_id.duplicated().any() or not set(ids)<=set(sf.hru_id):raise ValueError('support population mismatch')
    if not np.isfinite(sf.area_m2).all() or (sf.area_m2<=0).any():raise ValueError('invalid area support')
    support_hash=digest(support)
    identity={'source_support_sha256':support_hash,'hru_ids':ids,'start':start,'end':end,
              'data_origin':data_origin,'code_sha256':digest(__file__)}
    destination.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='et-receipt-',dir=destination.parent))
    try:
        files=[];bad=0
        shutil.copyfile(support,temp/'hru_support.csv')
        for date in dates:
            path=source/(date+'.csv');marker=source/(date+'.sha256')
            original_hash=digest(path);marker_hash=digest(marker)
            if original_hash!=marker_output(marker):raise ValueError('native source hash mismatch: '+date)
            selected=[];all_ids=set()
            with path.open(newline='') as inp:
                reader=csv.DictReader(inp);columns=reader.fieldnames
                if not {'hru_id','days','complete',*RAW,*['coverage_'+n for n in RAW]}<=set(columns or []):raise ValueError('native HRU-decade columns required')
                for row in reader:
                    hid=int(row['hru_id'])
                    if hid in all_ids:raise ValueError('duplicate source HRU')
                    all_ids.add(hid)
                    if hid in ids:selected.append(row)
            if all_ids!=set(sf.hru_id):raise ValueError('native population differs from support')
            selected.sort(key=lambda r:int(r['hru_id']))
            a,b=decade(pd.to_datetime(date,format='%Y%m%d'))
            bad+=validate_rows(selected,ids,(b-a).days+1)
            target=temp/path.name
            with target.open('w',newline='') as out:
                writer=csv.DictWriter(out,fieldnames=columns);writer.writeheader();writer.writerows(selected)
            shutil.copyfile(marker,temp/(date+'.source.sha256'))
            (temp/(date+'.sha256')).write_text('output='+digest(target)+'\nparent_output='+original_hash+'\n')
            if digest(path)!=original_hash or digest(marker)!=marker_hash:raise ValueError('source changed during reception')
            files.append({'date':date,'path':target.name,'sha256':digest(target),'source_output_sha256':original_hash,
                          'source_marker_sha256':marker_hash})
        if digest(support)!=support_hash:raise ValueError('support changed during reception')
        hashes={p.name:digest(p) for p in temp.iterdir()}
        receipt={**identity,'schema_version':1,'product_kind':'SELECTED_NATIVE_HRU_DECADES',
                 'status':'STRUCTURALLY_VERIFIED_CANDIDATE','units_review':'PENDING',
                 'scientific_reference_qualified':False,'production_admitted':False,
                 'decades':len(dates),'incomplete_hru_decades':bad,'files':files,'hashes':hashes}
        write_json(temp/'receipt.json',receipt)
        if destination.exists():
            previous=verify(destination)
            if previous!=receipt:raise ValueError('different immutable receipt; use a new destination')
            return {**receipt,'reused':True}
        temp.rename(destination)
        return {**receipt,'reused':False}
    finally:
        if temp.exists():shutil.rmtree(temp)


def verify(directory):
    directory=Path(directory);r=json.loads((directory/'receipt.json').read_text())
    if r.get('schema_version')!=1 or r.get('product_kind')!='SELECTED_NATIVE_HRU_DECADES':raise ValueError('unsupported receipt')
    if r.get('production_admitted') is not False or r.get('scientific_reference_qualified') is not False:raise ValueError('receipt cannot grant scientific admission')
    dates=calendar_ends(r['start'],r['end'])
    if [x['date'] for x in r['files']]!=dates or r['decades']!=len(dates):raise ValueError('receipt calendar differs')
    expected={'hru_support.csv'}|{d+suffix for d in dates for suffix in ('.csv','.sha256','.source.sha256')}
    if set(r['hashes'])!=expected:raise ValueError('receipt assets incomplete')
    for name,h in r['hashes'].items():
        if digest(relative(directory,name))!=h:raise ValueError('receipt asset changed: '+name)
    for item in r['files']:
        date=item['date']
        if item['path']!=date+'.csv' or item['sha256']!=r['hashes'][date+'.csv']:raise ValueError('receipt file binding differs')
        if item['source_marker_sha256']!=r['hashes'][date+'.source.sha256']:raise ValueError('source marker binding differs')
        if marker_output(directory/(date+'.source.sha256'))!=item['source_output_sha256']:raise ValueError('parent output binding differs')
    if digest(directory/'hru_support.csv')!=r['source_support_sha256']:raise ValueError('support identity differs')
    return r


def reference(directory,hru,review):
    """A review is bound to this exact receipt; transport never fabricates it."""
    directory=Path(directory);r=verify(directory)
    review=json.loads(Path(review).read_text())
    required={'unit':'mm/calendar_decade','sign':'positive_loss_or_gift','period':'calendar_decade_amount'}
    if review.get('receipt_sha256')!=digest(directory/'receipt.json') or review.get('status')!='SEMANTICS_REVIEWED':raise ValueError('review not bound to received data')
    if not review.get('evidence_refs') or not all(review.get(k)==v for k,v in required.items()):raise ValueError('source semantics evidence required')
    if hru not in r['hru_ids']:raise ValueError('HRU outside received selection')
    frame=load_reference(directory,hru,semantic_qualified=True)
    frame.attrs.update(data_origin=r['data_origin'],receipt_sha256=digest(directory/'receipt.json'))
    return frame


def select_received(directory,hru,review,candidates,train_years,validation_years,context_review=None):
    frame=reference(directory,hru,review)
    context_ok=False
    if context_review is not None:
        c=json.loads(Path(context_review).read_text())
        context_ok=(c.get('status')=='HYDROLOGY_MANAGEMENT_REVIEWED' and c.get('hru_id')==hru
                    and c.get('receipt_sha256')==frame.attrs['receipt_sha256'] and bool(c.get('evidence_refs')))
    result=select_profile(candidates,frame,train_years,validation_years,
                          real_reference=frame.attrs['data_origin']=='real_unreviewed',context_verified=context_ok)
    result.update(receipt_sha256=frame.attrs['receipt_sha256'],data_origin=frame.attrs['data_origin'])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('receive')
    for n in ['source','destination']:a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--hru-ids',type=int,nargs='+',required=True)
    for n in ['start','end']:a.add_argument('--'+n,required=True)
    a.add_argument('--data-origin',choices=['synthetic','real_unreviewed'],required=True)
    b=s.add_parser('verify');b.add_argument('--directory',type=Path,required=True)
    c=s.add_parser('extract');c.add_argument('--directory',type=Path,required=True);c.add_argument('--hru',type=int,required=True);c.add_argument('--review',type=Path,required=True);c.add_argument('--output',type=Path,required=True)
    d=s.add_parser('select');d.add_argument('--directory',type=Path,required=True);d.add_argument('--hru',type=int,required=True)
    for name in ('review','manifest','output'):d.add_argument('--'+name,type=Path,required=True)
    d.add_argument('--context-review',type=Path)
    args=p.parse_args()
    if args.command=='receive':print(json.dumps(receive(args.source,args.destination,args.hru_ids,args.start,args.end,data_origin=args.data_origin)))
    elif args.command=='verify':print(json.dumps(verify(args.directory)))
    elif args.command=='extract':reference(args.directory,args.hru,args.review).to_csv(args.output,index=False)
    else:
        cfg=json.loads(args.manifest.read_text());candidates={tuple(r['parameters'][n] for n in PARAMETERS):pd.read_csv(r['csv']) for r in cfg['candidates']}
        write_json(args.output,select_received(args.directory,args.hru,args.review,candidates,cfg['train_years'],cfg['validation_years'],args.context_review))

if __name__=='__main__':main()
