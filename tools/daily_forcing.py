"""Strict daily groundwater/MET -> SWAP text; no scientific self-admission."""
from datetime import date,timedelta
import numpy as np
import pandas as pd
from tools.validate_daily_series import validate_daily_series

MET_COLUMNS=['rad_kj_m2_d','tmin_c','tmax_c','vapour_pressure_kpa','wind_m_s','rain_mm_d','etref_mm_d','wet_fraction']


def modern_met(frame,*,start,end,station):
    f=frame.copy();validate_daily_series(f.date.tolist(),[0.]*len(f),start=start,end=end,label='modern MET')
    a=f[MET_COLUMNS].apply(pd.to_numeric,errors='raise')
    if not np.isfinite(a.to_numpy()).all():raise ValueError('nonfinite MET')
    if (a[['rad_kj_m2_d','wind_m_s','rain_mm_d','etref_mm_d']]<0).any().any():raise ValueError('negative MET')
    if not a.vapour_pressure_kpa.between(0,10).all() or not a.wet_fraction.between(0,1).all():raise ValueError('HUM/WET range')
    if (a.tmin_c>a.tmax_c).any():raise ValueError('Tmin>Tmax')
    if ((a.rain_mm_d>0)&(a.wet_fraction<=0)).any() or ((a.rain_mm_d==0)&(a.wet_fraction!=0)).any():raise ValueError('inconsistent rain duration')
    lines=['Station DD MM YYYY Rad Tmin Tmax Hum Wind Rain ETref Wet']
    for d,values in zip(f.date,a.to_numpy()):
        t=date.fromisoformat(str(d));lines.append(f"'{int(station)}' {t.day} {t.month} {t.year} "+' '.join(format(v,'.12g') for v in values))
    return '\n'.join(lines)+'\n'


def weighted_weather(weather,weights,*,start,end):
    if weights.duplicated(['hru_id','site_id']).any() or weather.duplicated(['date','site_id']).any():raise ValueError('duplicate weather/weight key')
    if not np.isfinite(weights.weight).all() or (weights.weight<=0).any():raise ValueError('invalid area weights')
    if not np.allclose(weights.groupby('hru_id').weight.sum(),1.,rtol=0,atol=1e-12):raise ValueError('weights do not sum to one')
    results=[]
    for hid,w in weights.groupby('hru_id',sort=True):
        f=weather[weather.site_id.isin(w.site_id)]
        for sid,g in f.groupby('site_id'):
            validate_daily_series(g.date.tolist(),[0.]*len(g),start=start,end=end,label='weather site')
        if set(f.site_id)!=set(w.site_id):raise ValueError('missing weather site')
        joined=f.merge(w,on='site_id',validate='many_to_one')
        for c in MET_COLUMNS:
            if not np.isfinite(joined[c]).all():raise ValueError('nonfinite weather source')
            joined[c]=joined[c]*joined.weight
        out=joined.groupby('date')[MET_COLUMNS].sum().reset_index();out.insert(0,'hru_id',hid);results.append(out)
    return pd.concat(results,ignore_index=True)


def effective_bbc(frame,*,start,end,experimental_daily_steps=False):
    """Owner-accepted daily mean nodes, positive into layer1, mm/d -> cm/d.

    Ordinary daily points intentionally allow SWAP interpolation. No correction
    to preserve source daily volumes is applied (owner decision 2026-10-20).
    The explicit experimental flag retains the archived step experiment only.
    """
    validate_daily_series(frame.date.tolist(),frame.q_ext_mm_d.tolist(),start=start,end=end,label='GW-L1 BBC')
    values=frame.q_ext_mm_d.to_numpy(float)/10.
    if (abs(values)>100.).any():raise ValueError("QBOT2 outside SWAP -100..100 cm/day")
    if len(values)*(2 if experimental_daily_steps else 1)>36600:raise ValueError('BBC exceeds SWAP 4.3.1 36600-row capacity; split run period')
    lines=['! LWKM_DAILY_STEP_V1' if experimental_daily_steps else '! LWKM_OWNER_DAILY_MEAN_NODES_20261020', 'SWBOTB=2','SW2=2','DATE2 QBOT2']
    for d,v in zip(frame.date,values):
        terminal=(date.fromisoformat(str(d))+timedelta(days=1)).isoformat()
        token=f'{v:.12g}'
        if not any(c in token.lower() for c in ['.','e']):token+='.'
        lines.append(f'{d} {token}')
        if experimental_daily_steps:lines.append(f'{terminal} {token}')
    lines.append('* End of table')
    return '\n'.join(lines)+'\n'
