import cv2
import numpy as np
import pytest
from services.orientation import correct_orientation

def test_correct_orientation():
    # Create a dummy image (e.g., 100x200)
    img = np.zeros((100, 200, 3), dtype=np.uint8)

    # Test 90 degrees
    rot90 = correct_orientation(img, 90)
    assert rot90.shape == (200, 100, 3)

    # Test 180 degrees
    rot180 = correct_orientation(img, 180)
    assert rot180.shape == (100, 200, 3)

    # Test 270 degrees
    rot270 = correct_orientation(img, 270)
    assert rot270.shape == (200, 100, 3)

    # Test 0 degrees
    rot0 = correct_orientation(img, 0)
    assert rot0.shape == (100, 200, 3)
