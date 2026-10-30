"""Render independently editable HRU cropfiles and bind local atmospheric CO2."""
import hashlib
import re
from datetime import date
from pathlib import Path
from tools.swp_renderer import render_text

ROOT = Path(__file__).resolve().parents[1]
CROPS = {1: 'gras_maaien', 6: 'snijmais', 26: 'snijmais',
         23: 'fictief', 22: 'gras_beweiding'}
CO2_NAME = 'atmospheric_1975-2020.co2'


def source_assets():
    files = [ROOT/'templates/crops/base'/f'{name}.crp' for name in sorted(set(CROPS.values()))]
    files += [ROOT/'templates/crops/auxiliary/vanggewas.crp', ROOT/'templates/atmosphere'/CO2_NAME]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def local_assets(run, context):
    """Return local filename->bytes without changing rotation dates or crop types."""
    crop = CROPS[int(run['crop_id'])]
    schedule = int(run['irrigation_id']) != 0
    co2 = (ROOT/'templates/atmosphere'/CO2_NAME).read_bytes()
    years = {}
    for line in co2.decode('utf-8-sig').splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[0].isdigit():
            year = int(fields[0])
            if year in years: raise ValueError('duplicate CO2 year')
            years[year] = float(fields[1])
    for year in range(date.fromisoformat(run['TSTART']).year, date.fromisoformat(run['TEND']).year+1):
        if year not in years: raise ValueError(f'missing CO2 year {year}')
    assets = {CO2_NAME: co2}
    names = {str(r['CROPFIL']).strip("'") for r in context['TABLE_CROPROTATION']}
    if crop not in names: raise ValueError('rotation does not reference selected four-class crop')
    for name in sorted(names):
        if name not in (crop, 'vanggewas'): raise ValueError(f'unexpected crop reference {name}')
        folder = 'auxiliary' if name == 'vanggewas' else 'base'
        raw = (ROOT/'templates/crops'/folder/(name+'.crp')).read_bytes()
        try: text = raw.decode('utf-8-sig')
        except UnicodeDecodeError: text = raw.decode('cp1252')
        text = text.replace('\r\n', '\n')
        text = render_text(text, dict(SCHEDULE=int(schedule), ATMOFIL="'"+Path(CO2_NAME).stem+"'",
                                     SWITCH_SCHEDULE_OPTION_1=schedule))
        text = re.sub(r'(?m)^(\s*SCHEDULE\s*=)[^!\n]*',
                      lambda m: m[1]+' '+str(int(schedule))+' ', text)
        # Simple crops may lack a CO2 section. Keep assimilation switches unchanged.
        if not re.search(r'(?m)^\s*ATMOFIL\s*=', text):
            text += "\n* Local atmospheric CO2 file (extension .co2 is implicit)\n  ATMOFIL = '"+Path(CO2_NAME).stem+"'\n"
        if '{{' in text: raise ValueError('unresolved crop template')
        assets[name+'.crp'] = text.encode('utf-8')
    return assets
