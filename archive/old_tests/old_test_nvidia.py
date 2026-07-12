import os
import requests

NVIDIA_API_KEY = "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"
url = "https://integrate.api.nvidia.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

# Let's try meta/llama-3.1-8b-instruct or meta/llama3-8b-instruct
payload = {
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "Hello! Reply with 'Hello from Llama 3.1!'"}],
    "temperature": 0.2,
    "top_p": 0.7,
    "max_tokens": 1024
}

print("Testing NVIDIA key with meta/llama-3.1-8b-instruct...")
try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Response:")
        print(data['choices'][0]['message']['content'])
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Failed to request: {e}")
