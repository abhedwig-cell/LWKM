import pytest
from tools.work_c_crop_factor import project


def test_constant_source_function_has_unambiguous_axis_projection():
    out,audit=project('SWCF=2\nCHTB=\n0.0 10.0\n2.0 10.0\n',
                      'DNR CH CF\n0.0 12.0 1.0\n180.0 12.0 1.0\n366.0 12.0 1.0\n* End of table\n')
    assert 'SWCF= 1' in out and '0.0 1.00000000' in out
    assert audit['constant_cf']==1 and not audit['production_admitted']


def test_time_varying_factor_does_not_get_invented_dvs_axis():
    with pytest.raises(ValueError,match='nonconstant'):
        project('SWCF=2\n','DNR CH CF\n0.0 12.0 0.5\n366.0 12.0 1.0\n* End of table\n')
