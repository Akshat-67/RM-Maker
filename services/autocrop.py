import os
import json
import logging
import shutil
from PIL import Image
from services.ai_client import AIClient
from utils.config import DEFAULT_GEMINI_API_KEYS

logger = logging.getLogger("Autocrop")

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
                logger.info(f"Saved original backup to {os.path.basename(backup_path)}")

            cropped_img = img.crop((xmin, ymin, xmax, ymax))
            cropped_img.save(filepath, "JPEG", quality=95)
            logger.info(f"Successfully auto-cropped Aadhaar card for {os.path.basename(filepath)}")

    except Exception as e:
        logger.error(f"Error during autocropping for {os.path.basename(filepath)}: {e}")

