"""NHI LHM MODFLOW layer-1 heads at 14th and 28th -> GHG GLG GVG GG per SVAT.
Hydrological year y = Apr 1 (y-1) .. Mar 31 y.
All outputs are depths in cm below MetaSWAP land surface, positive downward.
Read-only inputs. No automatic use of partition files or duplicate source selection.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, pathlib, re, sys, time
import numpy as np
from wb10_reader import read_area, raster, sample_xy

ROOT = pathlib.Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
AREA = pathlib.Path(r'E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp')
SOURCE = ROOT/'LWKM_run_resultaten_totaal'/'modflow'/'head'
OUTPUT = ROOT/'LWKM_run_resultaten_totaal'/'frank_export_heads'
PATTERN = re.compile(r'head_((?:19|20)\d{6})(?:000000)?_l1\.idf$', re.I)


def required_dates(first:int,last:int):
    # Only the 14th and 28th of each month: GHG, GLG, GVG and GG.
    # Begin in April of first-1 to complete the first hydrological year.
    for year in range(first-1, last+1):
        for month in range(1,13):
            if year == first-1 and month < 4:
                continue
            for day in (14, 28):
                yield dt.date(year, month, day)


def index_heads(folder:pathlib.Path):
    if not folder.is_dir(): raise FileNotFoundError(f'Map met samengevoegde laag-1-heads ontbreekt: {folder}')
    found={}; rejected=[]
    for f in folder.iterdir():
        if not f.is_file() or f.suffix.lower()!='.idf':continue
        m=PATTERN.fullmatch(f.name)
        if not m:
            if f.name.lower().startswith('head_') and len(rejected)<15: rejected.append(f.name)
            continue
        stamp=m[1]
        if stamp in found:raise ValueError(f'Dubbele samengevoegde head-IDFs {stamp}: {found[stamp]} en {f}')
        found[stamp]=f
    return found,rejected


def to_json(x):
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(np.floating,)):return float(x)
    raise TypeError(type(x))


def run(args):
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    manifest={'status':'STARTED','source':str(args.head_dir),'area_source':str(args.area),
              'method':'HG3/LG3 from twice-monthly 14th/28th per hydrological year; VG3 14 March, 28 March, 14 April; GG mean of 14th/28th monthly heads',
              'hydro_year_definition':'y-1 April 1 through y March 31','years':[args.first_year,args.last_year],
              'coordinate_reference':'EPSG:28992 (RD)','units':'cm below MetaSWAP land surface, positive down',
              'no_partial_gxg':True,'no_missing_required_measurements':True,
              'measurement_date_range':[f'{args.first_year-1}-04-14',f'{args.last_year}-12-28']}
    def save(): (out/'GXG_GG_manifest.json').write_text(json.dumps(manifest,indent=2,default=to_json),encoding='utf8')
    try:
        ds=list(required_dates(args.first_year,args.last_year))
        sources,excluded=index_heads(pathlib.Path(args.head_dir))
        missing=[d.isoformat() for d in ds if d.strftime('%Y%m%d') not in sources]
        manifest.update({'requested_14_28_dates':len(ds),'source_merged_files_indexed':len(sources),
                         'missing_required_measurements':len(missing),'first_missing_measurements':missing[:25],
                         'excluded_filename_examples':excluded,'available_requested_measurements':len(ds)-len(missing)})
        if args.check_only:
            manifest['status']='SOURCES_OK' if not missing else 'SOURCES_INCOMPLETE'
            save();print(json.dumps(manifest,indent=2));return 0 if not missing else 2
        if missing:
            raise FileNotFoundError(f'{len(missing)} vereiste 14/28 laag-1-IDFs ontbreken; zie GXG_GG_manifest.json')
        ids,areas,x,y=read_area(pathlib.Path(args.area))
        n=len(ids);manifest['n_svat']=n
        if n != args.expected_svats:raise ValueError(f"Expected {args.expected_svats} SVATs, got {n}")
        # Ground surface glk fixed width in authoritative original area_svat.inp;
        # validate alignments by ID against read_area() output.
        glk=[];glk_ids=[]
        with pathlib.Path(args.area).open('r',encoding='cp1252',errors='replace') as f:
            for ln in f:
                st=ln.strip()
                if not st or st[0] in '*#!':continue
                parts=st.replace(',','.').split()
                if not parts or not parts[0].isdigit():continue
                if len(parts)!=14:raise ValueError('AREA_SVAT onverwacht aantal kolommen tijdens maaiveldlezing')
                glk_ids.append(int(parts[0]));glk.append(float(parts[2]))
        if len(glk)!=n or not np.array_equal(np.array(glk_ids),ids):raise ValueError('AREA_SVAT glk-ID of aantal komt niet overeen met SVAT-volgorde')
        glk=np.asarray(glk,dtype=np.float64)
        if not np.isfinite(glk).all() or np.any((glk < -1000)|(glk>1000)):raise ValueError('Ongeldige maaiveldhoogte')

        # Yearly accumulation of GHG/GLG and GVG.
        ng=args.last_year-args.first_year+1
        ghg_sum=np.zeros(n,dtype=np.float64);glg_sum=np.zeros(n,dtype=np.float64)
        ghg_year_n=np.zeros(n,dtype=np.int16);glg_year_n=np.zeros(n,dtype=np.int16)
        gvg_sum=np.zeros(n,dtype=np.float64);gvg_year_n=np.zeros(n,dtype=np.int16)
        gg_sum=np.zeros(n,dtype=np.float64);gg_samples=np.zeros(n,dtype=np.int16)
        hg3=np.full((3,n),np.inf,dtype=np.float32)
        lg3=np.full((3,n),-np.inf,dtype=np.float32)
        half_count=np.zeros(n,dtype=np.uint8)
        vg_sum_y=np.zeros(n,dtype=np.float64);vg_n_y=np.zeros(n,dtype=np.uint8)
        geo_ref=None; rr=cc=None; invalid_totals=0; half_seen=0
        current_hy=args.first_year
        t0=time.time()
        def finish_hydro():
            nonlocal hg3,lg3,half_count
            valid=(half_count==24)&np.isfinite(hg3[2])&np.isfinite(lg3[2])
            # Depths: three lowest depths = highest water levels (GHG), three largest depths = lowest (GLG).
            ghg_sum[valid]+=np.sum(hg3[:,valid],axis=0,dtype=np.float64)/3
            glg_sum[valid]+=np.sum(lg3[:,valid],axis=0,dtype=np.float64)/3
            ghg_year_n[valid]+=1;glg_year_n[valid]+=1
            hg3[:]=np.inf;lg3[:]=-np.inf;half_count[:]=0
        def finish_vg():
            nonlocal vg_sum_y,vg_n_y
            valid=vg_n_y==3
            gvg_sum[valid]+=vg_sum_y[valid]/3
            gvg_year_n[valid]+=1
            vg_sum_y[:]=0;vg_n_y[:]=0
        for ix,d in enumerate(ds):
            stamp=d.strftime('%Y%m%d');path=sources[stamp]
            geo,nd,a=raster(path)
            if geo_ref is None:
                geo_ref=geo;rr,cc=sample_xy(geo,x,y)
                manifest['raster']={'nx':geo[0],'ny':geo[1],'xmin':geo[2],'ymax':geo[3],'dx':geo[4],'dy':geo[5]}
            elif geo!=geo_ref:raise ValueError(f'Rasterindeling gewijzigd bij {path}')
            h=np.asarray(a[rr,cc],dtype=np.float64)
            valid=np.isfinite(h)&(h!=nd)&(h>-1e10)&(h<1e10)
            invalid_totals+=int((~valid).sum())
            depth=(glk-h)*100.0
            # GG from exactly 24 half-monthly observations per calendar year.
            # This is not a daily time-weighted mean.
            if args.first_year<=d.year<=args.last_year:
                gg_sum[valid]+=depth[valid];gg_samples[valid]+=1
            if d.month in (3,4) and ((d.month==3 and d.day in (14,28)) or (d.month==4 and d.day==14)) and args.first_year<=d.year<=args.last_year:
                vg_sum_y[valid]+=depth[valid];vg_n_y[valid]+=1
                if d.month==4 and d.day==14:finish_vg()
            hy=d.year + (1 if d.month>=4 else 0)
            if args.first_year <= hy <= args.last_year and d.day in (14,28):
                # update smallest/largest three values per hydrological year
                v=np.where(valid,depth,np.inf).astype(np.float32)
                for row in range(3):
                    swap=hg3[row].copy();np.minimum(swap,v,out=hg3[row]);np.maximum(swap,v,out=v)
                v=np.where(valid,depth,-np.inf).astype(np.float32)
                for row in range(3):
                    swap=lg3[row].copy();np.maximum(swap,v,out=lg3[row]);np.minimum(swap,v,out=v)
                half_count[valid]+=1;half_seen+=1
                if d.month==3 and d.day==28:finish_hydro()
            if (ix+1)%365==0 or ix==len(ds)-1:
                print(f'Heads {ix+1}/{len(ds)} 14/28-meetmomenten, laatst {stamp}, verstreken {round(time.time()-t0)}s',flush=True)
        expected_gg=24*ng
        # no filling from incomplete hydro years
        ghg=np.full(n,np.nan);glg=np.full(n,np.nan);gvg=np.full(n,np.nan);gg=np.full(n,np.nan)
        all_ghg=ghg_year_n==ng;all_glg=glg_year_n==ng;all_gvg=gvg_year_n==ng;all_gg=gg_samples==expected_gg
        ghg[all_ghg]=ghg_sum[all_ghg]/ng;glg[all_glg]=glg_sum[all_glg]/ng
        gvg[all_gvg]=gvg_sum[all_gvg]/ng;gg[all_gg]=gg_sum[all_gg]/expected_gg
        dest=out/f'FRANK_LHM_SVAT_GXG_GG_{args.first_year}_{args.last_year}.csv'
        fields=['SVAT','Opp_svat_m2','X_RD','Y_RD','maaiveld_mNAP','GHG_cm_mv','GLG_cm_mv','GVG_cm_mv','GG_cm_mv','Dynamiek_cm','GHG_hydro_jaren','GLG_hydro_jaren','GVG_jaren','GG_meetmomenten','GG_meetmomenten_vereist']
        with dest.open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(fields)
            for i in range(n):
                val=lambda q: '' if not np.isfinite(q[i]) else format(q[i],'.6f')
                dynam=glg[i]-ghg[i] if all_glg[i] and all_ghg[i] else np.nan
                w.writerow([int(ids[i]),format(float(areas[i]),'.6f'),format(x[i],'.3f'),format(y[i],'.3f'),format(glk[i],'.4f'),val(ghg),val(glg),val(gvg),val(gg),'' if not np.isfinite(dynam) else format(dynam,'.6f'),int(ghg_year_n[i]),int(glg_year_n[i]),int(gvg_year_n[i]),int(gg_samples[i]),expected_gg])
        manifest.update({'status':'COMPLETE','files':{'svat_csv':str(dest)},'dates_processed':len(ds),'half_monthly_dates':half_seen,
          'n_complete_GHG':int(all_ghg.sum()),'n_complete_GLG':int(all_glg.sum()),'n_complete_GVG':int(all_gvg.sum()),'n_complete_GG':int(all_gg.sum()),
          'invalid_head_svat_measurement_samples':invalid_totals,'expected_14_28_GG_samples':expected_gg,
          'caveat':'Layer-1 head is a proxy for the phreatic groundwater level only where layer 1 is actually phreatic; compare with MetaSWAP groundwater level before interpreting GxG physically.',
          'GG_method':'arithmetic mean of 14th and 28th of each month, not daily average','no_interpolation':True,'no_level_clipping_at_land_surface':True})
        save();print(json.dumps({k:manifest[k] for k in ('status','n_svat','dates_processed','n_complete_GHG','n_complete_GVG','n_complete_GG')},indent=2));return 0
    except Exception as exc:
        manifest['status']='STOPPED_NO_QUALIFIED_RESULT';manifest['reason']=str(exc);save();raise


def cli():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--first-year',type=int,default=1991);p.add_argument('--last-year',type=int,default=2020)
    p.add_argument('--head-dir',type=pathlib.Path,default=SOURCE);p.add_argument('--area',type=pathlib.Path,default=AREA);p.add_argument('--out',type=pathlib.Path,default=OUTPUT)
    p.add_argument('--check-only',action='store_true')
    p.add_argument('--expected-svats',type=int,default=645582,help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.last_year<a.first_year or a.first_year<1971 or a.last_year>2022: p.error('Ongeldige periode; eerste hydrojaar moet minimaal 1971 zijn')
    sys.exit(run(a))
if __name__=='__main__':cli()
