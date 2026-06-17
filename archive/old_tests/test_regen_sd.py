
import requests
import time

url = 'http://127.0.0.1:5000/api/sd/generate/case_1781374115'
print(f'Calling {url}')
response = requests.post(url)
print(response.status_code)

if response.status_code == 200:
    with open(r'Test\AI_Regen.docx', 'wb') as f:
        f.write(response.content)
    print('Generated AI_Regen.docx successfully')
else:
    print(response.text)
