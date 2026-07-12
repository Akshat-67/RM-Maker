from utils.helpers import Unicode_to_KrutiDev

test_cases = [
    "20,00,000/-",
    "बीस लाख रुपये",
    "20,00,000/- (बीस लाख रुपये)"
]

for t in test_cases:
    print(f"INPUT: {t}")
    print(f"OUTPUT: {Unicode_to_KrutiDev(t)}")
    print("-" * 20)
