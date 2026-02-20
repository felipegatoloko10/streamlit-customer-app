import json
import base64
import sys
import os

try:
    # Try reading as utf-16 (handles BOM automatically)
    try:
        with open('qr_response_v3.json', 'r', encoding='utf-16') as f:
            data = json.load(f)
    except (UnicodeError, json.JSONDecodeError):
        # Fallback to utf-8 if utf-16 fails
        with open('qr_response_v3.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

    if 'base64' in data and data['base64']:
        # Extract base64 part (remove data:image/png;base64, prefix if present)
        b64_str = data['base64']
        if ',' in b64_str:
            b64_str = b64_str.split(',')[1]
        
        img_data = base64.b64decode(b64_str)
        
        with open('qr_code.png', 'wb') as f:
            f.write(img_data)
            
        print("QR Code saved to qr_code.png")
    else:
        print("No base64 field found in response:")
        print(json.dumps(data, indent=2))
        sys.exit(1)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
