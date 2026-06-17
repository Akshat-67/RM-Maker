from utils.helpers import Unicode_to_KrutiDev
res = Unicode_to_KrutiDev('25-05-2026')
print(f"RESULT: '{res}'")
print(f"HEX: {' '.join(hex(ord(c)) for c in res)}")
