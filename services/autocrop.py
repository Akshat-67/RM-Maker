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


# ---------------------------------------------------------------------------
# Method 1: Strict Contour Detection (fast, for clear-background images)
# ---------------------------------------------------------------------------
def _find_card_via_contour(img):
    """
    Finds the card via Canny edge detection + dilation + contour analysis.
    Works best when the card is on a clearly different (dark) background.
    Returns (xmin, ymin, xmax, ymax) or None.
    """
    h_img, w_img = img.shape[:2]
    img_area = h_img * w_img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    candidates = []

    v_median = np.median(blurred)
    lower = int(max(0, 0.5 * v_median))
    upper = int(min(255, 1.5 * v_median))
    edges = cv2.Canny(blurred, lower, upper)

    for dilation_iter in [3, 5, 8]:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(edges, kernel, iterations=dilation_iter)
        dilated = cv2.morphologyEx(
            dilated, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)),
        )

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < 0.10 * img_area or area > 0.92 * img_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if w > 0.92 * w_img and h > 0.85 * h_img:
                continue

            bbox_area = w * h
            solidity = area / bbox_area if bbox_area > 0 else 0
            aspect = max(w, h) / max(min(w, h), 1)
            if aspect < 1.2 or aspect > 2.5:
                continue
            if solidity < 0.7:
                continue

            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            vertex_bonus = 1.4 if len(approx) == 4 else (1.15 if len(approx) <= 6 else 1.0)
            score = area * (solidity ** 2) * vertex_bonus
            candidates.append({"box": (x, y, x + w, y + h), "score": score})

    # Also try OTSU threshold
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(otsu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        area = cv2.contourArea(c)
        if area < 0.10 * img_area or area > 0.92 * img_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if w > 0.92 * w_img and h > 0.85 * h_img:
            continue
        bbox_area = w * h
        solidity = area / bbox_area if bbox_area > 0 else 0
        aspect = max(w, h) / max(min(w, h), 1)
        if aspect < 1.2 or aspect > 2.5:
            continue
        if solidity < 0.7:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        vertex_bonus = 1.4 if len(approx) == 4 else (1.15 if len(approx) <= 6 else 1.0)
        score = area * (solidity ** 2) * vertex_bonus
        candidates.append({"box": (x, y, x + w, y + h), "score": score})

    if candidates:
        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[0]["box"]
    return None


# ---------------------------------------------------------------------------
# Method 2: GrabCut + Asymmetric Edge-Density Expansion
# ---------------------------------------------------------------------------
def _grabcut_with_expansion(img):
    """
    Uses GrabCut to segment the card from the background, then expands
    the detected region using edge density to capture footer/header areas
    that GrabCut may miss (red banner, Aadhaar number line, etc.).

    Asymmetric expansion:
      - Upward:   conservative (backgrounds tend to bleed above)
      - Downward: aggressive   (capture Aadhaar number + footer banner)
      - Left/Right: moderate

    Returns (xmin, ymin, xmax, ymax) or None.
    """
    h_img, w_img = img.shape[:2]

    # --- GrabCut ---
    margin_x = int(w_img * 0.08)
    margin_y = int(h_img * 0.08)
    rect = (margin_x, margin_y, w_img - 2 * margin_x, h_img - 2 * margin_y)

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Downscale for speed (GrabCut is O(n^2))
    scale = 1.0
    if max(h_img, w_img) > 800:
        scale = 800.0 / max(h_img, w_img)
        small = cv2.resize(img, None, fx=scale, fy=scale)
        small_mask = np.zeros(small.shape[:2], np.uint8)
        small_rect = (
            int(rect[0] * scale), int(rect[1] * scale),
            int(rect[2] * scale), int(rect[3] * scale),
        )
        cv2.grabCut(small, small_mask, small_rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        mask = cv2.resize(small_mask, (w_img, h_img), interpolation=cv2.INTER_NEAREST)
    else:
        mask = np.zeros((h_img, w_img), np.uint8)
        cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, k_close)

    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < 0.05 * (h_img * w_img):
        return None

    gx, gy, gw, gh = cv2.boundingRect(largest)
    gc_x1, gc_y1, gc_x2, gc_y2 = gx, gy, gx + gw, gy + gh

    # --- Edge-density expansion ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    v_median = np.median(blurred)
    edges = cv2.Canny(blurred, int(max(0, 0.5 * v_median)), int(min(255, 1.5 * v_median)))

    row_sums = np.sum(edges, axis=1).astype(np.float64)
    col_sums = np.sum(edges, axis=0).astype(np.float64)

    sw = max(3, int(min(h_img, w_img) * 0.015))
    if sw % 2 == 0:
        sw += 1
    row_sums = np.convolve(row_sums, np.ones(sw) / sw, mode="same")
    col_sums = np.convolve(col_sums, np.ones(sw) / sw, mode="same")

    inner_row_avg = np.mean(row_sums[gc_y1:gc_y2]) if gc_y2 > gc_y1 else 0
    inner_col_avg = np.mean(col_sums[gc_x1:gc_x2]) if gc_x2 > gc_x1 else 0

    # Asymmetric thresholds
    up_thresh = inner_row_avg * 0.25       # Conservative upward
    down_thresh = inner_row_avg * 0.10     # Aggressive downward
    left_thresh = inner_col_avg * 0.15     # Moderate
    right_thresh = inner_col_avg * 0.15    # Moderate

    # Expansion caps (% of GrabCut box size)
    max_up = int(gh * 0.15)
    max_down = int(gh * 0.40)
    max_left = int(gw * 0.15)
    max_right = int(gw * 0.15)

    # Expand upward
    new_y1 = gc_y1
    for y in range(gc_y1 - 1, max(0, gc_y1 - max_up) - 1, -1):
        if row_sums[y] > up_thresh:
            new_y1 = y
        else:
            break

    # Expand downward
    new_y2 = gc_y2
    for y in range(gc_y2, min(h_img, gc_y2 + max_down)):
        if row_sums[y] > down_thresh:
            new_y2 = y
        else:
            break

    # Expand left
    new_x1 = gc_x1
    for x in range(gc_x1 - 1, max(0, gc_x1 - max_left) - 1, -1):
        if col_sums[x] > left_thresh:
            new_x1 = x
        else:
            break

    # Expand right
    new_x2 = gc_x2
    for x in range(gc_x2, min(w_img, gc_x2 + max_right)):
        if col_sums[x] > right_thresh:
            new_x2 = x
        else:
            break

    # Reject if expansion covers the entire image
    if (new_x2 - new_x1) > 0.95 * w_img and (new_y2 - new_y1) > 0.95 * h_img:
        return (gc_x1, gc_y1, gc_x2, gc_y2)

    return (new_x1, new_y1, new_x2, new_y2)


# ---------------------------------------------------------------------------
# Crop validation and helper logic
# ---------------------------------------------------------------------------
def _validate_crop_box(img, box, w_img, h_img):
    """
    Validates if a crop box represents a valid card sub-region.
    Prevents cropping already-cropped/full-image cards or matching
    small features (like faces, signatures, text blocks).
    """
    if box is None:
        return False
    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1
    area = w * h
    img_area = w_img * h_img

    # 1. Input image is already card-shaped and small-res
    # (very common for scanned cards or pre-cropped images)
    input_aspect = max(w_img, h_img) / max(min(w_img, h_img), 1)
    if 1.35 <= input_aspect <= 1.65 and img_area < 780000:
        return False

    # 2. Area must be substantial (at least 20% of image area)
    # This prevents cropping to small sub-regions like faces/signatures.
    if area < 0.20 * img_area:
        return False

    # 3. Aspect ratio must look like a card (1.25 to 2.2)
    aspect = max(w, h) / max(min(w, h), 1)
    if aspect < 1.25 or aspect > 2.2:
        return False

    # 4. Discarded edge density check:
    # If the outer region contains text/details (high edge density), we are cutting into the card.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    v_median = np.median(blurred)
    edges = cv2.Canny(blurred, int(max(0, 0.5 * v_median)), int(min(255, 1.5 * v_median)))

    box_mask = np.zeros_like(edges)
    box_mask[y1:y2, x1:x2] = 255
    inner_edges = np.sum((edges > 0) & (box_mask == 255))
    outer_edges = np.sum(edges > 0) - inner_edges
    outer_area = img_area - area
    outer_density = outer_edges / outer_area if outer_area > 0 else 0

    if outer_density > 0.012:
        return False

    # 5. Already cropped checks: if the box occupies almost the full image
    w_ratio = w / w_img
    h_ratio = h / h_img
    if w_ratio > 0.92 and h_ratio > 0.88:
        return False

    return True


# ---------------------------------------------------------------------------
# Public API  —  unified card detection pipeline
# ---------------------------------------------------------------------------
def crop_via_opencv(img_path, padding_ratio=0.02):
    """
    Detects document boundary using a two-stage pipeline:
      1. Strict contour detection (fast, works on clear backgrounds)
      2. GrabCut + asymmetric edge-density expansion (for cards on
         similar-colour surfaces like white tablecloths)

    Returns (xmin, ymin, xmax, ymax) if a sub-region card is detected,
    else None (caller should fall back to VLM).
    """
    img = cv2.imread(img_path)
    if img is None:
        return None

    h_img, w_img = img.shape[:2]

    # Stage 1: Fast contour approach
    box = _find_card_via_contour(img)
    if box is not None and _validate_crop_box(img, box, w_img, h_img):
        logger.debug("Card detected via contour method")
    else:
        # Stage 2: GrabCut + expansion
        box = _grabcut_with_expansion(img)
        if box is not None and _validate_crop_box(img, box, w_img, h_img):
            logger.debug("Card detected via GrabCut + expansion")
        else:
            box = None

    if box is None:
        return None

    x1, y1, x2, y2 = box

    # Apply small padding
    bw = x2 - x1
    bh = y2 - y1
    pw = int(padding_ratio * bw)
    ph = int(padding_ratio * bh)
    x1 = max(0, x1 - pw)
    y1 = max(0, y1 - ph)
    x2 = min(w_img, x2 + pw)
    y2 = min(h_img, y2 + ph)

    return (x1, y1, x2, y2)




# ---------------------------------------------------------------------------
# Main entry point called from the ingestion pipeline
# ---------------------------------------------------------------------------
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
        crop_box = crop_via_opencv(filepath, padding_ratio=0.02)
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
