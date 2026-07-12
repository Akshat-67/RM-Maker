from flask import Blueprint, request, jsonify
import os
import time
import re
import datetime
from services.session_manager import load_case_session, save_case_session
from services.epanjiyan_service import generate_epanjiyan_payload

epanjiyan_bp = Blueprint('epanjiyan', __name__)

LATEST_OTP = {"otp": None, "timestamp": 0}

@epanjiyan_bp.route("/api/case/otp", methods=["GET", "POST"])
def receive_otp():
    global LATEST_OTP
    msg = request.args.get("message") or ""
    if not msg and request.json:
        msg = request.json.get("message") or ""
        
    otp_match = re.search(r'\b\d{6}\b', msg)
    if otp_match:
        otp_code = otp_match.group(0)
        LATEST_OTP = {"otp": otp_code, "timestamp": time.time()}
        print(f"[Backend] OTP received and saved: {otp_code}")
        return jsonify({"success": True, "otp": otp_code})
    return jsonify({"success": False, "error": "No 6-digit OTP found in message"}), 400

@epanjiyan_bp.route("/api/case/otp/recent", methods=["GET"])
def get_recent_otp():
    global LATEST_OTP
    if LATEST_OTP["otp"] and (time.time() - LATEST_OTP["timestamp"]) < 90:
        otp = LATEST_OTP["otp"]
        LATEST_OTP = {"otp": None, "timestamp": 0} # Consume
        return jsonify({"otp": otp})
    return jsonify({"otp": None})

@epanjiyan_bp.route("/api/case/<case_id>/public_dlc", methods=["POST"])
def save_public_dlc(case_id):
    try:
        session = load_case_session(case_id)
        if not session:
            return jsonify({"success": False, "error": "Case not found"}), 404
            
        req_data = request.json or {}
        dlc_profile = req_data.get("public_dlc_profile", {})
        
        if "data" not in session:
            session["data"] = {}
        session["data"]["public_dlc_profile"] = dlc_profile
        
        save_case_session(
            case_id=case_id,
            data=session["data"],
            files=session.get("files", []),
            verified_fields=set(session.get("verified_fields", [])),
            bank=session.get("bank", ""),
            borrower_count=session.get("borrower_count", "1"),
            loan_count=session.get("loan_count", "1"),
            properties_count=session.get("properties_count", "1"),
            doc_type=session.get("doc_type", "SD"),
            sellers_count=session.get("sellers_count", "1"),
            buyers_count=session.get("buyers_count", "1")
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@epanjiyan_bp.route("/api/case/<case_id>/epanjiyan_data")
def get_epanjiyan_data(case_id):
    try:
        session = load_case_session(case_id)
        if not session:
            return jsonify({"error": "Case not found"}), 404
            
        payload = generate_epanjiyan_payload(session)
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@epanjiyan_bp.route("/api/case/<case_id>/save_valuation_quote", methods=["POST"])
def save_case_valuation_quote(case_id):
    try:
        req_data = request.json or {}
        session = load_case_session(case_id)
        if not session:
            return jsonify({"error": "Case not found"}), 404
            
        session["valuation_quote"] = {
            "stamp_duty": req_data.get("stamp_duty", ""),
            "registration_fee": req_data.get("registration_fee", ""),
            "cess_surcharge": req_data.get("cess_surcharge", ""),
            "total_fee": req_data.get("total_fee", ""),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        save_case_session(
            case_id=case_id,
            data=session.get("data", {}),
            files=session.get("files", []),
            verified_fields=set(session.get("verified_fields", [])),
            bank=session.get("bank", ""),
            borrower_count=session.get("borrower_count", "1"),
            loan_count=session.get("loan_count", "1"),
            properties_count=session.get("properties_count", "1"),
            doc_type=session.get("doc_type", "SD"),
            sellers_count=session.get("sellers_count", "1"),
            buyers_count=session.get("buyers_count", "1"),
            valuation_quote=session["valuation_quote"]
        )
        return jsonify({"success": True, "message": "Valuation quote saved successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
