from flask import Blueprint, render_template, request, jsonify, send_file
import os
import time
import json
import re
from modules.rm.extractor import RMDataExtractor
from modules.sd.extractor import SDDataExtractor
from utils.config import DEFAULT_GEMINI_API_KEYS

template_builder_bp = Blueprint('template_builder', __name__)

@template_builder_bp.route("/template-builder")
def template_builder():
    try:
        extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        models = extractor.get_available_models()
    except Exception:
        models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"]
    
    from template_tools.builder_core import RM_FIELDS, SD_FIELDS
    rm_fields = [(f[0], f[1]) for f in RM_FIELDS]
    sd_fields = [(f[0], f[1]) for f in SD_FIELDS]
    sd_generated_fields = []
    
    return render_template("template_builder.html", models=models, rm_fields=rm_fields, sd_fields=sd_fields, sd_generated_fields=sd_generated_fields)

@template_builder_bp.route("/api/builder/upload", methods=["POST"])
def builder_upload():
    try:
        file = request.files.get("file")
        if not file or not file.filename.endswith(".docx"):
            return jsonify({"success": False, "error": "Invalid file format. Please upload a .docx file."}), 400
            
        temp_dir = os.path.join(os.getcwd(), "temp_builder")
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f"uploaded_{int(time.time())}.docx"
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        return jsonify({"success": True, "filepath": filepath, "filename": file.filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@template_builder_bp.route("/api/builder/discover", methods=["POST"])
def builder_discover():
    try:
        from template_tools.builder_core import DocManipulator, get_discovery_prompt, clean_mapping
        req_data = request.json
        filepath = req_data.get("filepath")
        mode = req_data.get("mode", "RM")
        model = req_data.get("model", "gemini-2.0-flash-lite")
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Invalid or missing file path."}), 400
            
        from docx import Document
        doc = Document(filepath)
        content = DocManipulator.get_doc_content(doc)
        
        prompt = get_discovery_prompt(content, mode)
        
        if mode == "SD":
            extractor = SDDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        else:
            extractor = RMDataExtractor(api_keys=DEFAULT_GEMINI_API_KEYS, provider="gemini")
        raw = extractor.raw_generate(prompt, model)
        
        match = re.search(r'\{.*\}', raw or "", re.DOTALL)
        mapping = {}
        if match:
            mapping_str = match.group(0)
            cleaned_lines = []
            for line in mapping_str.splitlines():
                line_stripped = line.strip()
                if line_stripped in ('{', '}', '[', ']', '') or not line_stripped.startswith('"'):
                    cleaned_lines.append(line)
                    continue
                match_val = re.search(r':\s*(("(.*)"|null|true|false|\d+)\s*(,?)\s*)$', line_stripped)
                if not match_val:
                    cleaned_lines.append(line)
                    continue
                key_part = line_stripped[:match_val.start()].strip()
                val_part = match_val.group(1).strip()
                if key_part.startswith('"') and key_part.endswith('"'):
                    raw_key = key_part[1:-1]
                    escaped_key = raw_key.replace('\\"', '"').replace('"', '\\"')
                    key_part = f'"{escaped_key}"'
                raw_val_match = re.match(r'^"(.*)"(,?)$', val_part)
                if raw_val_match:
                    raw_val = raw_val_match.group(1)
                    comma = raw_val_match.group(2)
                    escaped_val = raw_val.replace('\\"', '"').replace('"', '\\"')
                    val_part = f'"{escaped_val}"{comma}'
                indent = line[:len(line) - len(line.lstrip())]
                cleaned_lines.append(f'{indent}{key_part}: {val_part}')
            cleaned_mapping_str = "\n".join(cleaned_lines)
            
            try:
                mapping = json.loads(cleaned_mapping_str)
            except Exception:
                mapping = json.loads(mapping_str)
                
        cleaned = clean_mapping(mapping)
        return jsonify({"success": True, "mapping": cleaned, "doc_text": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@template_builder_bp.route("/api/builder/generate", methods=["POST"])
def builder_generate():
    try:
        from template_tools.builder_core import generate_master_template
        req_data = request.json
        filepath = req_data.get("filepath")
        mapping = req_data.get("mapping", {})
        mode = req_data.get("mode", "RM")
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Invalid or missing file path."}), 400
            
        temp_dir = os.path.dirname(filepath)
        output_filename = f"generated_master_{int(time.time())}.docx"
        output_path = os.path.join(temp_dir, output_filename)
        
        generate_master_template(filepath, mapping, output_path)
        
        return send_file(output_path, as_attachment=True, download_name="MASTER_TEMPLATE_READY.docx")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
