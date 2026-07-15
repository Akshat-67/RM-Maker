from flask import Blueprint, request, jsonify, send_file
from services.session_manager import load_case_session, save_case_session
from services.generation_service import compile_and_render_document, generate_draft_preview
from services.compile_gate import check_compile_prerequisites
from utils.helpers import validate_case_id

generation_bp = Blueprint('generation', __name__)

@generation_bp.before_request
def check_case_id():
    case_id = None
    if request.view_args and 'case_id' in request.view_args:
        case_id = request.view_args['case_id']
    elif request.args and 'case_id' in request.args:
        case_id = request.args['case_id']
    if case_id:
        if not validate_case_id(case_id):
            return jsonify({"success": False, "error": "Invalid case_id format"}), 400

@generation_bp.route("/case/<case_id>/generate", methods=["POST"])
def generate_rm(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json
    doc_type = req_data.get("doc_type", "RM")
    
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    properties = req_data.get("properties", "1")
    
    sellers_count = req_data.get("sellers_count", "1")
    buyers_count = req_data.get("buyers_count", "1")
    chain_scenario = req_data.get("chain_scenario", "")
    
    selected_template = req_data.get("selected_template", "")
    property_type = req_data.get("property_type", "Plot")
    
    data = req_data.get("data", {})
    verified_fields = set(req_data.get("verified_fields", session.get("verified_fields", [])))

    # Ensure the latest UI data is saved before generating
    save_case_session(case_id, 
                      data, 
                      session["files"],
                      verified_fields,
                      bank,
                      borrowers,
                      loans,
                      properties,
                      session.get("processed_files", []),
                      doc_type=doc_type,
                      sellers_count=sellers_count,
                      buyers_count=buyers_count,
                      chain_scenario=chain_scenario,
                      selected_template=selected_template,
                      property_type=property_type)

    # Reload from session to get the fully merged data
    session = load_case_session(case_id)

    # --- Server-side compile safety gate (Bug 4 fix) ---
    # Relaxed by user request: do not return 422/block compilation. Let it generate with warnings.
    missing = check_compile_prerequisites(session, doc_type)

    try:
        output_filepath, output_filename = compile_and_render_document(
            case_id=case_id,
            session=session,
            doc_type=doc_type,
            bank=bank,
            borrowers=borrowers,
            loans=loans,
            properties=properties,
            sellers_count=sellers_count,
            buyers_count=buyers_count,
            chain_scenario=chain_scenario,
            selected_template=selected_template,
            property_type=property_type,
            verified_fields=verified_fields
        )
        return send_file(output_filepath, as_attachment=True, download_name=output_filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@generation_bp.route("/case/<case_id>/preview_draft", methods=["POST"])
def preview_draft(case_id):
    session = load_case_session(case_id)
    if not session: return jsonify({"success": False, "error": "Case not found"}), 404

    req_data = request.json or {}
    doc_type = req_data.get("doc_type", "RM")
    
    bank = req_data.get("bank")
    borrowers = req_data.get("borrowers")
    loans = req_data.get("loans")
    properties = req_data.get("properties", "1")
    
    sellers_count = req_data.get("sellers_count", "1")
    buyers_count = req_data.get("buyers_count", "1")
    chain_scenario = req_data.get("chain_scenario", "")
    
    selected_template = req_data.get("selected_template", "")
    property_type = req_data.get("property_type", "Plot")
    
    data = req_data.get("data", {})
    verified_fields = set(req_data.get("verified_fields", session.get("verified_fields", [])))

    try:
        preview_html = generate_draft_preview(
            case_id=case_id,
            session=session,
            doc_type=doc_type,
            bank=bank,
            borrowers=borrowers,
            loans=loans,
            properties=properties,
            sellers_count=sellers_count,
            buyers_count=buyers_count,
            chain_scenario=chain_scenario,
            selected_template=selected_template,
            property_type=property_type,
            verified_fields=verified_fields
        )
        return jsonify({"success": True, "preview_html": preview_html})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
