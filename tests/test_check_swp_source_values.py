import csv
import gzip
import json
import sys
from unittest.mock import patch
import numpy as np
from tools.server.check_swp_source_values import sample,main


def test_coordinate_crop_no_interpolation_and_nodata():
    values=np.array([[1,-9999],[3,4]])
    geometry=dict(ncols=2,nrows=2,xmin=100,ymin=100,dx=250,dy=250,nodata=-9999)
    xy=np.array([[225,475],[475,475],[226,475],[999,999]])
    v,r=sample(values,geometry,xy)
    assert v[0]==1
    assert np.isnan(v[1:]).all()
    assert (r['outside'],r['off_center'],r['nodata_or_nonfinite'],r['finite'])==(1,1,1,1)


def test_standalone_check_keeps_raw_units_and_does_not_change_sources(tmp_path):
    sources={}
    for role,value in [('glk',200),('head',1),('area',50)]:
        f=tmp_path/(role+'.asc');f.write_text(f'ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 250\nNODATA_value -9999\n{value}\n')
        sources[role]=dict(path=str(f))
    binding=tmp_path/'sources.json';binding.write_text(json.dumps(dict(sources=sources)))
    members=tmp_path/'members.csv.gz'
    with gzip.open(members,'wt') as f:
        w=csv.DictWriter(f,fieldnames=['svat','HRU','x','y','svat_area_m2']);w.writeheader();w.writerow(dict(svat=1,HRU=1,x=125,y=125,svat_area_m2=50))
    argv=['check','--sources',str(binding),'--members',str(members),'--output',str(tmp_path/'out')]
    with patch.object(sys,'argv',argv):assert main()==0
    r=json.loads((tmp_path/'out/source_values.json').read_text())
    assert r['sources']['glk']['samples']['raw_values']['median']==200
    assert r['groundwater_depth_unit_hypotheses']['NO_SURFACE_CONVERSION']['median']==199
    assert r['groundwater_depth_unit_hypotheses']['SURFACE_CM_TO_M_HYPOTHESIS']['median']==1
    assert r['sources']['area']['comparison_with_qualified_svat_area']['max_ratio']==1
    assert (tmp_path/'glk.asc').read_text().endswith('200\n')
    assert (tmp_path/'out.zip').exists()
