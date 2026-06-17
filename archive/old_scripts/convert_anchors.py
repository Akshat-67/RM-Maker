import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.devlys_converter import unicode_to_devlys

def main():
    boundary_anchors = ["Boundaries as under", "जिसकी चारों सीमाएं", "सीमाऐं निम्न प्रकार", "Bounded as follows"]
    dim_anchors = ["East to West", "North to South", "Measuring", "जिसकी नाप", "पूर्व से पश्चिम", "उत्तर से दक्षिण"]
    addr_anchors = ["All that part and parcel", "Situated at", "Municipal No", "Ward No", "स्थित", "प्लॉट नं.", "फ्लैट नं."]
    chain_anchors = ["History of Title", "Chain of Ownership", "यह कि उक्त वर्णित संपत्ति का मूल", "History of the property", "Follow of title"]

    with open("scratch/converted_anchors.txt", "w", encoding="utf-8") as f:
        f.write("=== BOUNDARY ANCHORS ===\n")
        for a in boundary_anchors:
            f.write(f"'{a}' -> '{unicode_to_devlys(a)}'\n")

        f.write("\n=== DIMENSION ANCHORS ===\n")
        for a in dim_anchors:
            f.write(f"'{a}' -> '{unicode_to_devlys(a)}'\n")

        f.write("\n=== ADDRESS ANCHORS ===\n")
        for a in addr_anchors:
            f.write(f"'{a}' -> '{unicode_to_devlys(a)}'\n")

        f.write("\n=== CHAIN ANCHORS ===\n")
        for a in chain_anchors:
            f.write(f"'{a}' -> '{unicode_to_devlys(a)}'\n")

    print("Successfully wrote converted anchors to scratch/converted_anchors.txt")

if __name__ == "__main__":
    main()
