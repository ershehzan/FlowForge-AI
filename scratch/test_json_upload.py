import urllib.request
import urllib.error
import json

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open('examples/job_shop_sample.json', 'rb') as f:
    file_bytes = f.read()

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="job_shop_sample.json"\r\n'
    f'Content-Type: application/json\r\n\r\n'
).encode('utf-8') + file_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/factory/upload',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        print('HTTP Status:', response.status)
        print('Success:', res_data.get('success'))
        print('Data Source:', res_data.get('data_source'))
        print('Summary:', res_data.get('summary'))
        print('Schedule items:', len(res_data.get('baseline_schedule', [])))
        print('Resilience:', res_data.get('resilience', {}).get('score'))
        print('First 2 scheduled:', res_data.get('baseline_schedule', [])[:2])
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code, e.read().decode('utf-8'))
