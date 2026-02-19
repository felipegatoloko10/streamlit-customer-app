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
    
    response_data = response.json()
    print("Response:")
    print(json.dumps(response_data, indent=2))

    if "qrcode" in response_data and response_data["qrcode"]:
        # Evolution API v2 usually returns base64 in "qrcode" field or inside "instance" object
        base64_img = response_data.get("qrcode") or response_data.get("base64")
        
        # Sometimes it's inside an object
        if not base64_img and "instance" in response_data:
             base64_img = response_data["instance"].get("qrcode")
        
        if base64_img:
            if "base64," in base64_img:
                base64_img = base64_img.split("base64,")[1]
            
            import base64
            with open("qrcode.png", "wb") as f:
                f.write(base64.b64decode(base64_img))
            print("\nQR Code salvo em qrcode.png")
        else:
            print("\nQR Code não encontrado na resposta.")

except Exception as e:
    print(f"Error: {e}")
