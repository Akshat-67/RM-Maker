import os
from utils.config import NVIDIA_NIM_API_KEY, NVIDIA_OCR_API_KEY

def test_nvidia_keys():
    assert NVIDIA_NIM_API_KEY == "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"
    assert NVIDIA_OCR_API_KEY == "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"
