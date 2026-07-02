import os
import pytest
from utils.config import get_nvidia_api_key

def test_get_nvidia_api_key_missing(monkeypatch):
    # Ensure the env var is not set
    monkeypatch.delenv('NVIDIA_API_KEY', raising=False)
    with pytest.raises(RuntimeError) as exc:
        get_nvidia_api_key()
    assert 'NVIDIA_API_KEY not set' in str(exc.value)
