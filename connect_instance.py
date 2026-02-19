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
    
    response_data = response.json()
    print("Response:")
    print(json.dumps(response_data, indent=2))

    base64_img = None
    if "base64" in response_data:
        base64_img = response_data["base64"]
    elif "qrcode" in response_data and isinstance(response_data["qrcode"], str):
        base64_img = response_data["qrcode"]
    elif "instance" in response_data and isinstance(response_data["instance"], dict):
         base64_img = response_data["instance"].get("qrcode")

    if base64_img:
        if "base64," in base64_img:
            base64_img = base64_img.split("base64,")[1]
        
        import base64
        with open("qrcode.png", "wb") as f:
            f.write(base64.b64decode(base64_img))
        print("\nQR Code salvo em qrcode.png")
    else:
        print("\nQR Code não encontrado (pode já estar conectado).")
        
except Exception as e:
    print(f"Error: {e}")
