import cv2
import numpy as np
import pytesseract
import logging

logger = logging.getLogger(__name__)

def detect_orientation(img: np.ndarray) -> int:
    """
    Detects document orientation using Tesseract OSD and returns rotation degrees needed (0, 90, 180, 270).
    Fallback to 0 if detection fails or confidence is low.
    """
    try:
        # Convert to grayscale for Tesseract
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        # Use pytesseract OSD to detect orientation
        osd_data = pytesseract.image_to_osd(gray, output_type=pytesseract.Output.DICT, config='--psm 0 -c min_characters_to_try=5')

        rot = osd_data.get('rotate', 0)
        conf = osd_data.get('orientation_conf', 0)

        logger.info(f"Tesseract OSD detected rotation: {rot} degrees with confidence: {conf}")

        if conf > 1.0: # require at least some confidence
            return rot
        else:
            logger.info("Orientation confidence too low, defaulting to 0.")
            return 0

    except Exception as e:
        logger.warning(f"OSD orientation detection failed: {e}. Defaulting to 0.")
        return 0

def correct_orientation(img: np.ndarray, rotation_degrees: int) -> np.ndarray:
    """
    Rotates the image by the given degrees (must be multiple of 90) counter-clockwise.
    (Note: Tesseract's 'rotate' indicates how much the image needs to be rotated counter-clockwise to be upright).
    """
    if rotation_degrees == 90:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rotation_degrees == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif rotation_degrees == 270:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img
