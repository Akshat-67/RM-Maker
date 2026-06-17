from utils.helpers import Unicode_to_KrutiDev

tests = [
    "25-05-2026",
    "20,00,000/-",
    "अक्षरे बीस लाख रुपये"
]

for t in tests:
    print(f"INPUT:  {t}")
    print(f"OUTPUT: {Unicode_to_KrutiDev(t)}")
    print("-" * 20)
