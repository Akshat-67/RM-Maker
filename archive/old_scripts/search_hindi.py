"""Search all Python files for specific ownership or chain-ending keywords in Hindi or DevLys ASCII."""
import sys, os, re

keywords = [
    "मालिक", "स्वामी", "अधिकारी", "हुए", "हुआ",
    "ekfyd", "Lokeh", "vf/kdkjh", "gqvk", "gq,e"
]

def main():
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass
    
    root_dir = "c:/Users/aksha/Documents/RM Generator/RM-Maker"
    for dirpath, _, filenames in os.walk(root_dir):
        if ".git" in dirpath or "__pycache__" in dirpath or "node_modules" in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(".py") or fname.endswith(".html") or fname.endswith(".md"):
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for kw in keywords:
                        if kw in content:
                            print(f"FOUND '{kw}' in {fpath}")
                            # Print matching lines
                            lines = content.splitlines()
                            for i, line in enumerate(lines):
                                if kw in line:
                                    print(f"  Line {i+1}: {line.strip()}")
                except Exception as e:
                    print(f"Error reading {fpath}: {e}")

if __name__ == "__main__":
    main()
