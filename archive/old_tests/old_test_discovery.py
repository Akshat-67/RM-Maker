"""Print discovered templates to see how the mapping is constructed."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

from app import discover_templates

def main():
    template_map, sd_template_map, bank_folders = discover_templates()
    print("=== RM TEMPLATES ===")
    for bank, data in template_map.items():
        print(f"Bank: {bank}")
        print(data)
    print("\n=== SD TEMPLATES ===")
    for s_count, b_data in sd_template_map.items():
        print(f"Sellers: {s_count}")
        for b_count, path in b_data.items():
            print(f"  Buyers: {b_count} -> {path}")
    print("\n=== BANK FOLDERS ===")
    print(bank_folders)

if __name__ == "__main__":
    main()
