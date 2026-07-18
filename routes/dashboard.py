from flask import Blueprint, render_template, request, jsonify, send_file
import os
import time
import re
from services.session_manager import list_cases
from services.epanjiyan_service import format_recent_cases
from modules.rm.extractor import RMDataExtractor
from utils.config import DEFAULT_GEMINI_API_KEYS

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/")
def dashboard():
    cases_data = []
    for case in list_cases():
        case["updated"] = time.strftime("%d %b, %H:%M", time.localtime(case.get("last_updated", 0)))
        
        status = case.get("status")
        if status == "processing":
            case["status_text"] = "Processing..."
            case["status_color"] = "warning"
        elif status == "extracting":
            case["status_text"] = "Extracting..."
            case["status_color"] = "warning"
        elif status == "failed":
            case["status_text"] = "Failed"
            case["status_color"] = "danger"
        elif status == "ready":
            case["status_text"] = "Ready"
            case["status_color"] = "success"
        else:
            case["status_text"] = "New"
            case["status_color"] = "secondary"
            
        cases_data.append(case)
    return render_template("dashboard.html", cases=cases_data)


@dashboard_bp.route("/devlys-to-unicode")
def devlys_to_unicode_route():
    return render_template("devlys_to_unicode.html")

@dashboard_bp.route("/api/devlys-to-unicode/convert", methods=["POST"])
def devlys_to_unicode_convert():
    try:
        from utils.devlys_to_unicode import DevLysToUnicodeConverter
        from utils.devlys_converter import UnicodeToDevLysConverter
        
        file = request.files.get("file")
        if not file or not file.filename.endswith(".docx"):
            return jsonify({"success": False, "error": "Invalid file format. Please upload a .docx file."}), 400
            
        font_name = request.form.get("font_name", "Mangal")
        direction = request.form.get("direction", "dev_to_uni")
        
        temp_dir = os.path.join(os.getcwd(), "temp_builder")
        os.makedirs(temp_dir, exist_ok=True)
        
        input_filename = f"conv_in_{int(time.time())}.docx"
        output_filename = f"conv_out_{int(time.time())}.docx"
        input_path = os.path.join(temp_dir, input_filename)
        output_path = os.path.join(temp_dir, output_filename)
        
        file.save(input_path)
        
        if direction == "dev_to_uni":
            DevLysToUnicodeConverter.convert_docx(input_path, output_path, font_name)
        else:
            UnicodeToDevLysConverter.convert_docx(input_path, output_path, font_name)
            
        return send_file(output_path, as_attachment=True, download_name=file.filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@dashboard_bp.route("/devlys_keymap")
def devlys_keymap():
    # Use the definitive DevLys 040 to Unicode mapping
    from utils.devlys_to_unicode import MAPPING_PAIRS
    array_one = [pair[0] for pair in MAPPING_PAIRS]
    array_two = [pair[1] for pair in MAPPING_PAIRS]
    return jsonify({"success": True, "map_from": array_one, "map_to": array_two})

@dashboard_bp.route("/transliterate", methods=["POST"])
def transliterate_text():
    try:
        req_data = request.json or {}
        text = req_data.get("text", "").strip()
        if not text:
            return jsonify({"success": True, "result": ""})

        hindi_result = _google_input_tools_transliterate(text)
        if hindi_result:
            return jsonify({"success": True, "result": hindi_result})

        # Fallback: Gemini API (if quota available)
        try:
            extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
            prompt = f"Transliterate the following English legal name or address into standard, clean Devanagari Hindi script. Return ONLY the transliterated Hindi text, absolutely no surrounding text or formatting: '{text}'"
            gemini_result = extractor.raw_generate(prompt, "gemini-2.0-flash-lite")
            if gemini_result:
                return jsonify({"success": True, "result": gemini_result.strip()})
        except Exception:
            pass

        return jsonify({"success": False, "error": "Transliteration failed — all methods exhausted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@dashboard_bp.route("/api/cases/recent")
def get_recent_cases():
    try:
        cases = list_cases()
        recent = format_recent_cases(cases)
        return jsonify(recent)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _google_input_tools_transliterate(text):
    """
    Uses Google Input Tools API (free, no key) to phonetically transliterate
    English → Devanagari Hindi, word by word.
    Same engine as Google's Hindi keyboard / Input Tools Chrome extension.
    """
    import urllib.request
    import urllib.parse
    import json as _json
    import re

    original_text = text.strip()

    # Smart pre-transliteration replacements (case-insensitive)
    smart_replacements = [
        (r'\bs/o\b\.?', 'पुत्र श्री'),
        (r'\bd/o\b\.?', 'पुत्री श्री'),
        (r'\bw/o\b\.?', 'पत्नी श्री'),
        (r'\bc/o\b\.?', 'मार्फत'),
        (r'\bno\.', 'नं.'),
        (r'\bno\b(?=\s*\d+)', 'नं.'),
        (r'\bmr\.', 'श्री'),
        (r'\bmr\b(?=\s)', 'श्री'),
        (r'\bmrs\.', 'श्रीमती'),
        (r'\bmrs\b(?=\s)', 'श्रीमती'),
        (r'\bms\.', 'सुश्री'),
        (r'\bms\b(?=\s)', 'सुश्री'),
        (r'\bsh\.', 'श्री'),
        (r'\bsh\b(?=\s)', 'श्री'),
        (r'\bsmt\.', 'श्रीमती'),
        (r'\bsmt\b(?=\s)', 'श्रीमती'),
        (r'\bdr\.', 'डॉ.'),
        (r'\blate\b', 'स्वर्गीय'),
        (r'\bflat\b', 'फ्लैट'),
        (r'\bplot\b', 'प्लॉट'),
        (r'\bshop\b', 'दुकान'),
        (r'\bh\.\s*no\.?', 'मकान नं.'),
        (r'\bhouse\s+no\.?', 'मकान नं.'),
        (r'\bward\s+no\.?', 'वार्ड नं.'),
        (r'\bsector\b', 'सेक्टर'),
        (r'\bphase\b', 'फेज'),
        (r'\bblock\b', 'ब्लॉक'),
        (r'\bpocket\b', 'पॉकेट')
    ]
    
    for pat, repl in smart_replacements:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    words = text.strip().split()
    hindi_words = []
    for word in words:
        # Skip if the word contains no English alphabet characters (e.g. it's just numbers/punctuation)
        if not re.search(r'[a-zA-Z]', word):
            hindi_words.append(word)
            continue

        encoded = urllib.parse.quote(word)
        url = (
            f"https://inputtools.google.com/request"
            f"?text={encoded}&itc=hi-t-i0-und&num=1&cp=0&cs=1&ie=utf-8&oe=utf-8"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            # Response: ["SUCCESS", [["word", ["suggestion1", ...], ...]]]
            if data and data[0] == "SUCCESS" and len(data) > 1:
                suggestions = data[1]
                if suggestions and len(suggestions[0]) > 1 and suggestions[0][1]:
                    hindi_words.append(suggestions[0][1][0])
                else:
                    hindi_words.append(word)  # keep original if no suggestion
            else:
                hindi_words.append(word)
        except Exception as e:
            print(f"[InputTools] Failed for word '{word}': {e}")
            hindi_words.append(word)

    result = " ".join(hindi_words)
    # Return None if nothing actually got transliterated
    if result == original_text:
        return None
    return result
