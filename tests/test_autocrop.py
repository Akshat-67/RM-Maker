import os
import shutil
from unittest.mock import patch, MagicMock
from PIL import Image
import pytest
from services.autocrop import autocrop_image_if_aadhar

def test_autocrop_success(tmp_path):
    # Create dummy image
    img_path = str(tmp_path / "test.jpg")
    img = Image.new("RGB", (1000, 1000), color="white")
    img.save(img_path)

    mock_res = {"has_aadhar": True, "ymin": 100, "xmin": 100, "ymax": 900, "xmax": 900}

    with patch("services.autocrop.AIClient") as mock_aiclient:
        mock_instance = MagicMock()
        mock_aiclient.return_value = mock_instance
        mock_instance.generate_json.return_value = mock_res

        autocrop_image_if_aadhar(img_path)

    # Check original backup was created
    assert os.path.exists(img_path + ".original")
    # Check cropped image size
    cropped = Image.open(img_path)
    assert cropped.size == (800, 800)

def test_autocrop_no_aadhar(tmp_path):
    img_path = str(tmp_path / "test.jpg")
    img = Image.new("RGB", (1000, 1000), color="white")
    img.save(img_path)

    mock_res = {"has_aadhar": False, "ymin": 0, "xmin": 0, "ymax": 0, "xmax": 0}

    with patch("services.autocrop.AIClient") as mock_aiclient:
        mock_instance = MagicMock()
        mock_aiclient.return_value = mock_instance
        mock_instance.generate_json.return_value = mock_res

        autocrop_image_if_aadhar(img_path)

    # Check no backup was created
    assert not os.path.exists(img_path + ".original")
    # Check image size unchanged
    original = Image.open(img_path)
    assert original.size == (1000, 1000)
