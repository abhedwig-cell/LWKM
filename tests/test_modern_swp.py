import pytest
from tools.modern_swp import prepare_template


def test_modern_adapter_does_not_accept_different_template():
    with pytest.raises(ValueError, match="SHA mismatch"):
        prepare_template(b"different template")
