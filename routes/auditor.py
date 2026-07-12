from flask import Blueprint, jsonify, request
from services.session_manager import load_case_session, save_case_session
from services.audit_service import run_case_audit

auditor_bp = Blueprint("auditor", __name__)

@auditor_bp.route("/api/case/<case_id>/run_audit", methods=["POST"])
def run_audit(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case session not found"}), 404
        
    # Recompile the draft document on disk using the latest session data
    from services.generation_service import compile_and_render_document
    try:
        compile_and_render_document(
            case_id=case_id,
            session=session,
            doc_type=session.get("doc_type", "RM"),
            bank=session.get("bank", ""),
            borrowers=session.get("borrower_count", "1"),
            loans=session.get("loan_count", "1"),
            properties=session.get("properties_count", "1"),
            sellers_count=session.get("sellers_count", "1"),
            buyers_count=session.get("buyers_count", "1"),
            chain_scenario=session.get("chain_scenario", ""),
            selected_template=session.get("selected_template", ""),
            property_type=session.get("property_type", "Plot"),
            verified_fields=set(session.get("verified_fields", []))
        )
    except Exception as e:
        # Non-blocking compile failure, log it and proceed with audit
        print(f"Audit compilation warning: {e}")
        
    res = run_case_audit(case_id, doc_type=session.get("doc_type", "RM"))
    return jsonify({"success": True, "discrepancies": res.get("discrepancies", [])})

@auditor_bp.route("/api/case/<case_id>/autofix", methods=["POST"])
def autofix(case_id):
    session = load_case_session(case_id)
    if not session:
        return jsonify({"success": False, "error": "Case session not found"}), 404
        
    req_data = request.json or {}
    field_path = req_data.get("field_path")
    suggested_fix = req_data.get("suggested_fix")
    
    if not field_path:
        return jsonify({"success": False, "error": "Missing field_path"}), 400
        
    # Update field in session data using path syntax (e.g. bs.0.n)
    data = session.get("data", {})
    parts = field_path.split(".")
    
    # Navigate and set the value
    cur = data
    for p in parts[:-1]:
        if p.isdigit():
            idx = int(p)
            while len(cur) <= idx:
                cur.append({})
            cur = cur[idx]
        else:
            if p not in cur:
                cur[p] = {}
            cur = cur[p]
            
    last = parts[-1]
    if last.isdigit():
        idx = int(last)
        while len(cur) <= idx:
            cur.append("")
        cur[idx] = suggested_fix
    else:
        cur[last] = suggested_fix
        
    save_case_session(
        case_id=case_id,
        data=data,
        files=session.get("files", []),
        verified_fields=session.get("verified_fields", []),
        bank=session.get("bank", ""),
        borrower_count=session.get("borrower_count", "1"),
        loan_count=session.get("loan_count", "1"),
        properties_count=session.get("properties_count", "1"),
        processed_files=session.get("processed_files", []),
        doc_type=session.get("doc_type", "RM")
    )
    
    return jsonify({"success": True})
