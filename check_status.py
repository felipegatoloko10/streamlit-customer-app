import requests
import json

base_url = "http://localhost:8080"
instance = "cactvs"
apikey = "B6D6574D-3932-491A-850E-1649911D0C4F"

headers = {
    "apikey": apikey
}

def check_status():
    url = f"{base_url}/instance/connectionState/{instance}"
    try:
        print(f"Checking status at {url}...")
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

check_status()
