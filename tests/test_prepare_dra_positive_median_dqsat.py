import numpy as np
import pandas as pd
import pytest
from tools.compare_dqsat_authority import AsciiGrid
from tools.prepare_dra_positive_median_dqsat import prepare

def grid():
    return AsciiGrid(np.array([[0.,8.,20.],[3.,4.,10.]]),3,2,0.,0.,1.,-9999.)

def test_median_over_positive_members_and_original_preserved():
    relation=pd.DataFrame({"HRU":[99,99,99,7],"svat_orig":[1,2,3,4],
                           "x":[.5,1.5,2.5,1.5],"y":[1.5,1.5,1.5,.5]})
    schema=pd.DataFrame({"HRU":[99,7],"svat_repr":[1,4]})
    out=prepare(schema,relation,grid()).set_index("hru")
    assert out.loc[99,"source_representative_dqsat"]==0
    assert out.loc[99,"representative_dqsat"]==14
    assert out.loc[99,"positive_count"]==2
    assert out.loc[7,"representative_dqsat"]==4

def test_no_positive_member_fails_closed():
    relation=pd.DataFrame({"HRU":[1],"svat_orig":[1],"x":[.5],"y":[1.5]})
    schema=pd.DataFrame({"HRU":[1],"svat_repr":[1]})
    with pytest.raises(ValueError,match="no positive"):
        prepare(schema,relation,grid())


@pytest.mark.parametrize('representative',[0.,-9999.])
def test_excludes_exact_nodata_and_zero_but_preserves_representative(representative):
    relation=pd.DataFrame({"HRU":[99]*4,"svat_orig":[1,2,3,4],
                           "x":[.5,1.5,2.5,3.5],"y":[.5]*4})
    schema=pd.DataFrame({"HRU":[99],"svat_repr":[1]})
    g=AsciiGrid(np.array([[representative,-9999.,8.,20.]]),4,1,0.,0.,1.,-9999.)
    out=prepare(schema,relation,g).iloc[0]
    assert out.positive_median==14 and out.candidate_spacing_m==56
    assert out.source_representative_dqsat==representative
    assert out.nodata_count==(2 if representative==-9999 else 1)


@pytest.mark.parametrize('bad',[-1.,float('nan'),float('inf')])
def test_invalid_member_rejected_even_with_other_positives(bad):
    relation=pd.DataFrame({"HRU":[99,99],"svat_orig":[1,2],"x":[.5,1.5],"y":[.5,.5]})
    schema=pd.DataFrame({"HRU":[99],"svat_repr":[1]})
    g=AsciiGrid(np.array([[8.,bad]]),2,1,0.,0.,1.,-9999.)
    with pytest.raises(ValueError,match='negative|nonfinite'):
        prepare(schema,relation,g)
