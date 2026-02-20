import requests
import json

BASE = "http://localhost:8080"
TOKEN = "B6D6574D-3932-491A-850E-1649911D0C4F"
INSTANCE = "BotFeh"
HEADERS = {"apikey": TOKEN, "Content-Type": "application/json"}

# findMessages
r2 = requests.post(f"{BASE}/chat/findMessages/{INSTANCE}", json={"count": 5, "page": 1}, headers=HEADERS, timeout=10)
print("Status:", r2.status_code)
try:
    d = r2.json()
    # Show full structure
    print("=== FULL RESPONSE (first 2000 chars) ===")
    print(json.dumps(d, default=str)[:2000])
    
    # Navigate 'messages' key
    msgs_val = d.get("messages")
    print("\n=== messages value type:", type(msgs_val).__name__)
    if isinstance(msgs_val, dict):
        print("messages dict keys:", list(msgs_val.keys()))
        # Try common nested patterns
        for k in msgs_val.keys():
            v = msgs_val[k]
            print(f"  '{k}' -> type={type(v).__name__}, value_preview={str(v)[:200]}")
    elif isinstance(msgs_val, list):
        print("messages is a list of", len(msgs_val), "items")
        if msgs_val:
            print("First item:", json.dumps(msgs_val[0], default=str)[:500])
except Exception as e:
    print("Erro:", e)
    print("Raw:", r2.text[:1000])
