"""Select existing HRUs for a limited ET pilot; do not qualify missing forcing.

Model bodem_id remains authoritative. BOFEK labels use the unique realized
soil lookup; original representative labels remain separate diagnostics.
"""
import argparse
import calendar
import gzip
import json
from pathlib import Path
import numpy as np
import pandas as pd
from tools.execute_swap_candidate import digest
from tools.et_calibration import write_json
from tools.hru_population_manifest import build_manifest, validate_membership


def select_prototypes(population):
    f=population.loc[~population.structural_blocked & ~population.soil_binding_unresolved].copy()
    if not np.isfinite(f[['ghg_median_cm','net_kwel_median_mm_y']]).all().all():raise ValueError('nonfinite selection features')
    selected=[];used_bofek=set()
    for _,g in f.groupby(['profile','ghg_screening_bin'],sort=True):
        features=g[['ghg_median_cm','net_kwel_median_mm_y','root_limit_cm']]
        med=features.median();scale=features.quantile(.75)-features.quantile(.25)
        score=((features-med)/scale.where(scale>0,1)).abs().sum(axis=1)
        ranked=g.assign(distance_to_stratum_median=score,new_bofek=~g.bofek79.isin(used_bofek))
        ranked=ranked.sort_values(['new_bofek','distance_to_stratum_median','hru_id'],ascending=[False,True,True])
        chosen=ranked.iloc[0].to_dict();selected.append(chosen);used_bofek.add(chosen['bofek79'])
    return pd.DataFrame(selected).drop(columns=['new_bofek'],errors='ignore')


def prepare(repo,output):
    repo,output=Path(repo),Path(output)
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True)
    interface=repo/'docs/evidence/2026-10-19-work-b/interfaces'
    reps=pd.read_csv(interface/'HRU_REPRESENTATIVE.csv.gz')
    pop=pd.read_csv(interface/'SVAT_QUALIFIED.csv.gz',usecols=['svat','bofek79','bodem370'])
    x=reps.merge(pop,left_on='hru_representative_svat',right_on='svat',validate='many_to_one')
    soil_lookup=pop[['bodem370','bofek79']].drop_duplicates()
    if soil_lookup.bodem370.duplicated().any():raise ValueError('ambiguous realized soil mapping')
    soil_lookup=soil_lookup.set_index('bodem370').bofek79.to_dict()
    if x.empty or x.HRU.duplicated().any() or x.HRU.isna().any():raise ValueError('invalid representative population')
    c2=json.loads((repo/'docs/evidence/2026-10-19-work-c2/research-input-catalogue.json').read_text())
    drainage={r['hru'] for r in json.loads((repo/'docs/evidence/2026-10-19-work-c2/remaining-blockers.json').read_text())}
    crop=json.load(gzip.open(repo/'docs/evidence/2026-10-20-work-d1/crop-assets-catalogue.json.gz'))
    crop_bad={r['hru_id'] for r in crop['errors']}
    contexts={}
    with gzip.open(interface/'HRU_CONTEXT_10242.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);contexts[row['run_id']]=row['context']
    population_manifest=build_manifest(x.HRU,release='work-b-recovered-snapshot',source_path=interface/'HRU_REPRESENTATIVE.csv.gz')
    validate_membership(population_manifest,contexts)
    rows=[]
    for r in x.to_dict('records'):
        hid=int(r['HRU']);c=contexts[hid];run=c['run']
        land={1:'grass',2:'maize',3:'arable',4:'nature'}[r['lu4']]
        irrig=run['irrigation_id']>0 if land!='nature' else False
        ghg=float(r['GHG_median']);bin_='shallow_proxy' if ghg<40 else 'intermediate_proxy' if ghg<80 else 'deep_proxy'
        # Merge suffix _x is the existing HRU representative schema soil;
        # _y is the original representative SVAT's soil label.
        original_soil=r['bodem370_y']
        mismatch=original_soil!=run['bodem_id']
        rows.append(dict(hru_id=hid,bofek79=int(soil_lookup[run['bodem_id']]),representative_bofek79=int(r['bofek79']),model_bodem_id=run['bodem_id'],
                         soil_binding_unresolved=False,
                         representative_bodem370=original_soil,soil_binding_mismatch=bool(mismatch),
                         profile=land+('_irrigated' if irrig else '_rainfed'),historical_irrigation_id=run['irrigation_id'],
                         ghg_median_cm=ghg,ghg_screening_bin=bin_,net_kwel_median_mm_y=float(r['NettoKwel_median']),
                         root_limit_cm=float(c['RDS']),structural_blocked=hid in drainage|crop_bad,
                         c2_research_package= str(hid) in c2['runs'],
                         c2_start=c2['start'] if str(hid) in c2['runs'] else '',
                         c2_end=c2['end'] if str(hid) in c2['runs'] else '',
                         complete_multiyear_forcing_qualified=False,real_reference_received=False))
    frame=pd.DataFrame(rows);selected=select_prototypes(frame)
    frame.to_csv(output/'population.csv',index=False);selected.to_csv(output/'pilot-hrus.csv',index=False)
    write_json(output/'hru-population-manifest.json',population_manifest)
    counts=pd.read_csv(repo/'docs/evidence/2026-10-20-work-d1/meteo_counts_by_year.csv')
    common_start=max(pd.Timestamp(c['TSTART']) for c in contexts.values())
    common_end=min(pd.Timestamp(c['TEND']) for c in contexts.values())
    yr=[]
    for year,g in counts.groupby('year'):
        expected=366 if calendar.isleap(int(year)) else 365
        series=g.groupby('variable').files.sum().to_dict()
        yr.append(dict(year=int(year),expected_days=expected,inventory_counts=series,
                       count_complete_rain_etref=series.get('RAIN')==expected and series.get('ETREF')==expected,
                       within_current_context_window=pd.Timestamp(int(year),1,1)>=common_start and pd.Timestamp(int(year),12,31)<=common_end,
                       daily_dates_verified=False,units_qualified=False,swap_package_qualified=False,
                       weather_class='UNCLASSIFIED',assigned_role='UNASSIGNED'))
    source_paths=[interface/'HRU_REPRESENTATIVE.csv.gz',interface/'SVAT_QUALIFIED.csv.gz',interface/'HRU_CONTEXT_10242.jsonl.gz',
                  repo/'docs/evidence/2026-10-20-work-d1/meteo_counts_by_year.csv',
                  repo/'docs/evidence/2026-10-19-work-c2/research-input-catalogue.json',
                  repo/'docs/evidence/2026-10-19-work-c2/remaining-blockers.json',
                  repo/'docs/evidence/2026-10-20-work-d1/crop-assets-catalogue.json.gz']
    write_json(output/'year-availability.json',yr)
    summary={'status':'PILOT_PREPARED_NOT_EXECUTION_READY','production_admitted':False,
             'population':len(frame),'pilot_hrus':selected.hru_id.astype(int).tolist(),'pilot_count':len(selected),
             'profiles':selected.profile.value_counts().to_dict(),'bofek_units_in_population':int(frame.bofek79.nunique()),
             'bofek_units_in_pilot':int(selected.bofek79.nunique()),'soil_label_differences_preserved':int(frame.soil_binding_mismatch.sum()),
             'soil_mapping_policy':'model bodem_id is authoritative; BOFEK label via unique realized SVAT soil mapping; no BOFEK2020 substitution; original representative labels retained',
             'structurally_blocked_hrus':int(frame.structural_blocked.sum()),
             'common_context_window':[str(common_start.date()),str(common_end.date())],
             'count_only_candidate_years':[r['year'] for r in yr if r['count_complete_rain_etref'] and r['within_current_context_window']],
             'complete_years_proven_by_current_research_catalogue':0,'real_reference_received':False,
             'screening_rule':'one existing HRU per profile x GHG(<40,40-80,>=80cm) proxy bin; prefer new BOFEK labels, then smallest IQR-scaled L1 distance to stratum medians in GHG/net kwel/root limit; deterministic HRU tie-break',
             'screening_limit':'GHG is a high-groundwater proxy, not dry-season groundwater regime; no new HRU/soil/boundary generation',
             'source_sha256':{str(p.relative_to(repo)):digest(p) for p in source_paths},
             'code_sha256':digest(__file__),
             'blockers':['native HRU references not received','complete source-qualified multi-year MET/BBC packages absent','dry/average/wet years unclassified','irrigated CRP experiments require fixed verified gifts','PM/CRP parameter eligibility requires package-level check'],
             'next_run_budget':{'screening_per_hru':5,'maximum_screening_runs_for_one_forcing_sequence':len(selected)*5,
                                'nationwide_calibration_requested':False}}
    write_json(output/'pilot-plan.json',summary);return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.repo,a.output),indent=2))
