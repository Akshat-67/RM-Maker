import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def is_crop_valid(original_img: np.ndarray, cropped_img: np.ndarray, min_area_ratio: float = 0.05, min_resolution: int = 150) -> bool:
    """
    Validates the quality of the cropped image.
    If it fails, we should fall back to the original image.
    """
    if cropped_img is None or cropped_img.size == 0:
        return False

    orig_h, orig_w = original_img.shape[:2]
    crop_h, crop_w = cropped_img.shape[:2]

    orig_area = orig_h * orig_w
    crop_area = crop_h * crop_w

    # Check 1: Must retain at least a minimal portion of the original image
    if orig_area > 0 and (crop_area / orig_area) < min_area_ratio:
        logger.warning(f"Crop area ratio ({crop_area/orig_area:.3f}) below threshold ({min_area_ratio}).")
        return False

    # Check 2: Minimum absolute resolution
    if max(crop_w, crop_h) < min_resolution:
        logger.warning(f"Crop max dimension ({max(crop_w, crop_h)}) below minimum resolution ({min_resolution}).")
        return False

    # Check 3: Check for extreme aspect ratios (likely bad crop)
    aspect = max(crop_w, crop_h) / max(min(crop_w, crop_h), 1)
    if aspect > 4.0:
        logger.warning(f"Crop aspect ratio ({aspect:.2f}) too extreme.")
        return False

    return True
