import requests

NVIDIA_API_KEY = "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"
url = "https://integrate.api.nvidia.com/v1/models"

headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}"
}

print("Fetching NVIDIA models...")
try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json().get('data', [])
        print("Available models containing 'nemotron':")
        for m in sorted([x['id'] for x in models]):
            if 'nemotron' in m.lower():
                print(f"  {m}")
            elif 'ultra' in m.lower():
                 print(f"  [ULTRA] {m}")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Error: {e}")
