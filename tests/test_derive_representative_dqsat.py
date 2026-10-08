import numpy as np
import pandas as pd
import pytest
from tools.compare_dqsat_authority import AsciiGrid
from tools.derive_representative_dqsat import derive

def grid():
    return AsciiGrid(np.array([[10.,20.],[30.,40.]]),2,2,0.,0.,1.,-9999.)

def test_arbitrary_partition_and_representative():
    relation=pd.DataFrame({"HRU":[50,50,700],"svat_orig":[1,2,3],
                           "x":[.5,1.5,.5],"y":[1.5,1.5,.5]})
    schema=pd.DataFrame({"HRU":[700,50],"svat_repr":[3,2]})
    out=derive(schema,relation,grid())
    assert out.hru.tolist()==[50,700]
    assert out.representative_dqsat.tolist()==[20.,30.]

def test_wrong_hru_representative_fails():
    relation=pd.DataFrame({"HRU":[50,700],"svat_orig":[1,2],
                           "x":[.5,1.5],"y":[1.5,1.5]})
    schema=pd.DataFrame({"HRU":[50],"svat_repr":[2]})
    with pytest.raises(ValueError,match="representative SVAT"):
        derive(schema,relation,grid())

def test_split_hru_changes_derived_domain():
    relation=pd.DataFrame({"HRU":[1,2],"svat_orig":[1,2],
                           "x":[.5,1.5],"y":[1.5,1.5]})
    schema=pd.DataFrame({"HRU":[1,2],"svat_repr":[1,2]})
    assert len(derive(schema,relation,grid()))==2
