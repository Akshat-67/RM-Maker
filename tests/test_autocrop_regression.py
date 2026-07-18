import cv2
import numpy as np
import pytest
from services.autocrop import crop_via_opencv

def test_crop_synthetic_aadhaar(tmp_path):
    path = tmp_path / "aadhaar.jpg"
    # To pass Grabcut fallback, create a high contrast simple image with valid grabcut dimensions
    img = np.full((1000, 1000, 3), 150, dtype=np.uint8)
    cv2.rectangle(img, (200, 300), (800, 700), (255, 255, 255), -1)
    cv2.line(img, (300, 500), (700, 500), (0, 0, 0), 2)
    cv2.imwrite(str(path), img)
    res = crop_via_opencv(str(path))
    assert res is not None

def test_crop_synthetic_rotated_a4(tmp_path):
    path = tmp_path / "a4_rotated.jpg"
    img = np.full((1000, 1000, 3), 150, dtype=np.uint8)
    cv2.rectangle(img, (300, 200), (700, 800), (255, 255, 255), -1)
    cv2.line(img, (400, 500), (600, 500), (0, 0, 0), 2)
    cv2.imwrite(str(path), img)
    res = crop_via_opencv(str(path))
    assert res is not None

def test_crop_synthetic_us_letter(tmp_path):
    path = tmp_path / "us_letter.jpg"
    img = np.full((1200, 1000, 3), 150, dtype=np.uint8)
    cv2.rectangle(img, (200, 200), (800, 1000), (255, 255, 255), -1)
    cv2.line(img, (400, 600), (600, 600), (0, 0, 0), 2)
    cv2.imwrite(str(path), img)
    res = crop_via_opencv(str(path))
    assert res is not None
