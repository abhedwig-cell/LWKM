#!/usr/bin/env python3
"""Read original area_svat.inp and precomputed GxG, attach land-use and soil lookups.

No hydrological rasters or time series are re-read. Soil lookup can be copied
from the canonical LWKM repository into this package (required if soil classes
are requested). Fails on unknown classes; never guesses missing soil classes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path

BASE=Path(r'G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM')
AREA=Path(r'E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp')
HEAD=BASE/'LWKM_run_resultaten_totaal'/'frank_export_heads'/'FRANK_LHM_SVAT_GXG_GG_1991_2020.csv'
OUT=BASE/'LWKM_run_resultaten_totaal'/'frank_export_aanvulling_v04'
HERE=Path(__file__).resolve().parent


def gt_class(ghg,glg):
    """8 main groundwater-trap classes, cm below soil level, GHG <= GLG."""
    if not (math.isfinite(ghg) and math.isfinite(glg)) or ghg>glg:return None
    if glg<50:return 1
    if glg<80:return 2
    if glg<120:return 3 if ghg<40 else 4
    if ghg<40:return 5
    if ghg<80:return 6
    if ghg<140:return 7
    return 8


def read_table(path,source,fields):
    with path.open(newline='',encoding='utf-8-sig') as f:
        rd=csv.DictReader(f)
        if not {source,*fields}.issubset(rd.fieldnames or []):raise ValueError('Lookup ontbrekende kolommen '+str(path))
        out={}
        for row in rd:
            key=int(row[source])
            if key in out:raise ValueError('Dubbele code in lookup: '+str(key))
            out[key]=tuple(row[k] for k in fields)
        return out

# Posities volgens MetaSWAP area_svat.inp; 1-based in handleiding.
# Vaste breedtes blijven leidend, óók bij aaneengeschreven getallen.
FIXED_FIELDS = {
    'svat': (0, 10), 'ark': (10, 20), 'glk': (20, 28),
    'tempCbotk': (28, 36), 'slk': (36, 42),
    'soil_description': (42, 58), 'luk': (58, 64),
    'dprzk': (64, 72), 'nm': (72, 82),
    'cfPm': (82, 90), 'cfETref': (90, 98),
}


def parse_area_fixed(line: str, lineno: int):
    """Parseer officiële vaste kolommen; onbekende trailing velden negeren."""
    if len(line.rstrip('\r\n')) < 82:
        raise ValueError(f'area_svat regel {lineno}: record korter dan 82 tekens')
    def field(name):
        a, b = FIXED_FIELDS[name]
        value = line[a:b].strip()
        if not value:
            raise ValueError(f'area_svat regel {lineno}: leeg verplicht veld {name} [{a+1}:{b}]')
        return value
    try:
        svat = int(field('svat'))
        area = float(field('ark').replace(',', '.'))
        glk = float(field('glk').replace(',', '.'))
        slk = int(field('slk'))
        luk = int(field('luk'))
        # nm mag in MetaSWAP bij gridmeteorologie leeg zijn.
        nm_s = line[72:82].strip()
        nm = int(nm_s) if nm_s else None
    except (ValueError, OverflowError) as exc:
        raise ValueError(f'area_svat vaste kolommen, regel {lineno}: {exc}') from exc
    # SVAT area is the original ark value, not necessarily the area of a complete
    # 250 m MODFLOW cell. Never impose the 62500 m2 MODFLOW-cell limit here.
    if svat <= 0:
        raise ValueError(f'area_svat regel {lineno}: svat={svat}, moet positief zijn')
    if not math.isfinite(area) or area <= 0:
        raise ValueError(f'area_svat regel {lineno}: ark={area!r}, moet eindig en >0 m2 zijn; '
                         f'bronfragment={line[10:20]!r}')
    if not math.isfinite(glk):
        raise ValueError(f'area_svat regel {lineno}: glk={glk!r}, moet eindig zijn; '
                         f'bronfragment={line[20:28]!r}')
    if not (1 <= slk <= 370 and 1 <= luk <= 22):
        raise ValueError(f'area_svat regel {lineno}: slk={slk}, luk={luk}; controleer bronformaat')
    return svat, slk, luk, nm


def execute(a):
    lu=read_table(a.landuse_lookup,'landgebruik22',['lu7','lu4','lu2'])
    # Projecteigenaarbesluit 6-11-2026: deze vier LU22-codes vallen buiten LWKM.
    # Behoud originele code, label alle geclusterde landgebruiksklassen als 0.
    for code in (8, 16, 18, 22):
        if code in lu and lu[code] != ('0', '0', '0'):
            raise ValueError(f'LU22={code}: historische lookup conflicteert met expliciet restcategoriebeleid')
        lu[code] = ('0', '0', '0')
    soil=read_table(a.soil_lookup,'bodem370',['bofek79','pawn21','grondsoort4','grondsoort2']) if a.soil_lookup.is_file() else {}
    if not a.allow_missing_soil and not soil:raise FileNotFoundError('Gekwalificeerde bodemlookup ontbreekt: '+str(a.soil_lookup)+'; haal deze uit de LWKM Git-repository')
    area={}
    with a.area.open('r',encoding='utf-8-sig',errors='replace') as f:
        for n,line in enumerate(f,1):
            if not line.strip() or line.lstrip().startswith(('*','!','#')):
                continue
            i,slk,luk,nm=parse_area_fixed(line,n)
            if i in area:raise ValueError('Dubbele SVAT '+str(i))
            area[i]=(slk,luk,nm)
    if len(area)!=645582:raise ValueError('area_svat verwacht 645582; vond '+str(len(area)))
    a.out.mkdir(parents=True,exist_ok=True)
    csvpath=a.out/'FRANK_SVAT_STATISCH_GT_1991_2020.csv'
    fields=['SVAT','landgebruik22','LU7','LU4','LU2','bodem370','BOFEK79','Pawn21','Grondsoort4','Grondsoort2','Meteoregio_nm','GHG_cm_mv','GLG_cm_mv','Gtnr','Dynamiek_cm']
    missing_soil=set();unknown_lu=set();seen=set();counter=[0]*9;rest_lu_counts={8:0,16:0,18:0,22:0}
    with a.heads.open(newline='',encoding='utf-8-sig') as f, csvpath.open('w',newline='',encoding='utf-8') as out:
        rd=csv.DictReader(f);cols=set(rd.fieldnames or [])
        if not {'SVAT','GHG_cm_mv','GLG_cm_mv'}<=cols:raise ValueError('GxG kolomnamen zijn niet conform v0.2')
        wr=csv.writer(out);wr.writerow(fields)
        for row in rd:
            i=int(row['SVAT'])
            if i in seen:raise ValueError('Dubbele GxG SVAT '+str(i))
            seen.add(i)
            if i not in area:raise ValueError('GxG SVAT niet in area_svat: '+str(i))
            slk,luk,nm=area[i]
            if luk in rest_lu_counts:rest_lu_counts[luk]+=1
            land=lu.get(luk)
            if land is None:unknown_lu.add(luk);land=('','','')
            bodem=soil.get(slk)
            if bodem is None:missing_soil.add(slk);bodem=('','','','')
            ghg=float(row['GHG_cm_mv']) if row['GHG_cm_mv'] else float('nan')
            glg=float(row['GLG_cm_mv']) if row['GLG_cm_mv'] else float('nan')
            gt=gt_class(ghg,glg)
            if gt is not None:counter[gt]+=1
            dynamics=glg-ghg if math.isfinite(ghg) and math.isfinite(glg) else None
            wr.writerow([i,luk,*land,slk,*bodem,nm,ghg if math.isfinite(ghg) else '',glg if math.isfinite(glg) else '',gt if gt is not None else '',dynamics if dynamics is not None else ''])
    if seen!=set(area):raise ValueError('GxG ontbreekt voor '+str(len(set(area)-seen))+' SVATs')
    if unknown_lu:raise ValueError('Niet toegelaten landgebruik22 codes: '+str(sorted(unknown_lu)))
    if missing_soil and not a.allow_missing_soil:raise ValueError('Bodemlookup ontbreekt voor codes '+str(sorted(missing_soil)))
    report={'status':'COMPLETE' if not missing_soil else 'INCOMPLETE_SOIL_LOOKUP','svats':len(seen),'gt_counts':{str(i):counter[i] for i in range(1,9)},'no_gt':len(seen)-sum(counter),'unmapped_soil_codes':sorted(missing_soil),'excluded_lu22_to_zero':rest_lu_counts,'area_fixed_columns_1_based':{'svat':'1-10','ark':'11-20','glk':'21-28','slk':'37-42','luk':'59-64','nm':'73-82'},'gt_rule':'coarse 1-8, GHG/GLG cm-mv, boundaries lower inclusive','output':str(csvpath)}
    (a.out/'MANIFEST_FRANK_STATISCH_GT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(report['status'],len(seen),'SVAT', 'GT=',counter[1:])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--area',type=Path,default=AREA)
    p.add_argument('--heads',type=Path,default=HEAD)
    p.add_argument('--out',type=Path,default=OUT)
    p.add_argument('--landuse-lookup',type=Path,default=HERE/'landuse-mapping-realized-v1.csv')
    p.add_argument('--soil-lookup',type=Path,default=HERE/'bodem370_classification_lookup.csv')
    p.add_argument('--allow-missing-soil',action='store_true',help='QA ONLY, lege bodemklassen in plaats van productiestop')
    try:execute(p.parse_args())
    except Exception as e:print('STOP:',e,file=sys.stderr);sys.exit(2)
if __name__=='__main__':main()
