"""Profile-specific SWAP 4.3.1 package closure and calendar preflight.

Not a replacement for SWAP's parser or scientific source admission. Activates
references by switches, follows crop/CO2 dependencies, and checks period support.
"""
from datetime import date,timedelta
from pathlib import Path
import re
import numpy as np
import pandas as pd
from tools.swp_full_oracle import parse_assignments,parse_named_table
from tools.swp_template_adapter import TABLE_HEADERS


def scalar(text,key,default=None):
    v=parse_assignments(text).get(key,[])
    if not v:
        if default is not None:return default
        raise ValueError('missing '+key)
    if len(v)!=1:raise ValueError('duplicate '+key)
    return v[0]


def safe_name(value,extension=''):
    value=str(value)
    if not value or re.search(r'[/\\:]',value) or value in ('.','..'):
        raise ValueError('unsafe asset reference')
    return value+extension


def date_value(s):
    try:return date.fromisoformat(s)
    except ValueError:
        day,mon,year=s.split('-');months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
        return date(int(year),months.index(mon.lower())+1,int(day))


def dated_table(text,header,*,daily_steps=False):
    rows=parse_named_table(text,header)
    dates=[date_value(str(r[0])) for r in rows]
    if not dates:raise ValueError('unordered/missing dates: '+header)
    if daily_steps:
        if len(rows)%2:raise ValueError('incomplete BBC daily step')
        for i in range(0,len(rows),2):
            if len(rows[i])!=2 or len(rows[i+1])!=2 or dates[i+1]!=dates[i]+timedelta(days=1) or float(rows[i][1])!=float(rows[i+1][1]):
                raise ValueError('invalid BBC daily step')
            if i and dates[i]!=dates[i-1]:raise ValueError('BBC daily step gap/overlap')
    elif dates!=sorted(set(dates)):raise ValueError('unordered/missing dates: '+header)
    if not np.isfinite(np.array([r[1:] for r in rows],dtype=float)).all():raise ValueError('nonfinite table: '+header)
    return dates,rows


def validate(directory):
    root=Path(directory);swp=(root/'swap.swp').read_text();start=date_value(str(scalar(swp,'TSTART')));end=date_value(str(scalar(swp,'TEND')))
    if end<start:raise ValueError('reversed simulation period')
    # Fail closed for profiles whose external dependencies are not implemented.
    for key,allowed,default in [('SWDRA',(0,1),0),('SWINCO',(1,2),2),
            ('SWBBCFILE',(0,1),0),('SWSOPHY',(0,),0),('SWSOLU',(0,),0)]:
        if int(scalar(swp,key,default)) not in allowed:
            raise ValueError('unsupported package profile: '+key)
    hydraulic=parse_named_table(swp,TABLE_HEADERS['TABLE_SOILHYDRFUNC'])
    if hydraulic:
        a=np.asarray(hydraulic,dtype=float)
        if not np.isfinite(a).all():raise ValueError('nonfinite hydraulic parameter')
        if not ((a[:,0]>=0)&(a[:,0]<a[:,1])&(a[:,1]<=1)&(a[:,2]>0)&(a[:,3]>1)&(a[:,4]>0)&(a[:,8]>0)).all():
            raise ValueError('invalid hydraulic porosity/MvG/density parameter')
    profile=parse_named_table(swp,TABLE_HEADERS['TABLE_SOILPROFILE'])
    if profile:
        a=np.asarray(profile,dtype=float)
        if not np.isfinite(a).all() or (a[:,2:]<=0).any():raise ValueError('invalid soil discretization')
        if hydraulic and ((a[:,1]<1)|(a[:,1]>len(hydraulic))).any():raise ValueError('unresolved hydraulic layer reference')
        if float(scalar(swp,'RDS'))>a[:,2].sum():raise ValueError('rooting depth exceeds soil profile')
    files={'swap.swp'};warnings=[]
    def require(name):
        name=safe_name(name)
        p=root/name
        if not p.is_file():raise ValueError('missing asset: '+name)
        if '{{' in p.read_text(errors='strict'):raise ValueError('unresolved template in '+name)
        files.add(name);return p
    met=require(safe_name(scalar(swp,'METFIL')))
    frame=pd.read_csv(met,sep=r'\s+',skiprows=1,header=None,quotechar="'")
    if frame.shape[1]!=12:raise ValueError('MET requires twelve columns')
    values=frame.iloc[:,1:].apply(pd.to_numeric,errors='raise')
    if not np.isfinite(values.to_numpy()).all():raise ValueError('nonfinite MET')
    stamps=pd.to_datetime(dict(year=values.iloc[:,2],month=values.iloc[:,1],day=values.iloc[:,0]))
    expected=pd.date_range(start,end)
    if stamps.duplicated().any() or not stamps.is_monotonic_increasing or not expected.isin(stamps).all():raise ValueError('MET daily coverage gap/order/duplicate')
    if (values.iloc[:,3]<0).any() or (values.iloc[:,8]<0).any() or (values.iloc[:,9]<0).any():raise ValueError('negative MET radiation/rain/ETref')
    if not values.iloc[:,6].between(0,10).all():raise ValueError('HUM outside vapour-pressure range')
    if (values.iloc[:,4]>values.iloc[:,5]).any():raise ValueError('MET Tmin exceeds Tmax')
    if (values.iloc[:,7]<0).any() or not values.iloc[:,10].between(0,1).all():raise ValueError('invalid wind/WET day fraction')
    if int(scalar(swp,'SWDRA'))==1:
        dra=require(safe_name(scalar(swp,'DRFIL'),'.dra')).read_text()
        n=int(scalar(dra,'NRLEVS'))
        if not 1<=n<=5:raise ValueError('invalid NRLEVS')
        for i in range(1,n+1):
            for key,low,high in [(f'DRARES{i}',1,1e5),(f'INFRES{i}',0,1e5),(f'L{i}',1,1e5)]:
                if not low<=float(scalar(dra,key))<=high:raise ValueError('range '+key)
            days,_=dated_table(dra,f'DATOWL{i} LEVEL{i}')
            if days[0]>start or days[-1]<end:raise ValueError('DRA table does not bracket period')
    if int(scalar(swp,'SWBBCFILE'))==1:
        bbc=require(safe_name(scalar(swp,'BBCFIL'),'.bbc')).read_text()
        if int(scalar(bbc,'SWBOTB'))!=2 or int(scalar(bbc,'SW2'))!=2:raise ValueError('BBC profile requires prescribed-flux table')
        days,rows=dated_table(bbc,'DATE2 QBOT2',daily_steps='! LWKM_DAILY_STEP_V1' in bbc)
        if any(len(r)!=2 for r in rows):raise ValueError('BBC diagnostic extra columns forbidden')
        if any(abs(float(r[1]))>100 for r in rows):raise ValueError('BBC QBOT2 outside -100..100 cm/day')
        if days[0]>start or days[-1]<end:raise ValueError('BBC period gap')
    rotation=parse_named_table(swp,TABLE_HEADERS['TABLE_CROPROTATION'])
    covered=set()
    for row in rotation:
        a,b=date_value(str(row[0])),date_value(str(row[1]))
        if b<start or a>end:continue
        p=require(safe_name(row[3],'.crp'));crop=p.read_text()
        if int(scalar(swp,'SWETR'))==1 and int(scalar(crop,'SWCF'))!=1:
            raise ValueError('SWETR=1 requires crop factors: '+p.name)
        if int(scalar(crop,'SWCO2',0))==1 and int(scalar(crop,'SWATMOFIL',0))==1:
            co2=require(safe_name(scalar(crop,'ATMOFIL'),'.co2'))
            years=set()
            for line in co2.read_text().splitlines():
                tokens=line.split()
                if len(tokens)==2:
                    try:
                        yr=int(tokens[0]);v=float(tokens[1])
                        if not np.isfinite(v) or v<=0:raise ValueError('invalid CO2')
                        years.add(yr)
                    except ValueError:
                        if re.match(r'^\d',tokens[0]):raise
            if not set(range(max(a,start).year,min(b,end).year+1))<=years:raise ValueError('CO2 year coverage gap')
        for d in pd.date_range(max(a,start),min(b,end)):
            if d in covered:raise ValueError('overlapping crop rotation')
            covered.add(d)
    # SWAP explicitly simulates bare soil between crop cycles. Fallow is not
    # missing forcing and must not be replaced by an invented crop calendar.
    fallow_days=len(set(expected)-covered)
    return {'status':'PACKAGE_PREFLIGHT_PASS','production_admitted':False,
            'start':start.isoformat(),'end':end.isoformat(),'files':sorted(files),
            'fallow_days':fallow_days,'warnings':warnings}
