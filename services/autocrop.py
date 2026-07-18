import os
import json
import base64
import logging
import shutil
from PIL import Image
from openai import OpenAI
from utils.config import NVIDIA_NIM_API_KEY

logger = logging.getLogger("Autocrop")

def autocrop_image_if_aadhar(filepath: str) -> None:
    if not NVIDIA_NIM_API_KEY:
        logger.warning("NVIDIA NIM API key missing, skipping autocropping.")
        return
        
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

        with open(filepath, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=NVIDIA_NIM_API_KEY
        )

        system_prompt = (
            "You are an expert document detection VLM. Your job is to locate the Aadhaar card in the image. "
            "Return the bounding box coordinates on a 0 to 1000 scale, where: "
            "ymin is the top edge (0-1000), xmin is the left edge (0-1000), "
            "ymax is the bottom edge (0-1000), xmax is the right edge (0-1000). "
            "Return the output ONLY as a valid JSON object with these exact keys: "
            "{\"has_aadhar\": true/false, \"ymin\": int, \"xmin\": int, \"ymax\": int, \"xmax\": int}"
        )

        response = client.chat.completions.create(
            model="meta/llama-3.2-90b-vision-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Locate the Aadhaar card in this image and return its bounding box coordinates in JSON format."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=150,
            temperature=0.1
        )

        raw_content = response.choices[0].message.content.strip()
        result = json.loads(raw_content)

        if result.get("has_aadhar") and all(k in result for k in ["ymin", "xmin", "ymax", "xmax"]):
            ymin = max(0, int(result["ymin"] * img_height / 1000))
            xmin = max(0, int(result["xmin"] * img_width / 1000))
            ymax = min(img_height, int(result["ymax"] * img_height / 1000))
            xmax = min(img_width, int(result["xmax"] * img_width / 1000))

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
