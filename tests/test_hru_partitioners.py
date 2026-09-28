import pandas as pd, pytest
from tools.hru_partitioners import NativePartitionerUnavailable

def test_native_partitioner_cannot_silently_claim_equivalence():
    with pytest.raises(NotImplementedError):
        NativePartitionerUnavailable()(pd.DataFrame({"x":[1]}),1)
