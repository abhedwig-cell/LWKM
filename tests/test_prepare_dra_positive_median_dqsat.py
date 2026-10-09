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
