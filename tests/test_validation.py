import numpy as np
import pytest
from services.crop_validation import is_crop_valid

def test_is_crop_valid():
    orig = np.zeros((1000, 1000, 3), dtype=np.uint8)

    # Valid crop
    valid = np.zeros((800, 600, 3), dtype=np.uint8)
    assert is_crop_valid(orig, valid) == True

    # Too small (area)
    small = np.zeros((100, 100, 3), dtype=np.uint8)
    assert is_crop_valid(orig, small, min_area_ratio=0.05) == False

    # Extreme aspect ratio
    extreme = np.zeros((900, 100, 3), dtype=np.uint8)
    assert is_crop_valid(orig, extreme) == False

    # Empty image
    empty = np.array([])
    assert is_crop_valid(orig, empty) == False
