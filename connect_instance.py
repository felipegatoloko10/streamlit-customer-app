import requests
import json
import base64

url = "http://localhost:8080/instance/connect/cactvs"
apikey = "B6D6574D-3932-491A-850E-1649911D0C4F"

headers = {
    "apikey": apikey
}

try:
    print(f"Connecting to {url}...")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    data = response.json()
    print("Response:")
    print(json.dumps(data, indent=2))

    if "base64" in data:
        # Save QR code to file for easy viewing if possible, or just notify user
        # We can't easily display image in terminal, but having the base64 confirms it's there.
        print("\nQR Code received (base64).")
        
except Exception as e:
    print(f"Error: {e}")
