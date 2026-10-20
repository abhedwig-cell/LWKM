"""Package source-bound population support and an explicitly unbound MET spec."""
import argparse
import gzip
import io
import json
from pathlib import Path
import pandas as pd
from tools.assemble_swap_package import sha256
from tools.met_grid_consumer import UNITS
from tools.run_dra_protected_population import atomic_json

def prepare(output):
    output.mkdir(parents=True,exist_ok=True)
    src=Path(__file__).resolve().parent/'metaswap_hru/tests/supplied_members.csv.gz'
    if sha256(src)!='42a73f98acf428e1a3ffd698326aa03b4daf2bf8b505423ab0e6b11b7eed50c8':raise ValueError('normalized source support changed')
    f=pd.read_csv(src).rename(columns={'svat_orig':'svat_id','HRU':'hru_id','x':'x_rd','y':'y_rd'})
    data=f.to_csv(index=False,float_format='%.15g').encode();p=output/'members.csv.gz'
    with p.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as z:z.write(data)
    g=output/'met_grid_header.asc';g.write_text('ncols 300\nnrows 325\nxllcorner 0\nyllcorner 300000\ncellsize 1000\nNODATA_value -9999\n')
    # Runtime paths are relative to the delivery folder. Existing source
    # directories are documented; unverified units never receive a default.
    root=r'E:\LHM_4.3.3\Data\2_Model_Input\meteo'
    paths={'rain_mm_d':('RD1','precipitation_{date}.asc'),'etref_mm_d':('EV24','evaporation_{date}.asc'),
           'tmin_c':('TN','TN_{date}.asc'),'tmax_c':('TX','TX_{date}_l1.asc'),'rad_kj_m2_d':('Q','Q_{date}.asc'),
           'vapour_pressure_kpa':('FG','FG_{date}.asc')}
    sources={}
    for k,unit in UNITS.items():
        knmi=k in ['wind_m_s','wet_raw_fraction']
        directory,pattern=paths.get(k,('KNMI_WIND' if k=='wind_m_s' else 'KNMI_WET_RAW',('WIND' if k=='wind_m_s' else 'WET_RAW')+'_{date}.asc'))
        sources[k]=dict(directory=root+'\\'+directory,pattern=pattern,confirmed=knmi,
                        input_unit=unit if knmi else 'UNVERIFIED_RAW_LHM_UNIT',output_unit=unit,scale=1.,offset=0.,
                        evidence='WORK_A_KNMI_WIND_WET_OFFLINE_POLICY_2026-10-20' if knmi else '')
    spec=dict(dataset_id='LWKM_LHM433_KNMI_1970_2022_CANDIDATE',members=dict(path='members.csv.gz',sha256=sha256(p)),
              template=dict(path='met_grid_header.asc',sha256=sha256(g)),expected_members=427656,expected_hrus=10242,
              start='1970-01-01',end='2022-12-31',sources=sources,
              configuration_status='EXAMPLE_REQUIRES_SOURCE_UNIT_BINDING_AND_ACTUAL_KNMI_PATHS')
    atomic_json(output/'met_sources.example.json',spec)
    atomic_json(output/'support-provenance.json',dict(normalized_source_sha256=sha256(src),
                original_area_sha256='352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc',
                original_mapping_sha256='13f4f129957e24ce6f9380dc4e72cc9bdada59620dc4a0a5464bf6e8b319f7f4',
                selected_area_m2=float(f.area_m2.sum()),members=len(f),hrus=int(f.hru_id.nunique()),production_admitted=False,
                member_file_sha256=sha256(p),geometry_header_sha256=sha256(g)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.output)
