"""ET-CAL01: bounded CRP experiments on existing packages; no production admission.

All comparison fluxes are mm per calendar decade. The adapter consumes native
YYYYMMDD.csv HRU exports, not population summaries from compact acceptance.
"""
from __future__ import annotations
import argparse
import calendar
import hashlib
import json
from pathlib import Path
import re
import shutil
import numpy as np
import pandas as pd
from tools.execute_swap_candidate import execute, digest
from tools.work_c_report import metrics

PARAMETERS = {'rsc_scale': (.75, 1.25), 'feddes_scale': (.75, 1.25)}
COMPONENTS = ['ET', 'T', 'E_SOIL', 'E_IC', 'TPOT', 'IRRIG']
RAW = ['MSW_EBS','MSW_EIC','MSW_EPD','MSW_ESP','MSW_TACT','MSW_TPOT','PSSW','PSGW','BDGETACT']


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def scalar(text, name):
    matches = re.findall(r'^\s*'+re.escape(name)+r'\s*=\s*([-+\d.eEdD]+)', text, re.M|re.I)
    if len(matches)!=1: raise ValueError('expected one active scalar '+name)
    return float(matches[0].replace('D','e').replace('d','e'))


def replace_scalar(text, name, value):
    scalar(text, name)
    return re.sub(r'^(\s*'+re.escape(name)+r'\s*=\s*)[-+\d.eEdD]+',
                  lambda m:m[1]+format(value,'.12e'), text, flags=re.M|re.I)


def design(factorial=False):
    """Five screening runs; nine only when interaction/curvature merits expansion."""
    if factorial:
        return [dict(rsc_scale=a, feddes_scale=b) for a in (.75,1.,1.25) for b in (.75,1.,1.25)]
    return [dict(rsc_scale=1.,feddes_scale=1.)]+[
        dict(rsc_scale=(v if p=='rsc_scale' else 1.), feddes_scale=(v if p=='feddes_scale' else 1.))
        for p in PARAMETERS for v in PARAMETERS[p]]


def overlay(source, destination, parameters):
    """Patch only active CRPs in an already assembled SWAP package, never regenerate SWP."""
    if set(parameters)!=set(PARAMETERS): raise ValueError('unsupported parameter set')
    for p,(lo,hi) in PARAMETERS.items():
        if not np.isfinite(parameters[p]) or not lo<=parameters[p]<=hi: raise ValueError('outside bounds: '+p)
    source,destination=Path(source),Path(destination)
    swp=(source/'swap.swp').read_text()
    if scalar(swp,'SWETR')!=0: raise ValueError('RSC experiment requires PM SWETR=0')
    # The existing package preflight owns file references and crop rotations.
    # Require every available CRP to be active; reject unused/conflicting assets.
    crops=list(source.glob('*.crp'))
    if not crops: raise ValueError('no CRP')
    changes={}
    for crop in crops:
        if not re.search(r"['\"]"+re.escape(crop.stem)+r"['\"]",swp,re.I):
            raise ValueError('unused CRP requires explicit rotation-specific selection')
        t=crop.read_text()
        if re.search(r'^\s*SCHEDULE\s*=\s*1',t,re.M|re.I):
            raise ValueError('scheduled irrigation must be replayed/fixed before crop calibration')
        if scalar(t,'SWCF')!=2 or scalar(t,'SWDROUGHT')!=1:
            raise ValueError('requires crop-height PM and Feddes stress')
        vals={n:scalar(t,n) for n in ('RSC','HLIM3H','HLIM3L','HLIM4')}
        if vals['RSC']<=0: raise ValueError('RSC must be positive')
        new={'RSC':vals['RSC']*parameters['rsc_scale'],
             'HLIM3H':vals['HLIM3H']*parameters['feddes_scale'],
             'HLIM3L':vals['HLIM3L']*parameters['feddes_scale']}
        if not vals['HLIM4']<new['HLIM3L']<=new['HLIM3H']<0 or new['HLIM3L']< -10000:
            raise ValueError('Feddes order/range violated')
        for n,v in new.items():
            if v!=vals[n]: t=replace_scalar(t,n,v)
        changes[crop.name]={'before':vals,'after':new,'text':t}
    if destination.exists(): raise FileExistsError(destination)
    destination.mkdir(parents=True)
    original={}
    for f in source.iterdir():
        if f.is_file() and f.suffix.lower() in ('.swp','.crp','.bbc','.dra','.met','.co2','.end'):
            original[f.name]=digest(f);shutil.copyfile(f,destination/f.name)
    for n,c in changes.items():
        text=c.pop('text')
        if any(c['after'][key]!=c['before'][key] for key in c['after']):
            (destination/n).write_text(text)
    record={'status':'RESEARCH_OVERLAY_NOT_ADMITTED','parameters':parameters,'changes':changes,
            'parent_input_sha256':original,'input_sha256':{f.name:digest(f) for f in destination.iterdir()},
            'code_sha256':digest(__file__)}
    write_json(destination/'et-overlay.json',record)
    return record


def run_experiment(executable, source, destination, parameters, *, library_path=None,
                   start='1971-01-01',end='1971-12-20'):
    destination=Path(destination)
    overlay(source,destination/'input',parameters)
    r=execute(executable,destination/'input',destination/'run',library_path=library_path,
              expected_start=start,expected_end=end)
    if r['status']!='EXECUTION_PASS': raise ValueError('SWAP failed: '+str(destination))
    m=metrics(destination/'run/result_output.csv',Path(source).name,'ET-CAL01')
    if not m['serialized_water_balance_pass']: raise ValueError('independent water balance failed')
    write_json(destination/'metrics.json',m)
    d=extract(destination/'run/result_output.csv',start,end)
    d.to_csv(destination/'decades.csv',index=False)
    return r,m,d


def decade(date):
    d=pd.Timestamp(date);day=1 if d.day<=10 else 11 if d.day<=20 else 21
    start=pd.Timestamp(d.year,d.month,day)
    end=pd.Timestamp(d.year,d.month,day+9 if day<21 else calendar.monthrange(d.year,d.month)[1])
    return start,end


def validate_decades(f):
    f=f.copy()
    if f.empty: raise ValueError('empty decades')
    for c in ('start','end'): f[c]=pd.to_datetime(f[c],errors='raise')
    if f.start.duplicated().any(): raise ValueError('duplicate decade')
    f=f.sort_values('start').reset_index(drop=True)
    for row in f.itertuples():
        a,b=decade(row.start)
        if row.start!=a or row.end!=b or row.days!=(b-a).days+1: raise ValueError('invalid calendar decade')
    expected=pd.date_range(f.start.min(),f.end.max(),freq='D')
    if sum(f.days)!=len(expected): raise ValueError('missing calendar decades')
    if not np.isfinite(f[COMPONENTS].to_numpy(dtype=float)).all(): raise ValueError('nonfinite ET comparison')
    if (f[COMPONENTS]<-1e-6).any().any(): raise ValueError('negative ET or irrigation')
    if not np.allclose(f.ET,f['T']+f.E_SOIL+f.E_IC,atol=1e-5,rtol=1e-8):raise ValueError('ET component sum mismatch')
    return f


def extract(csv, start, end):
    """Daily interval amounts, cm -> mm. Explicit initial record excluded by start.

    Partial decades are rejected. No initial-state/day-zero or cumulative sums.
    ESUBLIM stays diagnostic and outside the five-term reference convention.
    """
    f=pd.read_csv(csv,comment='*');f['DATE']=pd.to_datetime(f.DATE)
    start,end=pd.Timestamp(start),pd.Timestamp(end)
    if f.DATE.duplicated().any(): raise ValueError('duplicate daily date')
    g=f.loc[f.DATE.between(start,end)].copy()
    if list(g.DATE)!=list(pd.date_range(start,end)): raise ValueError('daily coverage gap/order')
    if not np.isfinite(g[['TACT','EACT','EPD','EIC','TPOT','IRRIG']].to_numpy()).all():
        raise ValueError('nonfinite daily ET')
    g['T']=10*g.TACT;g['E_SOIL']=10*(g.EACT+g.EPD);g['E_IC']=10*g.EIC
    g['ET']=g['T']+g.E_SOIL+g.E_IC;g['TPOT']=10*g.TPOT;g['IRRIG']=10*g.IRRIG
    g['SUBLIMATION']=10*g.get('ESUBLIM',pd.Series(0.,index=g.index))
    g['DROUGHT_REDUCTION']=10*g.get('TREDDRY',pd.Series(np.nan,index=g.index))
    g['start']=g.DATE.map(lambda d:decade(d)[0])
    out=[]
    for a,h in g.groupby('start'):
        _,b=decade(a)
        if len(h)!=(b-a).days+1: raise ValueError('partial calendar decade')
        row={'start':a,'end':b,'days':len(h)}
        row.update(h[COMPONENTS+['SUBLIMATION','DROUGHT_REDUCTION']].sum(min_count=1).to_dict())
        row['T_REDUCTION']=row['TPOT']-row['T']
        row['STRESS_FRACTION']=1-row['T']/row['TPOT'] if row['TPOT']>0 else np.nan
        out.append(row)
    return validate_decades(pd.DataFrame(out))


def load_reference(directory, hru, *, semantic_qualified=False):
    """Read hash-bound native HRU decades. A provenance hash is not unit qualification."""
    if not semantic_qualified: raise ValueError('explicit unit/sign/period qualification required')
    directory=Path(directory);rows=[]
    for path in sorted(directory.glob('[0-9]'*8+'.csv')):
        stamp=pd.to_datetime(path.stem,format='%Y%m%d');a,b=decade(stamp)
        if stamp!=b: raise ValueError('native filename must be decade end')
        marker=(directory/(path.stem+'.sha256')).read_text()
        if 'output='+digest(path)+'\n' not in marker: raise ValueError('native output hash mismatch')
        f=pd.read_csv(path)
        if f.hru_id.duplicated().any(): raise ValueError('duplicate HRU')
        sel=f[f.hru_id==hru]
        if len(sel)!=1: raise ValueError('HRU absent')
        r=sel.iloc[0]
        if r.complete!=1 or any(r['coverage_'+n]!=1 for n in RAW): raise ValueError('incomplete HRU decade')
        if not np.isfinite(r[RAW].to_numpy(dtype=float)).all(): raise ValueError('nonfinite reference')
        row={'start':a,'end':b,'days':int(r.days),**r[RAW].to_dict()}
        row.update(T=r.MSW_TACT,E_SOIL=r.MSW_EBS+r.MSW_EPD,E_IC=r.MSW_EIC+r.MSW_ESP,
                   TPOT=r.MSW_TPOT,IRRIG=r.PSSW+r.PSGW)
        row['ET']=row['T']+row['E_SOIL']+row['E_IC'];row['BDGETACT_RESIDUAL']=r.BDGETACT-row['ET']
        row['source_sha256']=digest(path);rows.append(row)
    return validate_decades(pd.DataFrame(rows))


def compare(model, reference, parameters, *, regularization=.05):
    """ET-only objective + seasonal/annual closure + explicit bounded prior.

    Components are diagnostics. Equal-decade mean daily ET RMSE; dimensionless
    scale 1 mm/day. Calendar-year and Apr-Sep biases in mm/day.
    """
    if regularization<0: raise ValueError('negative regularization')
    m,r=validate_decades(model),validate_decades(reference)
    keys=['start','end','days']
    if not m[keys].equals(r[keys]): raise ValueError('model/reference calendars differ')
    d=m.days.to_numpy();e=(m.ET-r.ET).to_numpy()/d
    y=m.start.dt.year
    annual=(m.ET-r.ET).groupby(y).sum()/m.days.groupby(y).sum()
    season=m.start.dt.month.between(4,9)
    seasonal=(m.ET-r.ET)[season].groupby(y[season]).sum()/m.days[season].groupby(y[season]).sum()
    z=[]
    for p,(lo,hi) in PARAMETERS.items():
        v=parameters[p]
        if not lo<=v<=hi: raise ValueError('parameter bounds')
        z.append((v-1)/((hi-lo)/2))
    prior=regularization*float(np.mean(np.square(z)))
    data=float(np.mean(e**2)+.25*np.mean(annual**2)+(.25*np.mean(seasonal**2) if len(seasonal) else 0))
    diagnostics={c:{'bias_mm':float((m[c]-r[c]).sum()),'rmse_mm_decade':float(np.sqrt(np.mean((m[c]-r[c])**2)))} for c in COMPONENTS}
    stress=lambda f: float(1-f['T'].sum()/f.TPOT.sum()) if f.TPOT.sum()>0 else None
    return {'objective':data+prior,'data_loss':data,'regularization':prior,
            'rmse_et_mm_day':float(np.sqrt(np.mean(e**2))),
            'period_bias_et_mm':float((m.ET-r.ET).sum()),
            'year_bias_mm':{str(k):float(v) for k,v in (m.ET-r.ET).groupby(y).sum().items()},
            'season_bias_mm':{str(k):float(v) for k,v in (m.ET-r.ET)[season].groupby(y[season]).sum().items()},
            'stress_model':stress(m),'stress_reference':stress(r),'components':diagnostics,
            'psgw_reference_mm':float(r.PSGW.sum()) if 'PSGW' in r else None,
            'pssw_reference_mm':float(r.PSSW.sum()) if 'PSSW' in r else None,
            'bdgetact_residual_mm':float(r.BDGETACT_RESIDUAL.sum()) if 'BDGETACT_RESIDUAL' in r else None}


def sensitivity(outputs):
    """Central differences of decade ET and T reduction; singular values flag confounding."""
    derivatives=[];rows=[]
    base=outputs[(1.,1.)]
    for p,index in [('rsc_scale',0),('feddes_scale',1)]:
        low=[1.,1.];high=[1.,1.];low[index]=.75;high[index]=1.25
        l,h=outputs[tuple(low)],outputs[tuple(high)]
        derivative=(h.ET.to_numpy()-l.ET.to_numpy())/.5
        derivatives.append(derivative/base.days.to_numpy())
        rows.append({'parameter':p,'et_high_minus_low_mm':float((h.ET-l.ET).sum()),
                     't_high_minus_low_mm':float((h['T']-l['T']).sum()),
                     't_reduction_high_minus_low_mm':float(((h.TPOT-h['T'])-(l.TPOT-l['T'])).sum()),
                     'drought_reduction_high_minus_low_mm':float((h.DROUGHT_REDUCTION-l.DROUGHT_REDUCTION).sum()) if 'DROUGHT_REDUCTION' in h else None,
                     'rms_derivative_mm_day':float(np.sqrt(np.mean(derivatives[-1]**2)))})
    jac=np.array(derivatives).T
    singular=np.linalg.svd(jac,compute_uv=False)
    norms=np.linalg.norm(jac,axis=0)
    cosine=float(np.dot(jac[:,0],jac[:,1])/np.prod(norms)) if np.prod(norms)>0 else None
    return {'parameters':rows,'singular_values':singular.tolist(),'derivative_cosine':cosine,
            'weak_or_confounded':bool(min(norms)<.01 or singular[-1]<.05*singular[0]),
            'scope':'local 1971 research response; no national ranking'}


def features(x):
    a=np.asarray(x,dtype=float)
    if a.ndim!=2 or a.shape[1]!=2 or not np.isfinite(a).all(): raise ValueError('invalid coordinates')
    z=(a-1)/.25
    return np.column_stack([np.ones(len(z)),z,z[:,0]**2,z[:,1]**2,z[:,0]*z[:,1]])


def fit_surface(parameters, responses):
    x=features(parameters);y=np.asarray(responses,dtype=float)
    if len(x)!=len(y) or not np.isfinite(y).all(): raise ValueError('invalid responses')
    if np.linalg.matrix_rank(x)<6: raise ValueError('quadratic needs full-rank interaction design')
    beta=np.linalg.lstsq(x,y,rcond=None)[0]
    return {'coefficients':beta.tolist(),'training_rmse':float(np.sqrt(np.mean((x@beta-y)**2))),
            'bounds':PARAMETERS,'validation_required':True}


def predict_surface(surface, parameters):
    p=np.asarray(parameters,dtype=float)
    if (p<.75).any() or (p>1.25).any(): raise ValueError('no extrapolation')
    return features(p)@np.asarray(surface['coefficients'])


def select_profile(candidates, reference, train_years, validation_years, *, real_reference=False,
                   context_verified=False, irrigation_tolerance_mm=1., component_fraction_limit=.15):
    """Select observed SWAP profiles, never admit surrogate predictions or a same-year fit.

    Candidate keys are (RSC scale, Feddes scale). Independent year improvement,
    irrigated amount agreement and component partition guards must all pass.
    """
    if not set(train_years) or not set(validation_years) or set(train_years)&set(validation_years):
        raise ValueError('disjoint nonempty training/validation years required')
    r=validate_decades(reference);years=set(r.start.dt.year)
    if not set(train_years+validation_years)<=years: raise ValueError('missing requested years')
    subset=lambda f,yrs: f.loc[pd.to_datetime(f.start).dt.year.isin(yrs)].reset_index(drop=True)
    for year in train_years+validation_years:
        yy=r[r.start.dt.year==year]
        if len(yy)!=36 or yy.start.min()!=pd.Timestamp(year,1,1) or yy.end.max()!=pd.Timestamp(year,12,31):
            raise ValueError('complete independent calendar years required for selection')
    def score_years(f, yrs, parameters, penalty=.05):
        reports={str(y):compare(subset(f,[y]),subset(r,[y]),parameters,regularization=penalty) for y in yrs}
        return {'objective':float(np.mean([v['objective'] for v in reports.values()])),
                'data_loss':float(np.mean([v['data_loss'] for v in reports.values()])), 'by_year':reports}
    scores={}
    for key,f in candidates.items():
        mf=validate_decades(f)
        if not mf[['start','end','days']].equals(r[['start','end','days']]):raise ValueError('candidate calendar differs')
        train=score_years(f,train_years,dict(zip(PARAMETERS,key)))
        valid=score_years(f,validation_years,dict(zip(PARAMETERS,key)),penalty=0)
        scores[key]={'train':train,'validation':valid}
    baseline=(1.,1.)
    if baseline not in scores: raise ValueError('national baseline required')
    chosen=min(scores,key=lambda k:(scores[k]['train']['objective'],sum((v-1)**2 for v in k),k))
    f=validate_decades(candidates[chosen]);guards=[]
    if not context_verified:guards.append('unverified soil/drainage/bottom/management context')
    if not real_reference:guards.append('synthetic reference: no factual HRU calibration')
    if scores[chosen]['validation']['data_loss']>=scores[baseline]['validation']['data_loss']:
        guards.append('no independent-year improvement')
    if float((f.IRRIG-r.IRRIG).abs().sum())>irrigation_tolerance_mm:
        guards.append('irrigation mismatch must be resolved before crop calibration')
    for c in ('T','E_SOIL','E_IC'):
        for year in train_years+validation_years:
            a,b=subset(f,[year]),subset(r,[year])
            if abs(float((a[c]-b[c]).sum()))>component_fraction_limit*max(float(b.ET.sum()),1.):
                guards.append('component partition requires review: '+c+' '+str(year))
    year_winners={str(y):dict(zip(PARAMETERS,min(candidates,key=lambda k:compare(subset(candidates[k],[y]),subset(r,[y]),dict(zip(PARAMETERS,k)))['objective']))) for y in train_years+validation_years}
    near=[dict(zip(PARAMETERS,k)) for k in scores if scores[k]['train']['objective']<=scores[chosen]['train']['objective']+.01]
    return {'status':'RESEARCH_PROFILE_PROPOSED' if not guards else 'BASELINE_RETAINED',
            'chosen_parameters':dict(zip(PARAMETERS,chosen)),
            'applied_parameters':dict(zip(PARAMETERS,baseline if guards else chosen)),
            'blocking_diagnostics':guards,'yearwise_winners':year_winners,'near_optimal_profiles':near,'real_reference':real_reference,'production_admitted':False,
            'candidates':[{ 'parameters':dict(zip(PARAMETERS,k)),**v} for k,v in scores.items()]}


def library_plan(catalogue):
    """Screen existing complete representative packages, do not invent soils or forcing.

    Catalogue fields: case_id, bofek, landuse, irrigated, groundwater, weather,
    forcing_qualified. Deterministic first selection per soil-family/profile/regime/
    weather; all 79 BOFEK units receive baseline coverage before transfer.
    """
    f=catalogue.copy();allowed={'grass','maize','arable','nature'}
    if not set(f.landuse)<=allowed: raise ValueError('unknown landuse')
    if ((f.landuse=='nature')&f.irrigated).any(): raise ValueError('nature must be unirrigated')
    if not set(f.weather)<={'dry','average','wet'}: raise ValueError('unknown weather class')
    f=f.loc[f.forcing_qualified==True].copy()
    f['profile']=f.landuse+'_'+f.irrigated.map({True:'irrigated',False:'rainfed'})
    f=f.sort_values(['bofek','case_id'])
    initial=f.drop_duplicates(['soil_family','profile','groundwater','weather'])
    return {'status':'DESIGN_ONLY','nominal_full_strata':79*7*3*3,
            'baseline_case_ids':f.case_id.tolist(),'screening_case_ids':initial.case_id.tolist(),
            'screening_runs':len(initial)*5,'expansion_rule':'nine-point quadratic only if ET changes > 5 mm/season or local daily derivative > .05 mm/day; validate at off-grid point',
            'bofek_covered':sorted(f.bofek.unique().tolist()),'production_admitted':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    g=sub.add_parser('generate');g.add_argument('--source',type=Path,required=True);g.add_argument('--output',type=Path,required=True);g.add_argument('--factorial',action='store_true')
    e=sub.add_parser('extract');e.add_argument('--csv',type=Path,required=True);e.add_argument('--start',required=True);e.add_argument('--end',required=True);e.add_argument('--output',type=Path,required=True)
    c=sub.add_parser('compare');c.add_argument('--model',type=Path,required=True);c.add_argument('--reference',type=Path,required=True);c.add_argument('--output',type=Path,required=True)
    run=sub.add_parser('run')
    for n in ('executable','source','output','library-path'):run.add_argument('--'+n,type=Path,required=True)
    for n in PARAMETERS:run.add_argument('--'+n.replace('_','-'),type=float,default=1.)
    run.add_argument('--start',required=True);run.add_argument('--end',required=True)
    ref=sub.add_parser('reference')
    ref.add_argument('--directory',type=Path,required=True);ref.add_argument('--hru',type=int,required=True)
    ref.add_argument('--output',type=Path,required=True);ref.add_argument('--semantic-qualified',action='store_true')
    sel=sub.add_parser('select');sel.add_argument('--manifest',type=Path,required=True);sel.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='generate':
        for i,v in enumerate(design(a.factorial)):overlay(a.source,a.output/f'{i:03d}',v)
    elif a.command=='extract':extract(a.csv,a.start,a.end).to_csv(a.output,index=False)
    elif a.command=='compare':write_json(a.output,compare(pd.read_csv(a.model),pd.read_csv(a.reference),dict(rsc_scale=1.,feddes_scale=1.)))
    elif a.command=='run':run_experiment(a.executable,a.source,a.output,{n:getattr(a,n) for n in PARAMETERS},library_path=a.library_path,start=a.start,end=a.end)
    elif a.command=='reference':load_reference(a.directory,a.hru,semantic_qualified=a.semantic_qualified).to_csv(a.output,index=False)
    else:
        cfg=json.loads(a.manifest.read_text());candidates={tuple(r['parameters'][n] for n in PARAMETERS):pd.read_csv(r['csv']) for r in cfg['candidates']}
        write_json(a.output,select_profile(candidates,pd.read_csv(cfg['reference']),cfg['train_years'],cfg['validation_years'],real_reference=cfg.get('real_reference',False),context_verified=cfg.get('context_verified',False)))

if __name__=='__main__':main()
