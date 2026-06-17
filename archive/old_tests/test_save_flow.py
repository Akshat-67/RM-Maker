import json
import sys
import os

try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import load_case_session, save_case_session
from extractor import DataExtractor

def test_save_flow():
    case_id = "case_1781264570"
    session = load_case_session(case_id)
    if not session:
        print("[ERROR]: Case session not found!")
        return

    print("Initial property type:", session.get("property_type"))
    
    # Save original values to restore them later
    orig_data = json.loads(json.dumps(session.get("data", {})))
    orig_property_type = session.get("property_type")
    orig_template = session.get("selected_template")

    try:
        # Simulate saving case data from UI
        # 1. Modify plot_no and scheme
        data = json.loads(json.dumps(orig_data))
        if "ps" not in data or not data["ps"]:
            data["ps"] = [{}]
        data["ps"][0]["plot_no"] = "78"
        data["ps"][0]["scheme"] = "Manglam City"
        
        # 2. Compile address using DataExtractor like app.py save_case does
        ext = DataExtractor()
        data["ps"][0]["full_address"] = ext.generate_full_property_address(data["ps"][0], doc_type="RM", property_type="Flat")
        
        # 3. Save case session with property_type="Flat"
        save_case_session(
            case_id, 
            data, 
            session["files"], 
            set(session.get("verified_fields", [])),
            session.get("bank", ""),
            session.get("borrower_count", "1"),
            session.get("loan_count", "1"),
            properties_count=session.get("properties_count", "1"),
            processed_files=session.get("processed_files", []),
            doc_type=session.get("doc_type", "RM"),
            sellers_count=session.get("sellers_count", "1"),
            buyers_count=session.get("buyers_count", "1"),
            chain_scenario=session.get("chain_scenario", ""),
            selected_template="RM_HFFC_2B_1L.docx",  # Simulate manual template selection
            property_type="Flat"
        )
        
        # Reload and check values
        reloaded = load_case_session(case_id)
        reloaded_data = reloaded.get("data", {})
        reloaded_property_type = reloaded.get("property_type")
        reloaded_template = reloaded.get("selected_template")
        reloaded_address = reloaded_data.get("ps", [{}])[0].get("full_address", "")
        
        print("\n--- Reloaded Settings ---")
        print("Property Type:", reloaded_property_type)
        print("Selected Template:", reloaded_template)
        print("Compiled Address:", reloaded_address)
        
        assert reloaded_property_type == "Flat", "Property type was not saved as Flat!"
        assert reloaded_template == "RM_HFFC_2B_1L.docx", "Selected template was not saved!"
        assert "Flat No. 78" in reloaded_address, f"Address was not compiled with Flat prefix! Address: {reloaded_address}"
        
        # 4. Now simulate save without passing property_type or selected_template (simulate upload or AI run reset check)
        # This will call save_case_session with defaults (None) to test preservation
        save_case_session(
            case_id,
            reloaded_data,
            reloaded["files"],
            set(reloaded.get("verified_fields", [])),
            reloaded.get("bank", ""),
            reloaded.get("borrower_count", "1"),
            reloaded.get("loan_count", "1"),
            properties_count=reloaded.get("properties_count", "1"),
            processed_files=reloaded.get("processed_files", []),
            # Omit parameters to test fallback defaults
            doc_type=None,
            sellers_count=None,
            buyers_count=None,
            chain_scenario=None,
            selected_template=None,
            property_type=None
        )
        
        preserved = load_case_session(case_id)
        print("\n--- Preserved Settings (after upload/AI save check) ---")
        print("Property Type:", preserved.get("property_type"))
        print("Selected Template:", preserved.get("selected_template"))
        print("Doc Type:", preserved.get("doc_type"))
        
        assert preserved.get("property_type") == "Flat", "Property type was reset!"
        assert preserved.get("selected_template") == "RM_HFFC_2B_1L.docx", "Selected template was reset!"
        assert preserved.get("doc_type") == "RM", "Doc type was reset!"
        
        print("\n[UAT SAVING FLOW PASSED CLEANLY!]")
        
    finally:
        # Restore original session data to keep the test sandbox clean
        save_case_session(
            case_id, 
            orig_data, 
            session["files"], 
            set(session.get("verified_fields", [])),
            session.get("bank", ""),
            session.get("borrower_count", "1"),
            session.get("loan_count", "1"),
            properties_count=session.get("properties_count", "1"),
            processed_files=session.get("processed_files", []),
            doc_type=session.get("doc_type", "RM"),
            sellers_count=session.get("sellers_count", "1"),
            buyers_count=session.get("buyers_count", "1"),
            chain_scenario=session.get("chain_scenario", ""),
            selected_template=orig_template,
            property_type=orig_property_type
        )
        print("Original sandbox case restored.")

if __name__ == "__main__":
    test_save_flow()
