import requests
import json

url = "http://localhost:8080/instance/create"
apikey = "B6D6574D-3932-491A-850E-1649911D0C4F"

headers = {
    "apikey": apikey,
    "Content-Type": "application/json"
}

data = {
    "instanceName": "cactvs",
    "token": apikey,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

try:
    print(f"Connecting to {url}...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
