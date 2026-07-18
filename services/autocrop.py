import os
import json
import logging
import shutil
import cv2
import numpy as np
from PIL import Image
from services.ai_client import AIClient
from utils.config import DEFAULT_GEMINI_API_KEYS

logger = logging.getLogger("Autocrop")

def crop_via_opencv_intersection(img_path, padding_ratio=0.03):
    """
    Tries to detect document boundary using a hybrid of Light Region masking
    and high edge-density projection.
    Returns (xmin, ymin, xmax, ymax) if a sub-region card is detected, else None.
    """
    img = cv2.imread(img_path)
    if img is None:
        return None
        
    h_img, w_img = img.shape[:2]
    img_area = h_img * w_img
    
    # 1. Method A: Light Region Detection (low saturation, high lightness)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, _, _ = cv2.split(lab)
    
    white_mask = cv2.inRange(hsv, np.array([0, 0, 150]), np.array([180, 75, 255]))
    _, thresh_l = cv2.threshold(l_channel, 170, 255, cv2.THRESH_BINARY)
    combined = cv2.bitwise_or(white_mask, thresh_l)
    
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    processed_light = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel_open)
    processed_light = cv2.morphologyEx(processed_light, cv2.MORPH_CLOSE, kernel_close)
    
    contours, _ = cv2.findContours(processed_light, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_light_box = None
    max_area = 0
    
    for c in contours:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = max(w, h) / min(w, h)
        if aspect_ratio < 1.1 or aspect_ratio > 2.2:
            continue
        if area > max_area and area > 0.08 * img_area:
            max_area = area
            best_light_box = (x, y, x + w, y + h)
            
    if best_light_box is None:
        if contours:
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            for c in contours:
                area = cv2.contourArea(c)
                if area > 0.08 * img_area:
                    x, y, w, h = cv2.boundingRect(c)
                    best_light_box = (x, y, x + w, y + h)
                    break
                    
    if best_light_box is None:
        best_light_box = (0, 0, w_img, h_img)

    # 2. Method B: Edge Density Region Detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    v_median = np.median(blurred)
    lower = int(max(0, 0.66 * v_median))
    upper = int(min(255, 1.33 * v_median))
    edged = cv2.Canny(blurred, lower, upper)
    
    # Clear outer 4% edges
    margin_y = int(h_img * 0.04)
    margin_x = int(w_img * 0.04)
    edged[0:margin_y, :] = 0
    edged[h_img-margin_y:, :] = 0
    edged[:, 0:margin_x] = 0
    edged[:, w_img-margin_x:] = 0
    
    row_sums = np.sum(edged, axis=1)
    col_sums = np.sum(edged, axis=0)
    
    smooth_window = int(min(h_img, w_img) * 0.02)
    if smooth_window % 2 == 0:
        smooth_window += 1
    
    row_sums = np.convolve(row_sums, np.ones(smooth_window)/smooth_window, mode='same')
    col_sums = np.convolve(col_sums, np.ones(smooth_window)/smooth_window, mode='same')
    
    row_thresh = np.max(row_sums) * 0.08
    col_thresh = np.max(col_sums) * 0.08
    
    active_rows = np.where(row_sums > row_thresh)[0]
    active_cols = np.where(col_sums > col_thresh)[0]
    
    if len(active_rows) > 0 and len(active_cols) > 0:
        best_edge_box = (active_cols[0], active_rows[0], active_cols[-1], active_rows[-1])
    else:
        best_edge_box = (0, 0, w_img, h_img)

    # 3. Intersect bounds
    lx1, ly1, lx2, ly2 = best_light_box
    ex1, ey1, ex2, ey2 = best_edge_box
    
    ix1 = max(lx1, ex1)
    iy1 = max(ly1, ey1)
    ix2 = min(lx2, ex2)
    iy2 = min(ly2, ey2)
    
    if ix2 - ix1 < 100 or iy2 - iy1 < 100:
        ix1, iy1, ix2, iy2 = ex1, ey1, ex2, ey2
        
    if ix2 - ix1 < 100 or iy2 - iy1 < 100:
        return None
        
    # Apply padding
    w_box = ix2 - ix1
    h_box = iy2 - iy1
    pad_w = int(padding_ratio * w_box)
    pad_h = int(padding_ratio * h_box)
    
    xmin = max(0, ix1 - pad_w)
    ymin = max(0, iy1 - pad_h)
    xmax = min(w_img, ix2 + pad_w)
    ymax = min(h_img, iy2 + pad_h)
    
    # Check if the detected crop represents a true sub-region (not the entire image)
    if (xmax - xmin) < 0.98 * w_img or (ymax - ymin) < 0.98 * h_img:
        return (xmin, ymin, xmax, ymax)
        
    return None

def autocrop_image_if_aadhar(filepath: str) -> None:
    # Ensure file exists and is an image
    _, ext = os.path.splitext(filepath.lower())
    if ext not in ['.jpg', '.jpeg', '.png']:
        return
        
    if filepath.endswith('.original'):
        return

    try:
        img = Image.open(filepath)
        img_width, img_height = img.size
        
        if img_width < 100 or img_height < 100:
            return

        # 1. Try local OpenCV cropper first
        crop_box = crop_via_opencv_intersection(filepath, padding_ratio=0.03)
        if crop_box is not None:
            xmin, ymin, xmax, ymax = crop_box
            logger.info(f"Local OpenCV cropper successfully localized card for {os.path.basename(filepath)}")
            
            # Save original backup
            backup_path = filepath + ".original"
            if not os.path.exists(backup_path):
                shutil.copy2(filepath, backup_path)
                
            cropped_img = img.crop((xmin, ymin, xmax, ymax))
            cropped_img.save(filepath, "JPEG", quality=95)
            return

        # 2. Fallback to VLM if local cropper did not find a sub-region
        logger.info(f"OpenCV could not localize sub-region for {os.path.basename(filepath)}. Falling back to VLM...")
        
        ai_client = AIClient(api_keys=DEFAULT_GEMINI_API_KEYS)

        system_instruction = (
            "You are an expert document localization tool. Your job is to locate the absolute outer boundaries of the entire Aadhaar card. "
            "The Aadhaar card contains several key elements: a photo (usually on the left), personal text details (name, DOB, gender), "
            "a 12-digit Aadhaar number (at the bottom), a bottom tricolor or red banner, and a QR code (usually on the right). "
            "Your bounding box must be a single rectangle that fully encapsulates all of these elements: "
            "1. ymin must be placed just above the top header ('Government of India' / 'भारत सरकार' and the emblem). "
            "2. ymax must be placed just below the bottom red/tricolor banner and the bottom-most text/Aadhaar number. "
            "3. xmin must be placed just to the left of the photo/emblem. "
            "4. xmax must be placed just to the right of the QR code/card border. "
            "Do not crop inside the card or cut off the Aadhaar number or QR code. Crop exactly at the outer white edges of the card, leaving no surrounding background. "
            "Return the output ONLY as a valid JSON object with these exact keys: "
            "{\"has_aadhar\": true/false, \"ymin\": int, \"xmin\": int, \"ymax\": int, \"xmax\": int}"
        )

        res = ai_client.generate_json(
            system_instruction=system_instruction,
            user_prompt=[img, "Locate the entire Aadhaar card encapsulating all headers, footers, Aadhaar number, photo, and QR code, cropping exactly to the outer borders."],
            model="gemini-2.5-flash"
        )
        
        if "text" in res:
            text = res["text"].strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            res = json.loads(text)

        if res.get("has_aadhar") and all(k in res for k in ["ymin", "xmin", "ymax", "xmax"]):
            ymin_raw = res["ymin"]
            xmin_raw = res["xmin"]
            ymax_raw = res["ymax"]
            xmax_raw = res["xmax"]

            ymin = max(0, int(ymin_raw * img_height / 1000))
            xmin = max(0, int(xmin_raw * img_width / 1000))
            ymax = min(img_height, int(ymax_raw * img_height / 1000))
            xmax = min(img_width, int(xmax_raw * img_width / 1000))

            if (xmax - xmin) < 50 or (ymax - ymin) < 50:
                logger.warning(f"Detected crop box for {os.path.basename(filepath)} is too small. Skipping crop.")
                return

            backup_path = filepath + ".original"
            if not os.path.exists(backup_path):
                shutil.copy2(filepath, backup_path)

            cropped_img = img.crop((xmin, ymin, xmax, ymax))
            cropped_img.save(filepath, "JPEG", quality=95)
            logger.info(f"Successfully auto-cropped Aadhaar card via VLM fallback for {os.path.basename(filepath)}")

    except Exception as e:
        logger.error(f"Error during autocropping for {os.path.basename(filepath)}: {e}")
