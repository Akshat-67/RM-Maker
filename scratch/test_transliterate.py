import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import urllib.request
import urllib.parse
import json

def google_input_tools_transliterate(text):
    words = text.strip().split()
    hindi_words = []
    for word in words:
        encoded = urllib.parse.quote(word)
        url = (
            f"https://inputtools.google.com/request"
            f"?text={encoded}&itc=hi-t-i0-und&num=1&cp=0&cs=1&ie=utf-8&oe=utf-8"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data and data[0] == "SUCCESS" and len(data) > 1:
            suggestions = data[1]
            if suggestions and len(suggestions[0]) > 1 and suggestions[0][1]:
                hindi_words.append(suggestions[0][1][0])
            else:
                hindi_words.append(word)
        else:
            hindi_words.append(word)
    return " ".join(hindi_words)

tests = ["Vivek Saxena", "Rajesh Kumar", "New Delhi", "Plot No 15 Sector 7"]
for t in tests:
    result = google_input_tools_transliterate(t)
    print(f"OK: '{t}' => '{result}'")
